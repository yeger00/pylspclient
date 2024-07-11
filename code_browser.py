"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

from textual.scroll_view import ScrollView
from textual.widgets.text_area import Document, Selection
from concurrent.futures import ThreadPoolExecutor
import os
import re
import asyncio
import threading
from rich.repr import Result
from textual import on
import argparse
from textual.message_pump import events
from textual.suggester import SuggestFromList, SuggestionReady
from textual.validation import Failure
from textual.widgets import Log, TextArea

from pydantic import Field, NatsDsn
from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.color import Lab
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, Static
from textual.widgets import Footer, Label, ListItem, ListView
from codesearch import SourceCode, SourceCodeSearch
from lspcpp import LspMain, Symbol, OutputFile, lspcpp
from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.widgets import Footer, Label, TabbedContent, TabPane

find_key = "find "
view_key = "view "
clear_key = "clear"
input_command_options = [
    "history", "symbol", "open", "find", "refer", "callin", "ctrl-c", "copy",
    "save", "log", "quit", "grep", "view", "clear"
]


class ResultItem:

    def __init__(self) -> None:
        pass


class ResultItemString(ResultItem):

    def __init__(self, s) -> None:
        super().__init__()
        self.__str = s

    def __str__(self) -> str:
        return self.__str


class ResultItemSearch(ResultItem):

    def __init__(self, item: SourceCodeSearch.Pos) -> None:
        super().__init__()
        self.item = item

    def __str__(self) -> str:
        return str(self.item)


class ResultItemSymbo(ResultItem):

    def __init__(self, s: Symbol) -> None:
        super().__init__()
        self.symbol = s


class SearchResults:
    list: list[ResultItem]

    def __init__(self, list: list[ResultItem] = []):
        self.list = list


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
                pass
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
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.find(file_extension) > 0:
                files_found.append(os.path.join(root, file))
    return files_found


def thread_submit(fn, cb, args: tuple):
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(fn, *args)
        result = future.result()
        cb(result)


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
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                p = os.path.join(root, file)
                if self.match_pattern(p):
                    files_found.append(p)
        return files_found

    @staticmethod
    def run(dir, pattern, cb):
        fileset = ["h", "c", "hpp", "cc", "cpp"]

        def fn(dir, pattern):

            def extfilter(x: str):
                for s in fileset:
                    if x.endswith(s):
                        return True
                return False

            return list(filter(extfilter, TaskFindFile(dir, pattern).get()))

        thread_submit(fn, cb, (dir, pattern))


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

    def __init__(self, name, type) -> None:
        self.data = name
        self.type = type
        pass

    def __eq__(self, value: object) -> bool:
        return self.data == value.data and self.type == value.type


class history:

    def __init__(self, file=None) -> None:
        self._data = set()
        self.list = list(self._data)
        self.file = file
        if file != None:
            try:
                self.list = map(lambda x: x.replace("\n", ""),
                                open(file, "r").readlines())
                self._data = set(self.list)
            except:
                pass
        pass

    def add_to_history(self, data):
        self._data.add(data)
        self.list = list(self._data)
        if self.file != None:
            open(self.file, "w").write("\n".join(self.list))


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
        except:
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
            pass


SYMBOL_LISTVIEW_TYPE = 1
HISTORY_LISTVIEW_TYPE = 2


class MyListView(ListView):
    mainui: 'CodeBrowser'

    def setlist(self, data: list[str]):
        self.clear()
        self.extend(list(map(lambda x: ListItem(Label(x)), data)))

    def _on_list_item__child_clicked(self,
                                     event: ListItem._ChildClicked) -> None:
        ListView._on_list_item__child_clicked(self, event)
        self.mainui.on_select_list(self)

    def action_select_cursor(self):
        self.mainui.on_select_list(self)


class CodeBrowser(App):
    root: str
    symbol_query = LspQuery("", "")
    codeview_file: str
    search_result: SearchResults | None = None

    def __init__(self, root, file):
        App.__init__(self)
        self.thread = None
        self.lsp = LspMain(root=root, file=file)
        self.root = root
        self.tofile = None
        self.toUml = None
        self.codeview_file = self.sub_title = file
        self.history = history()
        self.history.add_to_history(self.codeview_file)
        self.symbol_listview_type = SYMBOL_LISTVIEW_TYPE
        # self.lsp.currentfile.save_uml_file = self.print_recieved
        # self.lsp.currentfile.save_stack_file = self.print_recieved

    """Textual code browser app."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
        ("i", "focus_input", "Focus to cmdline"),
        ("c", "callin", "CallIn"),
        ("o", "open_file", "Open"),
        ("r", "refer", "Reference"),
    ]

    show_tree = var(True)

    def action_focus_input(self) -> None:
        self.cmdline.focus()
        pass

    def on_select_list(self, list: ListView):
        if self.searchview == list:
            result = self.search_result.list[list.index]
            if isinstance(result, ResultItemString):
                self.on_choose_file_from_event(
                    str(result))
            elif isinstance(result, ResultItemSearch):
                search: ResultItemSearch = result
                y = search.item.line
                self.code_editor_scroll_view().scroll_to(y=y - 10,
                                                         animate=False)
                self.hightlight_code_line(
                    y, colbegin=search.item.col, colend=search.item.col+len(self.soucecode.search.pattern))
                pass
        if self.history_view == list:
            self.on_choose_file_from_event(self.history.list[list.index])
        elif self.symbol_listview == list:
            try:
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

    def hightlight_code_line(self, y, colbegin=None, colend=None):
        code: TextArea.code_editor = self.code_editor_view()
        code.selection = Selection(start=(y, 0 if colbegin == None else colbegin), end=(
            y, code.region.width if colend == None else colend))

    def on_click_link(self, link, line=None):
        self.on_choose_file_from_event(link)
        if line != None:
            self.code_editor_scroll_view().scroll_to(y=line, animate=False)
        pass

    def change_lsp_file(self, file):

        def my_function(_self, file):
            try:
                _self.lsp.changefile(file)
                _self.refresh_symbol_view()
                _self.logview.write_line("open %s finished" % (file))
            except Exception as e:
                _self.logview.write_line("open %s error %s" % (file, str(e)))

        self.symbol_listview.clear()
        # thread = threading.Thread(target=my_function, args=(self, file))
        # thread.start()
        my_function(self, file)
        self.logview.write_line("open %s" % (file))

    def on_command_input(self, value):
        args = convert_command_args(value)
        try:
            ret = self.did_command_opt(value, args)
            if ret == True:
                return
        except Exception as e:
            pass
        self.did_command_cmdline(args)

    def udpate_search_result_view(self):
        m = map(lambda x: str(x), self.search_result.list)
        self.searchview.setlist(list(m))

    def did_command_opt(self, value, args):
        self.logview.write_line(value)
        if len(args) > 0:
            if args[0] == "search":
                ret = self.soucecode.search.search(args[1])
                self.search_result = SearchResults(
                    list(map(lambda x: ResultItemSearch(x), ret)))
                self.udpate_search_result_view()
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

                def cb(s: list[str]):
                    try:
                        logui.write_line("find files %d" % (len(s)))
                        self.search_result = SearchResults(
                            list(map(lambda x: ResultItemString(x), s)))
                        # logui.write_lines(s)
                        self.searchview.setlist(s)
                    except Exception as e:
                        logui.write_line(str(e))
                        pass

                self.logview.write_line("start to find %s" % (dir))
                TaskFindFile.run(dir, args[1:], cb)
                pass
            elif args[0] == "history":
                self.refresh_history_view()
            elif args[0] == "symbol":
                self.refresh_symbol_view()
            elif args[0] == "refer":
                self.action_refer()
            else:
                return False
            return True
        return False

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
            try:
                cpp = get_language("cpp")
                cpp_highlight_query = (Path(__file__).parent /
                                       "queries/c/highlights.scm").read_text()
                code.register_language(cpp, cpp_highlight_query)
                code.language = "cpp"
            except Exception as e:
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
        yield Footer()
        # self.text = TextArea.code_editor("xxxx")
        # yield self.text

        with Container():
            with TabbedContent(initial="log-tab"):
                with TabPane("Log", id="log-tab"):  # First tab
                    self.logview = MyLogView(id="log")
                    self.logview.mainuui = self
                    yield self.logview
                with TabPane("Fzf", id="fzf-tab"):
                    self.searchview = MyListView(id='fzf')
                    self.searchview.mainui = self
                    yield self.searchview
                    pass
        v = CommandInput(self, root=self.lsp.root)
        self.cmdline = v
        yield v
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        self.on_choose_file_from_event(self.codeview_file)
        self.change_lsp_file(self.codeview_file)
        self.refresh_symbol_view()

    def refresh_history_view(self):
        aa = map(lambda x: ListItem(Label(os.path.basename(x))),
                 list(self.history.list))
        self.history_view.clear()
        self.history_view.extend(aa)

    def refresh_symbol_view(self):
        aa = map(lambda x: ListItem(Label(x)),
                 self.lsp.currentfile.symbol_list_string())
        self.symbol_listview.clear()
        self.symbol_listview.extend(list(aa))
        self.logview.write_line("open %s" % (self.lsp.currentfile.file))

    def on_directory_tree_file_selected(
            self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        self.on_choose_file_from_event(str(event.path))

    def code_editor_view(self):
        return self.query_one("#code-view", TextArea)

    def code_editor_scroll_view(self):
        return self.query_one("#code-view")

    def on_choose_file_from_event(self, path):
        code_view = self.code_editor_view()

        TEXT = open(str(path), "r").read()
        code_view.document = Document(TEXT)
        self.soucecode = SourceCode(self.codeview_file)
        self.code_editor_view().scroll_home(animate=False)
        self.sub_title = str(path)
        self.codeview_file = self.sub_title
        self.logview.write_line("tree open %s" % (self.sub_title))
        self.history.add_to_history(self.codeview_file)
        self.refresh_history_view()
        self.change_lsp_file(self.codeview_file)

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

    def action_refer(self) -> None:
        # if self.thread!=None:
        #     if self.thread.is_alive():
        #         self.logview.write_line("Wait for previous call finished")
        #         return
        def my_function(lsp, q: LspQuery, toFile, toUml):
            try:
                lsp.currentfile.refer(q.data, toFile=toFile)
            except Exception as e:
                self.logview.write_line(str(e))
                pass
            self.logview.write_line("Call Job finished")

        sym = self.lsp.currentfile.symbols_list[self.symbol_listview.index]
        q = LspQuery(sym.symbol_display_name(), "r")
        if q != self.symbol_query:
            if self.tofile != None:
                self.tofile.close()
            self.tofile = UiOutput(q.data + ".txt")
            self.tofile.ui = self.logview

            if self.toUml != None:
                self.toUml.close()
            self.toUml = UiOutput(q.data + ".qml")
            self.toUml.ui = self.logview

            self.thread = threading.Thread(target=my_function,
                                           args=(self.lsp, q, self.tofile,
                                                 None))
            self.thread.start()
            self.logview.focus()

    def action_callin(self) -> None:
        # if self.thread!=None:
        #     if self.thread.is_alive():
        #         self.logview.write_line("Wait for previous call finished")
        #         return
        def my_function(lsp, q: LspQuery, toFile, toUml):
            lsp.currentfile.call(q.data,
                                 once=False,
                                 uml=True,
                                 toFile=toFile,
                                 toUml=toUml)
            self.logview.write_line("Call Job finished")

        import threading
        sym = self.lsp.currentfile.symbols_list[self.symbol_listview.index]
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

            self.thread = threading.Thread(target=my_function,
                                           args=(self.lsp, q, self.tofile,
                                                 self.toUml))
            self.thread.start()
            self.logview.focus()

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree

    def __del__(self):
        self.lsp.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--root", help="root path")
    parser.add_argument("-f", "--file", help="root path")
    args = parser.parse_args()
    CodeBrowser(root=args.root, file=args.file).run()
