"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import traceback
from typing import Optional
from textual import on
from textual.message import Message
from textual.widget import Widget
from textual.widgets.text_area import Selection
from concurrent.futures import ThreadPoolExecutor
import os
import re
import argparse
from textual.message_pump import events
from textual.widgets import Log, TextArea
from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.dom import DOMNode
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, Static
from textual.widgets import Footer, Label, ListItem, ListView
from baseview import MyListView, uicallback
from callinview import ResultTree, callinopen, callinview
from codesearch import ResultItemRefer, ResultItemSearch, ResultItemString, SearchResults, SourceCode, SourceCodeSearch
from codeview import CodeView, code_message_decl, code_message_impl, code_message_refer
from commandline import convert_command_args, clear_key
from common import Body, from_file, to_file
from codetask import TaskManager
from dircomplete import TaskFindFile, dir_complete_db
from event import callin_message, changelspmessage, log_message, message_open_file, mymessage, refermessage, symbolsmessage
from input_suggestion import input_suggestion
from lspcpp import CallNode, CallerWalker, LspMain, Symbol, OutputFile, config, task_call_in, task_callback
from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.widgets import Footer, Label, TabbedContent, TabPane
from planuml import Failure
from pylspclient.lsp_pydantic_strcuts import Location, SymbolInformation
from history import BackFoward, history
from commandline import input_command_options
from codesearch import generic_search
from event import message_get_symbol_refer, message_line_change, message_get_symbol_callin
from symbolload import _symbol_tree_view, symbol_tree_update, symbolload


class UiOutput(OutputFile):
    ui: Log | None = None
    is_close = False

    def close(self):
        self.is_close = True
        OutputFile.close(self)

    def flush(self):
        if self.is_close:
            return
        return super().flush()

    def write(self, s):
        if self.is_close:
            return
        OutputFile.write(self, s)
        if self.ui != None:
            if len(s) and s[-1] == "\n":
                s = s[:-1]
            self.ui.write_line(s)


class LspQuery:
    data: str
    type: str

    def __init__(self, name: str, type: str) -> None:
        self.data = name
        self.type = type
        pass

    def __eq__(self, value: object) -> bool:
        if isinstance(value, LspQuery):
            s: LspQuery = value
            return self.data == s.data and self.type == s.type
        return False


class CommandInput(Input):
    mainui: uicallback

    def __init__(self, mainui: 'CodeBrowser', root) -> None:
        suggestion = input_suggestion(input_command_options)
        suggestion.dircomplete = dir_complete_db(root)
        super().__init__(suggester=suggestion,
                         placeholder=" ".join(input_command_options),
                         type="text")
        self.history = history("input_history.history")
        self.mainui = mainui
        self.suggestion = suggestion
        suggestion._history = self.history

    @on(Input.Changed)
    def on_input_changed(self, message: Message):
        if self.mainui != None:
            self.mainui.on_vi_command(self.value)
        pass

    def on_input_submitted(self) -> None:
        if self.mainui != None:
            self.history.add_to_history(self.value)
            args = convert_command_args(self.value)
            if len(args) > 1:
                if args[0] in input_command_options:
                    for a in args[1:]:
                        self.history.add_to_history(a)

            self.mainui.on_command_input(self.value)
        pass

    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            event.stop()
            return
        if event.key == "down":
            event.stop()
            return
        pass


def extract_file_paths(text):
    # 正则表达式匹配Linux文件路径
    # 假设路径是从根目录开始，包含一个或多个目录层级
    pattern = r'/(?:[\w-]+/)*[\w-]+\.(?:[\w-]+)'
    matches = re.findall(pattern, text)
    return matches


class MyLogView(Log):
    mainuui: 'CodeBrowser'

    def on_mouse_down(self, event) -> None:
        try:
            s: str = self.lines[int(event.y + self.scroll_y)]
            file_paths = extract_file_paths(s)
            link = None
            for f in file_paths:
                pos = s.find(f)
                if event.x > pos and event.x < pos + len(f):
                    link = f
                    break
            if link != None:
                line = None
                try:
                    end = s[s.index(link) + len(link):]
                    pattern = re.compile(r'^:([0-9]+)')
                    matches = pattern.findall(end)
                    line = int(matches[0])
                except:
                    pass
                self.mainuui.on_click_link(link, line=line)
            pass
        except Exception as e:
            self.log.error(str(e))
            pass


SYMBOL_LISTVIEW_TYPE = 1
HISTORY_LISTVIEW_TYPE = 2


class vimstate:
    escape = False
    find = False
    command = False
    find_enter: Optional[str]

    def __init__(self, escape=False, find=False, command=False, insert=False):
        self.escape = escape
        self.find = find
        self.command = command
        self.insert = insert
        self.find_enter = None


class vim:
    vi: vimstate

    def __init__(self, app: 'CodeBrowser') -> None:
        self.app = app
        self.vi = vimstate()
        pass

    def check_input(self):
        if self.vi.find_enter != None:
            if len(self.vi.find_enter) > len(self.app.cmdline.value):
                self.vi.find_enter = None
            else:
                self.app.cmdline.value = self.vi.find_enter
        return self.app.cmdline.value

    def enter_find(self):
        if self.vi.escape:
            self.app.cmdline.focus()
            self.vi = vimstate(find=True)
            self.app.cmdline.value = "/"

    def enter_insert(self):
        if self.vi.escape:
            self.vi = vimstate(insert=True)
        pass

    def enter_escape(self):
        self.app.cmdline.clear()
        self.vi = vimstate(escape=True)
        pass

    def enter_command(self):
        if self.vi.escape:
            self.vi = vimstate(command=True)
            self.app.cmdline.value = ":"
            self.app.cmdline.focus()
        pass


class CodeBrowser(App, uicallback):
    root: str
    symbol_query = LspQuery("", "")
    codeview_file: str
    search_result: SearchResults
    # symbol_listview: MyListView
    history_view: MyListView
    lsp: LspMain
    callin: callinview
    preview_focused: Optional[Widget]
    generic_search_mgr: generic_search
    _symbolload: symbolload

    def __init__(self, root, file):
        App.__init__(self)
        self.thread = None
        self.lsp = LspMain(root=root, file=file)
        self.root = root
        self.tofile = None
        self.toUml = None
        self.codeview_file = self.sub_title = file
        self.soucecode = SourceCode(self.codeview_file)
        self.history = history()
        self.backforward = BackFoward(self.history)
        self.history.add_to_history(self.codeview_file)
        self.symbol_listview_type = SYMBOL_LISTVIEW_TYPE
        self.CodeView = CodeView()
        self.callin = callinview()
        self.taskmanager = TaskManager()
        self.preview_focused = None
        self.generic_search_mgr = generic_search(None, "")
        self._symbolload = symbolload("", self.lsp)
        self.symbol_tree_view = _symbol_tree_view()
        self.uml = ResultTree()
        self.uml.update()

    def on_callinopen(self, msg: callinopen) -> None:
        try:
            if isinstance(msg.node, CallNode):
                node: CallNode = msg.node
                self.on_choose_file_from_event(
                    from_file(node.sym.uri),
                    Location(uri=node.sym.uri, range=node.sym.selectionRange))
            elif isinstance(msg.node, task_call_in):
                task: task_call_in = msg.node
                self.on_choose_file_from_event(
                    from_file(task.method.location.uri), task.method.location)
                pass
        except Exception as e:
            self.logview.write(str(e))

    def on_callin_message(self, message: callin_message) -> None:
        if message.taskmsg != None:
            self.callin.update_job(message.taskmsg)
            f: Label = self.query_one("#f1", Label)
            self.callin.status = "call in to <%d> " % (len(
                message.taskmsg.task.callin_all
            )) + message.taskmsg.task.displayname()
            f.update(self.callin.status)
            # if len(message.task.callin_all) > 0:
            #     self.callin.tree.focus()

        pass

    def on_message_open_file(self, message: message_open_file):
        self.on_choose_file_from_event(message.file)

    def on_refermessage(self, message: refermessage) -> None:
        self.search_result = SearchResults(
            list(map(lambda x: ResultItemRefer(x), message.s)))
        self.udpate_search_result_view()
        self.searchview.focus()
        f: Label = self.query_one("#f1", Label)
        self.search_result.status = "Refer to <%d> " % (len(
            message.s)) + message.query
        f.update(self.search_result.status)
        pass

    @on(TabbedContent.TabActivated)
    def on_tabpanemessage(self, message: Message):
        if isinstance(message, TabbedContent.TabActivated):
            tab: TabbedContent.TabActivated = message
            id = tab.pane.id
            f: Label = self.query_one("#f1", Label)
            if id == "fzf-tab":
                f.update(self.search_result.status)
            elif id == "callin-tab":
                f.update(self.callin.status)
                pass
        pass

    @on(TextArea.SelectionChanged)
    def message_received(self, message: Message):
        if self.CodeView.is_focused() == False:
            pass
        if self.CodeView.textarea is None:
            return
        try:
            selection = self.CodeView.get_select_range()
            if selection != None:
                self.symbol_tree_view.goto_selection(selection)
        except Exception as e:
            self.logview.write_line(str(e))

    def on_log_message(self, message: log_message):
        self.logview.write_line(message.log)

    def on_mymessage(self, message: mymessage) -> None:
        s = message.s
        self.search_result = SearchResults(
            list(map(lambda x: ResultItemString(x), s)))
        # logui.write_lines(s)
        self.searchview.setlist(s)
        self.searchview.focus()
        pass
        """Textual code browser app."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
        # ("i", "focus_to_code", "Focus to cmdline"),
        ("k", "key_up", "up"),
        ("j", "key_down", "down"),
        ("escape", "vim_escape", "Focus to cmdline"),
        (":", "vim_command_mode", "Focus to cmdline"),
        ("i", "vim_insert_mode", "Focus to cmdline"),
        ("/", "vim_find_mode", "Focus to cmdline"),
        ("ctrl+o", "goback", "Go Back"),
        ("ctrl+b", "goforward", "Go Forward"),
    ]

    show_tree = var(True)

    def action_vim_insert_mode(self) -> None:
        self.vim.enter_insert()

    def action_vim_find_mode(self) -> None:
        self.vim.enter_find()

    def action_vim_escape(self) -> None:
        self.vim.enter_escape()
        if self.screen.focused != self.cmdline:
            self.preview_focused = self.screen.focused
        pass

    def action_vim_command_mode(self) -> None:
        self.vim.enter_command()
        pass

    def action_key_down(self) -> None:
        if self.CodeView.is_focused():
            self.CodeView.key_down()
        pass

    def action_key_up(self) -> None:
        if self.CodeView.is_focused():
            self.CodeView.key_down(False)
        pass

    def action_focus_to_code(self) -> None:
        if self.CodeView.textarea is None:
            return
        self.CodeView.textarea.focus()
        pass

    def on_select_list(self, list: ListView):
        if self.searchview == list:
            if list.index == None:
                return
            result = self.search_result.on_select(list.index)
            if isinstance(result, ResultItemString):
                self.on_choose_file_from_event(str(result))
            elif isinstance(result, ResultItemRefer):
                self.code_to_refer(result)
                pass
            elif isinstance(result, ResultItemSearch):
                search: ResultItemSearch = result
                self.code_to_search_position(search)
        if self.history_view == list:
            if list.index != None:
                self.on_choose_file_from_event(
                    self.history.datalist[list.index])
        pass

    def code_to_refer(self, refer: ResultItemRefer):
        self.on_choose_file_from_event(refer.item.file, loc=refer.loc())
        # y = refer.item.range.start.line
        # b = refer.item.range.start.character
        # e = refer.item.range.end.character
        # self.code_editor_scroll_view().scroll_to(y=y - 10, animate=False)
        # self.hightlight_code_line(y, colbegin=b, colend=e)
        pass

    def code_to_search_position(self, search):
        y = search.item.line
        self.soucecode.search.index = y
        self.code_editor_scroll_view().scroll_to(y=y - 10, animate=False)
        self.hightlight_code_line(y,
                                  colbegin=search.item.col,
                                  colend=search.item.col +
                                  len(self.soucecode.search.pattern))
        pass

    def hightlight_code_line(self, y, colbegin=None, colend=None):
        code = self.code_editor_view()
        code.selection = Selection(
            start=(y, 0 if colbegin == None else colbegin),
            end=(y, code.region.width if colend == None else colend))

    def on_click_link(self, link, line=None):
        self.on_choose_file_from_event(link)
        if line != None:
            self.code_editor_scroll_view().scroll_to(y=line, animate=False)
        pass

    def on_message_line_change(self, message: message_line_change):
        if self.codeview_file != message.file:
            return
        y = message.line
        self.code_editor_scroll_view().scroll_to(y=y - 10, animate=False)
        self.hightlight_code_line(y)
        pass

    def on_changelspmessage(self, msg: changelspmessage) -> None:
        if self.codeview_file != msg.file:
            return
        if msg.refresh_symbol_view == True or self._symbolload.need_refresh(
                msg.file):
            self._symbolload = symbolload(msg.file, self.lsp)
            self.refresh_symbol_view()
        if msg.loc != None:
            line = msg.loc.range.start.line
            self.code_editor_scroll_view().scroll_to(y=max(line - 10, 0),
                                                     animate=False)
            range = msg.loc.range
            y = range.start.line
            b = range.start.character
            e = range.end.character
            self.hightlight_code_line(y, colbegin=b, colend=e)
        pass

    def change_lsp_file(self, file: str, loc: Optional[Location] = None):
        try:
            self.__change_lsp_file(file, loc)
        except Exception as e:
            self.logview.write_line(str(e))

    def __change_lsp_file(self, file: str, loc: Optional[Location] = None):

        def lsp_change(lsp: LspMain, file: str):
            lsp.changefile(file)
            self.post_message(changelspmessage(file, loc))

        t = ThreadPoolExecutor(1)
        t.submit(lsp_change, self.lsp, file)
        self.logview.write_line("open %s" % (file))

    def on_command_input(self, value):
        if self.vim.vi.find:
            self.vim.vi.find_enter = value
            return
        args = convert_command_args(value)
        try:
            ret = self.did_command_opt(value, args)
            if ret == True:
                return
        except Exception as e:
            self.logview.write_line(str(e))
            pass
        self.did_command_cmdline(args)

    def udpate_search_result_view(self):
        m = map(lambda x: str(x), self.search_result.data)
        self.searchview.setlist(list(m))

    def search_preview_ui(self, args: list[str]):
        key = args[0][1:].lower()
        changed = False
        if self.generic_search_mgr.key != key or self.generic_search_mgr.view != self.preview_focused:
            self.generic_search_mgr = generic_search(self.preview_focused, key)
            changed = True
        if changed == False:
            self.generic_search_mgr.get_next()
        f: Label = self.query_one("#f1", Label)

        if self.preview_focused == self.symbol_tree_view:
            if changed:
                ret = self.symbol_tree_view.search_word(key)
                for a in ret:
                    self.generic_search_mgr.add(a)
                self.symbol_tree_view.goto(self.generic_search_mgr.get_index())
            else:
                self.symbol_tree_view.goto(self.generic_search_mgr.get_next())
            pass
        elif self.preview_focused == self.history_view:
            if changed:
                for i in range(len(self.history.datalist)):
                    h = self.history.datalist[i].lower()
                    if h.find(key) > -1:
                        self.generic_search_mgr.add(i)
            self.history_view.index = self.generic_search_mgr.get_index()
            pass
        elif self.preview_focused == self.searchview:
            if changed:
                index = 0
                for s in self.search_result.data:
                    if str(s).lower().find(key) > -1:
                        self.generic_search_mgr.add(index)
                    index += 1
            self.searchview.index = self.generic_search_mgr.get_index()
            pass
        elif self.preview_focused == self.CodeView.textarea:
            if self.CodeView.textarea != None:
                if changed:
                    index = 0
                    for item in self.CodeView.textarea.document.lines:
                        if item.lower().find(key) > -1:
                            self.generic_search_mgr.add(index)
                        index += 1
                    pass
                else:
                    self.generic_search_mgr.get_next()
                    pass
                line = self.generic_search_mgr.get_index()
                sss = self.CodeView.textarea.document.lines[line]
                pos = SourceCodeSearch.Pos(line,
                                           col=sss.lower().find(key),
                                           text=key)
                self.soucecode.search.pattern = key
                self.code_to_search_position(ResultItemSearch(pos))
            pass
        elif self.preview_focused == self.callin.tree:
            if changed:
                self.callin.find_text(key)
                for i in range(len(self.callin.findresult)):
                    self.generic_search_mgr.add(i)
            else:
                self.callin.goto_next()
            pass
        f.update(str(self.generic_search_mgr))

    def on_vi_command(self, value: str):
        try:
            if self.vim.vi.find:
                value = self.vim.check_input()
                args = value.split(" ")
                self.search_preview_ui(args)
            pass
        except Exception as e:
            self.logview.write_line(str(e))
            pass

    def did_command_opt(self, value, args):
        self.logview.write_line(value)
        if len(args) > 0:
            if self.vim.vi.find: return
            if self.vim.vi.command:
                try:
                    args[0] = args[0][1:]
                except Exception as e:
                    self.logview.write_line(str(e))
            if args[0] == "set":
                if len(args) == 3:
                    if args[1] == 'maxlevel':
                        CallerWalker.maxlevel = int(args[2])
                        config.load().set("maxlevel", CallerWalker.maxlevel)
                    return
            elif args[0] == "help":
                self.help()
                return
            elif args[0] in set(["cn", "cp"]):
                self.search_prev_next(args[0] == "cp")
                pass
            elif args[0] == "grep":
                if len(args) > 1 and self.soucecode.search.pattern == args[1]:
                    if len(args) > 2 and args[2] == "-":
                        self.soucecode.search.index = self.soucecode.search.index + \
                            len(self.search_result.data)-1
                    else:
                        self.soucecode.search.index = self.soucecode.search.index + 1

                    index = self.soucecode.search.index % len(
                        self.search_result.data)
                    search = self.search_result.data[index]
                    self.code_to_search_position(search)
                    pass
                else:
                    word = args[1] if len(args) == 2 else ""
                    if word == "":
                        word = self.CodeView.get_select_wholeword()
                        self.logview.write_line("search word is [%s]" % (word))
                    if len(word) == 0:
                        return
                    self.search_word(word)
                pass
            elif args[0] == "view":
                view = args[1]
                self.focus_to_viewid(view)
            elif args[0] == clear_key:
                self.logview.clear()
            elif args[0] == "open":
                self.change_lsp_file(self.codeview_file)
            elif args[0] == "find":
                dir = args[1]
                if self.root.find(dir) == -1:
                    dir = self.root + dir
                    dir = os.path.realpath(dir)

                logui = self.logview
                self.logview.write_line("start to find %s" % (dir))
                t = ThreadPoolExecutor(1)

                def cb2(future):
                    try:
                        sss = future.result()
                        logui.write_line("find files %d" % (len(sss)))
                        self.post_message(mymessage(sss))
                    except Exception as e:
                        logui.write_line(str(e))
                        pass

                t.submit(TaskFindFile.run, dir,
                         args[1:]).add_done_callback(cb2)
                pass
            elif args[0] == "history":
                self.history_view.focus()
                self.refresh_history_view()
            elif args[0] == "symbol":
                self.symbol_tree_view.focus()
                self.refresh_symbol_view()
            else:
                return False
            return True
        return False

    def search_word(self, word):
        try:
            self.soucecode.search = SourceCodeSearch(file=self.codeview_file)
            ret = self.soucecode.search.search(word)
            self.search_result = SearchResults(
                list(map(lambda x: ResultItemSearch(x), ret)))
            self.udpate_search_result_view()
            self.focus_to_viewid("fzf")
            f: Label = self.query_one("#f1", Label)
            f.update("Search Result to <%d>" %
                     (self.search_result.result_number()) + word)
            search = self.search_result.get(0)
            if search != None:
                self.code_to_search_position(search)
        except Exception as e:
            self.logview.write_line(str(e))
            pass

    def search_prev_next(self, prev):
        if self.search_result.isType(ResultItemSearch):
            data = self.search_result.search_next(
            ) if prev == False else self.search_result.search_prev()
            self.code_to_search_position(data)
        elif self.search_result.isType(ResultItemRefer):
            s = self.search_result.search_next(
            ) if prev == False else self.search_result.search_prev()
            self.code_to_refer(s)  # type: ignore
            pass
        self.searchview.index = self.search_result.index

    def focus_to_viewid(self, view):
        try:
            v = self.query_one("#" + view)
            if v != None:
                v.focus()
        except:
            pass

    def did_command_cmdline(self, args):
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("-o", "--file", help="root path")
            parser.parse_args(args)
            if args.file != None:
                self.change_lsp_file(args.file)
        except:
            pass

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = self.root
        yield Header()
        with Container():
            yield DirectoryTree(path, id="tree-view")
            self.CodeView.loadfile(self.codeview_file)
            yield self.CodeView.textarea
            with TabbedContent(initial="symboltree", id="symbol-list"):
                with TabPane("Rencently", id="leto"):  # First tab
                    self.history_view = MyListView(id="history")
                    self.history_view.mainui = self
                    yield self.history_view
                with TabPane("Symbol", id="symboltree"):
                    yield self.symbol_tree_view
        # self.text = TextArea.code_editor("xxxx")
        # yield self.text

        with Container():
            with TabbedContent(initial="log-tab", id="bottom-tab"):
                with TabPane("Log", id="log-tab"):  # First tab
                    self.logview = MyLogView(id="log")
                    self.logview.mainuui = self
                    yield self.logview
                with TabPane("FZF", id="fzf-tab"):
                    self.searchview = MyListView(id='fzf')
                    self.searchview.mainui = self
                    yield self.searchview
                    pass
                with TabPane("callHierarchy incomming", id="callin-tab"):
                    yield self.callin.tree
                with TabPane("UML", id="uml"):
                    yield self.uml
        yield Label(id="f1")
        v = CommandInput(self, root=self.lsp.root)
        self.cmdline = v
        self.vim = vim(self)
        yield v
        yield Footer(id="f2")

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        self.on_choose_file_from_event(self.codeview_file)
        self.change_lsp_file(self.codeview_file)
        self.refresh_symbol_view()

    def refresh_history_view(self):
        aa = map(lambda x: ListItem(Label(os.path.basename(x))),
                 list(self.history.datalist))
        self.history_view.clear()
        self.history_view.extend(aa)

    def on_symbol_tree_update(self, message: symbol_tree_update):
        self.symbol_tree_view.on_symbol_tree_update(message)
        pass

    def refresh_symbol_view(self):

        def my_function():
            try:
                __my_function()
            except Exception as e:
                self.logview.write_line(str(e))
                pass

        def __my_function():
            file = self.lsp.currentfile.file
            liststr = self.lsp.currentfile.get_symbol_list_string()

            if file != self.codeview_file:
                return
            self.post_message(symbol_tree_update(self.lsp.currentfile))

        self.post_message(symbol_tree_update(None))
        ThreadPoolExecutor(1).submit(my_function)

    def on_directory_tree_file_selected(
            self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        self.on_choose_file_from_event(str(event.path))

    def code_editor_view(self) -> TextArea:
        return self.query_one("#code-view", TextArea)

    def code_editor_scroll_view(self):
        return self.query_one("#code-view")

    def on_choose_file_from_event(self,
                                  path: str,
                                  loc: Optional[Location] = None,
                                  backforward=False):
        if self.codeview_file == path:
            self.post_message(changelspmessage(path, loc, False))
            return
        # code_view = self.code_editor_view()
        self.CodeView.changefile(path)
        self.post_message(changelspmessage(path, loc, True))
        self.soucecode = SourceCode(self.codeview_file)
        self.code_editor_view().scroll_home(animate=False)
        self.sub_title = str(path)
        self.codeview_file = self.sub_title
        self.logview.write_line("tree open %s" % (self.sub_title))
        self.history.add_to_history(self.codeview_file, backforward)
        self.refresh_history_view()
        self.change_lsp_file(self.codeview_file, loc)

    def help(self):
        help = [
            "help", "opeh filepath", "history|code-view|fzf|symbol",
            "view history|code-view|fzf|symbol", "cn", "cp",
            "find       find file under directory \"find xx yy\"",
            "search     find word", "Ctrl Key:", "   o  goback",
            "   b  goforward", "Key:", "   j/k  down/up",
            "   f find current word", "   c CallIncomming",
            "   d goto declaration", "   i goto impl", "   r Refere"
        ]
        self.logview.write_lines(help)

    def action_open_file(self) -> None:
        if self.lsp.currentfile.file != self.codeview_file:
            self.change_lsp_file(self.codeview_file)

        pass

    async def action_quit(self) -> None:
        self.lsp.close()
        await App.action_quit(self)

    def is_foucused(self, dom: DOMNode):
        try:
            return dom.screen.focused == dom
        except:
            return False

    def action_goback(self) -> None:
        url = self.backforward.goback()
        self.on_choose_file_from_event(url, backforward=True)
        pass

    def action_goforward(self) -> None:
        url = self.backforward.goforward()
        self.on_choose_file_from_event(url, backforward=True)
        pass

    def on_code_message_impl(self, message: code_message_impl):
        if self.lsp.client is None:
            return
        file_location = self.lsp.client.get_impl(message.location)
        if file_location is None:
            return
        self.on_choose_file_from_event(from_file(file_location.uri),
                                       file_location)
        pass

    def on_message_get_symbol_callin(self, message: message_get_symbol_callin):
        self.action_callin_sym(message.sym)
        pass

    def on_code_message_decl(self, message: code_message_decl):
        if self.lsp.client is None:
            return
        try:
            ret = self.lsp.client.get_decl(message.location)
            if ret is None:
                return
            self.on_choose_file_from_event(from_file(ret.uri), ret)
        except Exception as e:
            self.logview.write_line(str(e))

            pass
        pass

    def on_code_message_refer(self, message: code_message_refer):
        try:

            def cursor_refer(client, message: code_message_refer):
                s = message.selection
                loc = message.location()
                ret = client.get_refer_from_cursor(loc, s.text)

                self.post_message(refermessage(ret, message.key))

            ThreadPoolExecutor(1).submit(cursor_refer, self.lsp.client,
                                         message)
            pass

        except Exception as e:
            self.log.error("exception %s" % (str(e)))
            self.logview.write_line("exception %s" % (str(e)))
            pass

    def on_message_get_symbol_refer(self, message: message_get_symbol_refer):
        try:
            self.get_symbol_refer(sym=message.sym)
        except Exception as e:
            self.logview.write_line(str(e))
            pass
        pass

    def get_symbol_refer(self, sym: Symbol) -> None:

        def my_function(lsp: LspMain, sym: SymbolInformation, toFile):
            ret = []
            try:
                ret = lsp.currentfile.refer_symbolinformation(sym,
                                                              toFile=toFile)
            except Exception as e:
                self.logview.write_line(str(e))
                pass
            self.logview.write_line("Call Job finished")
            key = '''[u]%s[/u]''' % (str(Body(sym.location)).replace(
                "\n", "")) + "%s:%d" % (from_file(
                    sym.location.uri), sym.location.range.start.line)
            self.post_message(refermessage(ret, key))
            return ret

        q = LspQuery(sym.sym.name, "r")
        if q != self.symbol_query:
            if self.tofile != None:
                self.tofile.close()
            self.tofile = UiOutput(q.data + ".txt")
            self.tofile.ui = self.logview
            ThreadPoolExecutor(1).submit(my_function,
                                         self.lsp,
                                         sym.sym,
                                         toFile=self.tofile)

    def action_callin_sym(self, sym: Symbol) -> None:
        # if self.thread!=None:
        #     if self.thread.is_alive():
        #         self.logview.write_line("Wait for previous call finished")
        #         return
        def my_function(lsp: LspMain, sym: SymbolInformation, toFile, toUml):
            try:
                self.logview.write_line("Callin Job %s Started" % (sym.name))

                class callin_ui_cb(task_callback):

                    def __init__(self, app: App) -> None:
                        super().__init__()
                        self.app = app

                    def update(self, a):
                        if isinstance(a, task_call_in.message):
                            self.app.post_message(callin_message(message=a))
                        pass

                cb = callin_ui_cb(self)
                cb.toUml = toUml
                cb.toFile = toFile
                task = lsp.currentfile.callin(
                    sym,
                    once=False,
                    cb=cb,
                )
                self.taskmanager.add(task)
                task.run()
                self.logview.write_line("Callin Job %s Stopped" % (sym.name))
            except Exception as e:
                self.logview.write_line("exception %s" % (str(e)))
                pass

        q = LspQuery(sym.symbol_display_name(), "callin")
        if q != self.symbol_query:
            if self.tofile != None:
                self.tofile.close()
            dir = "output"
            if os.path.exists(dir) == False:
                os.mkdir(dir)
            self.tofile = UiOutput(os.path.join(dir, q.data + ".txt"))
            self.tofile.ui = self.logview

            if self.toUml != None:
                self.toUml.close()
            self.toUml = UiOutput(os.path.join(dir, q.data + ".qml"))
            self.toUml.ui = self.logview
            ThreadPoolExecutor(1).submit(my_function, self.lsp, sym.sym,
                                         self.tofile, self.toUml)
            self.logview.focus()

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        if self.CodeView.is_focused():
            range = self.CodeView.get_select_range()
            if range is None:
                w = self.CodeView.get_select_wholeword()
            elif range.text != None:
                if len(range.text) <= 1:
                    w = self.CodeView.get_select_wholeword()
                else:
                    w = range.text
            else:
                w = self.CodeView.get_select_wholeword()
            if len(w):
                self.search_word(w)
            return
        self.show_tree = not self.show_tree

    def __del__(self):
        self.lsp.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--root", help="root path")
    parser.add_argument("-f", "--file", help="root path")
    args = parser.parse_args()
    CodeBrowser(root=args.root, file=args.file).run()
