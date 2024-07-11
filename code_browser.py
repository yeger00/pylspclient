"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

from concurrent.futures import ThreadPoolExecutor
import os
import re
import asyncio
import threading
from textual import on
import argparse
from textual.message_pump import events
from textual.suggester import SuggestFromList, SuggestionReady
from textual.validation import Failure
from textual.widgets import Log

from pydantic import Field, NatsDsn
from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.color import Lab
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, Static
from textual.widgets import Footer, Label, ListItem, ListView
from lspcpp import LspMain, Symbol, OutputFile
from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.widgets import Footer, Label, TabbedContent, TabPane

input_command_options = [
    "history", "symbol", "open", "find", "refer", "callin", "ctrl-c", "copy",
    "save", "log", "quit", "grep"
]


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
        self.db = build_dirs(root)
        pass

    def find(self, pattern):
        try:
            if self.db[pattern]:
                return str(pattern)[1:]
        except:
            keys = list(filter(lambda x: x.startswith(pattern),
                               self.db.keys()))
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

    def __init__(self, dir, pattern) -> None:
        self.dir = dir
        self.pattern = pattern
        self.ret = []
        pass

    def match_pattern(self, path):
        for p in self.pattern:
            if path.find(p) == -1:
                return False
        return True

    def get(self):
        files_found = []
        if self.dir is None: return files_found
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                p = os.path.join(root, file)
                if self.match_pattern(p):
                    files_found.append(p)
        return files_found

    @staticmethod
    def run(dir, pattern, cb):
        fileset = ["h", "cc", "cpp"]

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

        normalized_value = value if self.case_sensitive else value.casefold()
        if self.cache is None or normalized_value not in self.cache:
            suggestion = await self.get_suggestion(normalized_value)
            if self.cache is not None:
                self.cache[normalized_value] = suggestion
        else:
            suggestion = self.cache[normalized_value]

        if suggestion is None:
            suggestion = self.complete_path(value)
        if suggestion is None:
            ret = list(
                filter(lambda x: x.startswith(value), self._history._data))
            if len(ret) > 0:
                suggestion = ret[0]
        if suggestion is None:
            return
        requester.post_message(SuggestionReady(value, suggestion))

    def complete_path(self, value: str):
        try:
            # if self.root is None: return None
            if value.startswith(find_key) == False:
                return None
            args = convert_command_args(value)
            if self.dircomplete != None:
                if len(args) == 2 and len(args[1]) > 1:
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
    def _on_list_item__child_clicked(self, event: ListItem._ChildClicked) -> None:
        ListView._on_list_item__child_clicked(self, event)
        self.mainui.on_select_list(self)
    def action_select_cursor(self):
        self.mainui.on_select_list(self)


class CodeBrowser(App):
    root: str
    symbol_query = LspQuery("", "")
    codeview_file: str

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
        ("c", "callin", "CallIn"),
        ("o", "open_file", "Open"),
        ("r", "refer", "Reference"),
    ]

    show_tree = var(True)

    def on_select_list(self, list: ListView):
        if list == self.symbol_listview:
            if self.history_view == list:
                self.on_choose_file_from_event(self.history.list[list.index])
            elif self.symbol_listview == list:
                try:
                    sym: Symbol = self.lsp.currentfile.symbols_list[list.index]
                    y = sym.sym.location.range.start.line
                    self.query_one("#code-view").scroll_to(y=y, animate=False)
                    pass
                except Exception as e:
                    self.logview.write_line(str(e))
            pass
        pass

    def on_click_link(self, link, line=None):
        self.on_choose_file_from_event(link)
        if line != None:
            self.query_one("#code-view").scroll_to(y=line, animate=False)
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
        except:
            pass
        self.did_command_cmdline(args)

    def did_command_opt(self, value, args):
        self.logview.write_line(value)
        if len(args) > 0:
            if args[0] == "open":
                self.change_lsp_file(self.codeview_file)
            elif args[0] == "find":
                dir = args[1]
                if self.root.find(dir) == -1:
                    dir = self.root + dir
                    dir = os.path.realpath(dir)

                logui = self.logview

                def cb(s):
                    try:
                        logui.write_line("find files %d" % (len(s)))
                        logui.write_lines(s)
                    except Exception as e:
                        pass

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
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
            with TabbedContent(initial="jessica", id="symbol-list"):
                with TabPane("Rencently", id="leto"):  # First tab
                    self.history_view = MyListView(id="symbol-listx")
                    self.history_view.mainui = self
                    yield self.history_view
                with TabPane("Symbol", id="jessica"):
                    self.symbol_listview = MyListView(id="symbol-listx")
                    self.symbol_listview.mainui = self
                    yield self.symbol_listview
        yield Footer()
        # self.text = TextArea.code_editor("xxxx")
        # yield self.text
        self.logview = MyLogView(id="logview")
        self.logview.mainuui = self
        yield self.logview
        v = CommandInput(self, root=self.lsp.root)
        yield v

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        self.on_choose_file_from_event(self.codeview_file)
        self.change_lsp_file(self.codeview_file)
        self.refresh_symbol_view()

    def refresh_history_view(self):
        aa = map(lambda x: ListItem(Label(os.path.basename(x))), list(self.history.list))
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

    def on_choose_file_from_event(self, path):
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
            self.query_one("#code-view").scroll_home(animate=False)
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
