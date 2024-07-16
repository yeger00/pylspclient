"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import sys
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
from textual.suggester import SuggestFromList, SuggestionReady
from textual.widgets import Log, TextArea
from rich.syntax import Syntax
from rich.traceback import Traceback
from textual.dom import DOMNode
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, Static
from textual.widgets import Footer, Label, ListItem, ListView
from callinview import CallTreeNode, callinopen, callinview, uicallback
from codesearch import ResultItem, ResultItemRefer, ResultItemSearch, ResultItemString, SearchResults, SourceCode
from cpp_impl import Body, from_file, to_file
from codetask import TaskManager
from lspcpp import CallNode, LspMain, Symbol, OutputFile, SymbolLocation, task_call_in, task_callback
from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.widgets import Footer, Label, TabbedContent, TabPane

from pylspclient.lsp_pydantic_strcuts import Location, Position, Range, SymbolInformation

find_key = "find "
view_key = "view "
clear_key = "clear"
input_command_options = [
    "history", "symbol", "open", "find", "refer", "callin", "ctrl-c", "copy",
    "save", "log", "quit", "grep", "view", "clear"
]


class CodeView:
    textarea: TextArea | None = None

    def __init__(self, textarea: TextArea | None = None) -> None:
        self.textarea = textarea
        pass

    def key_down(self, down=True):
        if self.textarea is None:
            return
        begin = self.textarea.selection.start[0]
        # self.textarea.selection.start.
        self.textarea.select_line(begin + 1 if down else begin - 1)

    def is_focused(self):
        if self.textarea is None:
            return False
        return self.textarea.screen.focused == self.textarea

    class Selection:
        range: Range
        text: str

    def get_select_range(self) -> Selection | None:
        if self.textarea is None:
            return None
        begin = self.textarea.selection.start
        end = self.textarea.selection.end
        r = Range(start=Position(line=begin[0], character=begin[1]),
                  end=Position(line=end[0], character=end[1]))
        s = CodeView.Selection()
        s.range = r
        s.text = self.textarea.selected_text
        return s

    def get_select_wholeword(self) -> str:
        r = self.get_select_range()
        if self.textarea is None:
            return ""
        if r is None:
            return ""
        linenum = r.range.start.line
        b = r.range.start.character
        e = r.range.end.character
        line = self.textarea.document.lines[linenum]
        ignore_set = set(
            [' ', ',', '{', '-', '}', ';', '.', '(', ')', '/', '"'])
        while b - 1 >= 0:
            if line[b - 1] in ignore_set:
                break
            else:
                b = b - 1

        while e + 1 < len(line):
            if line[e + 1] in ignore_set:
                break
            else:
                e += 1
        return line[b:e + 1]

    def get_select(self) -> str:
        if self.textarea is None:
            return ""
        return self.textarea.selected_text


def convert_command_args(value):
    args = list(filter(lambda x: len(x) > 0, value.split(" ")))
    return args


def build_dirs(directory):
    files_found = {}
    for root, dirs, _, in os.walk(directory):
        aa = root.replace(directory, "").split("/")
        if len(aa) > 3:
            continue
        for file in dirs:
            key = os.path.join(root, file)
            files_found[key.replace(directory, "")] = True
            # files_found[file] = os.path.join(root, file)
    return files_found


class dir_complete_db:

    def __init__(self, root) -> None:
        self.root = root
        self.db = build_dirs(root)
        pass

    def find(self, pattern):
        try:
            if self.db[pattern]:
                return str(pattern)[1:]
        except:

            if pattern[-1] == "/":
                # pattern = pattern[:-1]
                # keys= list(filter(lambda x: os.path.dirname(x)==pattern,self.db.keys()))
                root = os.path.join(self.root, pattern[1:])
                keys = os.listdir(root)
                keys = list(
                    filter(lambda x: os.path.isdir(os.path.join(root, x)),
                           keys))
                keys = sorted(keys, key=lambda x: x)
                keys = list(set(list(map(lambda x: x[:2], keys))))
                keys = sorted(keys, key=lambda x: x)
                # return pattern + "|".join(keys[0:20])
                return pattern + "|".join(keys)
            else:
                keys = list(
                    filter(lambda x: x.startswith(pattern), self.db.keys()))
                keys = sorted(keys, key=lambda x: len(x))
                if len(keys):
                    return keys[0][1:]

        return None


def find_dirs_os_walk(directory, pattern):
    files_found = []
    for root, dirs, _, in os.walk(directory):
        for file in dirs:
            if file.startswith(pattern):
                files_found.append(os.path.join(root, file))
    return files_found


def find_files_os_walk(directory, file_extension):
    files_found = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.find(file_extension) > 0:
                files_found.append(os.path.join(root, file))
    return files_found


# def thread_submit(fn, cb, args: tuple):
#     with ThreadPoolExecutor(max_workers=2) as executor:
#         future = executor.submit(fn, *args)
#             cb(future.result())
#         future.add_done_callback(done,cb)
#         # result = future.result()
#         # cb(result)
#


class TaskFindFile:

    def __init__(self, dir, pattern: list[str]) -> None:
        self.dir = dir
        self.pattern = list(filter(lambda x: x[0] != '!', pattern))
        self.exclude_pattern = list(
            map(lambda x: x[1:], filter(lambda x: x[0] == '!', pattern)))
        self.ret = []
        pass

    def match_pattern(self, path):
        for p in self.exclude_pattern:
            if path.find(p) > -1:
                return False
        for p in self.pattern:
            if path.find(p) == -1:
                return False

        return True

    def get(self):
        files_found = []
        if self.dir is None:
            return files_found
        for root, _, files in os.walk(self.dir):
            for file in files:
                p = os.path.join(root, file)
                if self.match_pattern(p):
                    files_found.append(p)
        return files_found

    @staticmethod
    def run(dir, pattern):
        fileset = ["h", "c", "hpp", "cc", "cpp"]

        def extfilter(x: str):
            for s in fileset:
                if x.endswith(s):
                    return True
            return False

        ret = list(filter(extfilter, TaskFindFile(dir, pattern).get()))
        return ret


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


class history:
    datalist: list[str]

    def __init__(self, file=None) -> None:
        self._data = set()
        self.datalist = list(self._data)
        self.file = file
        if file != None:
            try:
                self.datalist = list(
                    map(lambda x: x.replace("\n", ""),
                        open(file, "r").readlines()))
                self._data = set(self.datalist)
            except:
                pass
        pass

    def add_to_history(self, data, barckforward=False):
        self._data.add(data)
        self.datalist = list(filter(lambda x: x != data, self.datalist))
        self.datalist.insert(0, data)
        if self.file != None:
            open(self.file, "w").write("\n".join(self.datalist))


class BackFoward:

    def __init__(self, h: history) -> None:
        self.history = h
        self.index = 0
        pass

    def goback(self) -> str:
        self.index += 1
        self.index = min(len(self.history.datalist) - 1, self.index)
        ret = self.history.datalist[self.index]
        return ret

    def goforward(self) -> str:
        self.index -= 1
        self.index = max(0, self.index)
        ret = self.history.datalist[self.index]
        return ret


class input_suggestion(SuggestFromList):
    _history: history
    dircomplete: dir_complete_db

    async def _get_suggestion(self, requester, value: str) -> None:
        """Used by widgets to get completion suggestions.

        Note:
            When implementing custom suggesters, this method does not need to be
            overridden.

        Args:
            requester: The message target that requested a suggestion.
            value: The current value to complete.
        """

        args = convert_command_args(value)
        suggestion = None
        if suggestion is None:
            suggestion = self.complete_view(value, args)

        if suggestion != None:
            requester.post_message(SuggestionReady(value, suggestion))

        normalized_value = value if self.case_sensitive else value.casefold()
        if self.cache is None or normalized_value not in self.cache:
            suggestion = await self.get_suggestion(normalized_value)
            if self.cache is not None:
                self.cache[normalized_value] = suggestion
        else:
            suggestion = self.cache[normalized_value]

        if suggestion is None:
            suggestion = self.complete_path(value, args)
        if suggestion is None:
            ret = list(
                filter(lambda x: x.startswith(value), self._history._data))
            if len(ret) > 0:
                suggestion = ret[0]
        if suggestion is None:
            return
        requester.post_message(SuggestionReady(value, suggestion))

    def complete_view(self, value: str, args):
        view_name = ["code", "explore", "symbol", "history"]
        try:
            if value.startswith(view_key) == False:
                return None
            if len(args) == 2:
                for a in view_name:
                    if a.startswith(args[1]):
                        args[1] = a
                        return " ".join(args)

        except:
            pass
        return None

    def complete_path(self, value: str, args):
        try:
            # if self.root is None: return None
            if value.startswith(find_key) == False:
                return None
            if self.dircomplete != None:
                if len(args) == 2:
                    s = self.dircomplete.find(args[1])
                    if s != None:
                        part1 = value[0:value.find(args[1])]
                        return part1 + "/" + s

            # ret = find_dirs_os_walk(self.root, args[1])
            # if len(ret):
            # return ret[0]
        except Exception as e:
            print(e)
            pass
        return None


class CommandInput(Input):
    mainui: 'CodeBrowser'

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


class mymessage(Message):

    def __init__(self, s: list[str]) -> None:
        super().__init__()
        self.s = s


class changelspmessage(Message):
    loc: Optional[Location] = None

    def __init__(self,
                 file,
                 loc: Optional[Location] = None,
                 refresh=True) -> None:
        super().__init__()
        self.loc = loc
        self.file = file
        self.refresh_symbol_view = refresh

    pass


class symbolsmessage(Message):
    data = []
    file: str

    def __init__(self, data, file: str) -> None:
        super().__init__()
        self.file = file
        self.data = data


class callin_message(Message):
    task: Optional[task_call_in]

    def __init__(self,
                 task: Optional[task_call_in] = None,
                 call: Optional[CallNode] = None) -> None:
        super().__init__()
        self.task = task
        self.call = call


class refermessage(Message):
    s: list[SymbolLocation]
    query: str

    def __init__(self, s: list[SymbolLocation], key: str) -> None:
        super().__init__()
        self.query = key
        self.s = s


class MyListView(ListView):
    mainui: uicallback

    def setlist(self, data: list[str]):
        self.clear()
        self.extend(list(map(lambda x: ListItem(Label(x)), data)))

    def _on_list_item__child_clicked(self,
                                     event: ListItem._ChildClicked) -> None:
        ListView._on_list_item__child_clicked(self, event)
        self.mainui.on_select_list(self)

    def action_select_cursor(self):
        self.mainui.on_select_list(self)


class generic_search:
    indexlist: list[int] = []
    view: object
    key: str

    def __init__(self, view: object, key: str = "") -> None:
        self.view = view
        self.key = key
        self.indexlist = []
        self.currentindex = 0
        pass

    def get_next(self) -> int:
        self.currentindex += 1
        self.currentindex = self.currentindex % len(self.indexlist)
        return self.indexlist[self.currentindex]

    def get_index(self) -> int:
        return self.indexlist[self.currentindex]

    def add(self, index: int):
        self.indexlist.append(index)

    def result_number(self) -> int:
        return len(self.indexlist)


class CodeBrowser(App, uicallback):
    root: str
    symbol_query = LspQuery("", "")
    codeview_file: str
    search_result: SearchResults
    symbol_listview: MyListView
    history_view: MyListView
    lsp: LspMain
    callin: callinview
    preview_focused: Optional[Widget]
    symbols_list: list[Symbol] = []
    generic_search_mgr: generic_search

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
        self.CodeView = CodeView(None)
        self.callin = callinview()
        self.taskmanager = TaskManager()
        self.preview_focused = None
        self.generic_search_mgr = generic_search(None, "")
        # self.lsp.currentfile.save_uml_file = self.print_recieved
        # self.lsp.currentfile.save_stack_file = self.print_recieved

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
        if message.task != None:
            self.callin.update_job(message.task)
            f: Label = self.query_one("#f1", Label)
            self.callin.status = "call in to <%d> " % (len(
                message.task.callin_all)) + message.task.displayname()
            f.update(self.callin.status)
            # if len(message.task.callin_all) > 0:
            #     self.callin.tree.focus()

        pass

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
            if selection is None:
                return
            l = self.lsp.currentfile.symbols_list
            max = 10
            index = None
            closest = None
            i = 0
            for item in l:
                gap = abs(selection.range.start.line -
                          item.sym.location.range.start.line)
                if gap < max:
                    index = i
                    max = gap
                    closest = item
                i += 1
            if index != None:
                self.symbol_listview.index = index
        except Exception as e:
            self.logview.write_line(str(e))

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
        ("escape", "focus_input", "Focus to cmdline"),
        ("ctrl+o", "goback", "Go Back"),
        ("ctrl+b", "goforward", "Go Forward"),
        ("c", "callin", "CallIn"),
        ("o", "open_file", "Open"),
        ("d", "go_declare", "Go to declare"),
        ("D", "go_impl", "Go to Define"),
        ("r", "refer", "Reference"),
    ]

    show_tree = var(True)

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

    def action_focus_input(self) -> None:
        if self.screen.focused != self.cmdline:
            self.preview_focused = self.screen.focused
            self.cmdline.focus()
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
        elif self.symbol_listview == list:
            try:
                if list.index == None:
                    return
                sym: Symbol = self.lsp.currentfile.symbols_list[list.index]
                y = sym.sym.location.range.start.line
                self.code_editor_scroll_view().scroll_to(y=y - 10,
                                                         animate=False)
                self.hightlight_code_line(y)
                # code_view.selection=Selection(start=(0,y),end=(10,y))
                pass
            except Exception as e:
                self.logview.write_line(str(e))
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

    def on_changelspmessage(self, msg: changelspmessage) -> None:
        if self.codeview_file != msg.file:
            return
        if msg.refresh_symbol_view == True:
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

        def lsp_change(lsp: LspMain, file: str):
            lsp.changefile(file)
            self.post_message(changelspmessage(file, loc))

        self.symbol_listview.clear()
        self.symbol_listview.loading = True
        t = ThreadPoolExecutor(1)
        t.submit(lsp_change, self.lsp, file)
        self.logview.write_line("open %s" % (file))

    def on_command_input(self, value):
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
        key = args[0][2:]
        changed = False
        if self.generic_search_mgr.key != key or self.generic_search_mgr.view != self.preview_focused:
            self.generic_search_mgr = generic_search(self.preview_focused, key)
            changed = True
        if changed == False:
            self.generic_search_mgr.get_next()
        f: Label = self.query_one("#f1", Label)

        if self.preview_focused == self.history:
            pass
        elif self.preview_focused == self.symbol_listview:
            if changed == True:
                for i in range(len(self.symbols_list)):
                    l = self.symbols_list[i]
                    if l.symbol_display_name().find(key) > -1:
                        self.generic_search_mgr.add(i)
            self.symbol_listview.index = self.generic_search_mgr.get_index()
            pass
        elif self.preview_focused == self.searchview:
            pass
        elif self.preview_focused == self.CodeView.textarea:
            pass
        elif self.preview_focused == self.callin.tree:
            pass
        f.update("Search Result to <%d>" %
                 (self.generic_search_mgr.result_number()) + key)

    def did_command_opt(self, value, args):
        self.logview.write_line(value)
        if len(args) > 0:
            if args[0].find(":/") != -1:
                self.search_preview_ui(args)
                return True
            elif args[0] == "help":
                self.help()
                return
            if args[0] in set(["cn", "cp"]):
                self.search_prev_next(args[0] == "cp")
                pass

            if args[0] == "search":
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
                self.symbol_listview.focus()
                self.refresh_symbol_view()
            elif args[0] == "refer":
                self.action_refer()
            else:
                return False
            return True
        return False

    def search_word(self, word):
        try:
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
            from tree_sitter_languages import get_language
            from pathlib import Path
            code = TextArea.code_editor(Path(self.codeview_file).read_text(),
                                        id="code-view",
                                        read_only=True)
            self.CodeView.textarea = code
            try:
                cpp = get_language("cpp")
                cpp_highlight_query = (Path(__file__).parent /
                                       "queries/c/highlights.scm").read_text()
                code.register_language(cpp, cpp_highlight_query)
                code.language = "cpp"
            except Exception as e:
                self.log.error(str(e))
                pass
            yield code
            with TabbedContent(initial="jessica", id="symbol-list"):
                with TabPane("Rencently", id="leto"):  # First tab
                    self.history_view = MyListView(id="history")
                    self.history_view.mainui = self
                    yield self.history_view
                with TabPane("Symbol", id="jessica"):
                    self.symbol_listview = MyListView(id="symbol")
                    self.symbol_listview.mainui = self
                    yield self.symbol_listview
        yield Label(id="f1")
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
                with TabPane("CallInView", id="callin-tab"):
                    yield self.callin.tree
                    # tree: Tree[dict] = Tree("Dune")
                    # tree.root.expand()
                    # characters = tree.root.add("Characters", expand=True)
                    # characters.add_leaf("Paul")
                    # characters.add_leaf("Jessica")
                    # characters.add_leaf("Chani")
                    # yield tree
                    # pass
        v = CommandInput(self, root=self.lsp.root)
        self.cmdline = v
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

    def on_symbolsmessage(self, message: symbolsmessage) -> None:
        try:
            if message.file != self.codeview_file:
                return
            self.symbol_listview.clear()
            self.symbol_listview.extend(message.data)
            self.logview.write_line(
                "on_symbolsmessage %s %d" %
                (self.lsp.currentfile.file, len(message.data)))
        except Exception as e:
            self.logview.write_line("exception %s" % (str(e)))
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
            self.symbol_listview.loading = True
            aa = map(lambda x: ListItem(Label(x)),
                     self.lsp.currentfile.get_symbol_list_string())
            self.symbol_listview.loading = False
            if file != self.codeview_file:
                return
            self.symbols_list = self.lsp.currentfile.symbols_list
            self.post_message(symbolsmessage(list(aa), file))

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
        code_view = self.code_editor_view()

        TEXT = open(str(path), "r").read()
        # code_view.document = Document(TEXT)
        code_view.load_text(TEXT)
        self.post_message(changelspmessage(path, loc, False))
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

    def on_choose_file_from_event_static(self, path):
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.code_editor_scroll_view().scroll_home(animate=False)
            self.sub_title = str(path)
            self.codeview_file = self.sub_title
            self.logview.write_line("tree open %s" % (self.sub_title))
            self.history.add_to_history(self.codeview_file)
            self.refresh_history_view()
            self.change_lsp_file(self.codeview_file)

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

    def action_go_declare(self) -> None:
        if self.lsp.client is None:
            return
        if self.CodeView.is_focused():
            range = self.CodeView.get_select_range()
            if range is None:
                return
            loc = Location(uri=to_file(self.codeview_file), range=range.range)
            file_location = self.lsp.client.get_decl(loc)
            if file_location is None:
                return
            self.on_choose_file_from_event(from_file(file_location.uri),
                                           file_location)
            pass
        pass

    def action_go_impl(self) -> None:
        if self.lsp.client is None:
            return
        if self.CodeView.is_focused():
            range = self.CodeView.get_select_range()
            if range is None:
                return
            loc = Location(uri=to_file(self.codeview_file), range=range.range)
            file_location = self.lsp.client.get_impl(loc)
            if file_location is None:
                return
            self.on_choose_file_from_event(from_file(file_location.uri),
                                           file_location)
            pass
        pass
        pass

    def action_refer(self) -> None:
        try:

            if self.is_foucused(self.symbol_listview):
                self.get_refer_for_symbol_list()
            elif self.CodeView.is_focused():
                s = self.CodeView.get_select_range()
                if s is None:
                    return

                def cursor_refer():
                    if self.lsp.client is None:
                        return

                    loc = Location(uri=to_file(self.codeview_file),
                                   range=s.range)
                    ret = self.lsp.client.get_refer_from_cursor(loc, s.text)
                    key1 = str(Body(loc)).replace("\n", "")
                    key2 = self.CodeView.get_select_wholeword()
                    key = key1 if len(key1) > len(key2) else key2 + \
                        " %s:%d" % (from_file(loc.uri), loc.range.start.line)
                    self.post_message(refermessage(ret, key))

                ThreadPoolExecutor(1).submit(cursor_refer)
                pass

        except Exception as e:
            self.log.error("exception %s" % (str(e)))
            self.logview.write_line("exception %s" % (str(e)))
            pass

    def get_refer_for_symbol_list(self) -> None:
        if self.symbol_listview.index is None:
            return None
        sym: Symbol = self.lsp.currentfile.symbols_list[
            self.symbol_listview.index]
        self.get_symbol_refer(sym=sym)

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

    def action_callin(self) -> None:
        if self.is_foucused(self.symbol_listview):
            self.action_callin_symlist()
        else:
            pass

    def action_callin_symlist(self) -> None:
        if self.symbol_listview.index is None:
            return
        sym = self.lsp.currentfile.symbols_list[self.symbol_listview.index]
        self.action_callin_sym(sym)

    def action_callin_sym(self, sym: Symbol) -> None:
        # if self.thread!=None:
        #     if self.thread.is_alive():
        #         self.logview.write_line("Wait for previous call finished")
        #         return
        def my_function(lsp: LspMain, sym: SymbolInformation, toFile, toUml):
            try:
                self.logview.write_line("Callin Job %s Started" % (sym.name))
                filepath = from_file(sym.location.uri)

                class callin_ui_cb(task_callback):

                    def __init__(self, app: App) -> None:
                        super().__init__()
                        self.app = app

                    def update(self, task):
                        if isinstance(task, task_call_in):
                            self.app.post_message(
                                callin_message(task=task, call=None))
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
            self.tofile = UiOutput(q.data + ".txt")
            self.tofile.ui = self.logview

            if self.toUml != None:
                self.toUml.close()
            self.toUml = UiOutput(q.data + ".qml")
            self.toUml.ui = self.logview
            ThreadPoolExecutor(1).submit(my_function, self.lsp, sym.sym,
                                         self.tofile, self.toUml)
            self.logview.focus()

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        if self.CodeView.is_focused():
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
