"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

from textual import on
import argparse
from logging import root
import sys
from textual.suggester import SuggestFromList
from textual.widgets import Log

from pydantic import NatsDsn
from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.color import Lab
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, Static
from textual.widgets import Footer, Label, ListItem, ListView
from lspcpp import LspMain, Output, lspcpp, OutputFile
from textual.app import App, ComposeResult
from textual.widgets import TextArea
from textual.widgets import Input


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


class Query:

    def __init__(self, name, type) -> None:
        self.data = name
        self.type = type
        pass

    def __eq__(self, value: object) -> bool:
        return self.data == value.data and self.type == value.type


class CommandInput(Input):
    mainui: 'CodeBrowser'

    def on_input_submitted(self) -> None:
        if self.mainui != None:
            self.mainui.on_command_input(self.value)
        pass


import re


class history:

    def __init__(self) -> None:
        self._data = set()
        self.list = list(self._data)
        pass

    def add(self, data):
        self._data.add(data)
        self.list = list(self._data)


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
            s: str = self.lines[event.y]
            file_paths = extract_file_paths(s)
            link = None
            for f in file_paths:
                pos = s.find(f)
                if event.x > pos and event.x < pos + len(f):
                    link = f
                    break
            self.mainuui.on_click_link(link)
        except:pass
        pass


SYMBOL_LISTVIEW_TYPE = 1
HISTORY_LISTVIEW_TYPE = 2


class MyListView(ListView):
    mainui: 'CodeBrowser'
    def action_select_cursor(self):
        self.mainui.on_select_list(self)


class CodeBrowser(App):
    root: str
    symbol_query = Query("", "")
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
        self.history.add(self.codeview_file)
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
            if self.symbol_listview_type == HISTORY_LISTVIEW_TYPE:
                self.on_choose_file_from_event(self.history.list[list.index])
            pass
        pass

    def on_click_link(self, link):
        self.on_choose_file_from_event(link)
        pass

    def changefile(self, file):
        self.lsp.changefile(file)
        self.refresh_symbol_view()
        self.logview.write_line("open %s" % (file))

    def on_command_input(self, value):
        args = value.split(" ")
        self.logview.write_line(value)
        if len(args) == 1:
            if args[0] == "open":
                self.changefile(self.codeview_file)
            elif args[0] == "history":
                self.refresh_history_view()
            elif args[0] == "symbol":
                self.refresh_symbol_view()
            return

        parser = argparse.ArgumentParser()
        parser.add_argument("-o", "--file", help="root path")
        parser.parse_args(args)
        if args.file != None:
            self.changefile(args.file)
            return

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
        yield Footer()
        # self.text = TextArea.code_editor("xxxx")
        # yield self.text
        self.symbol_listview = MyListView(id="symbol-list")
        self.symbol_listview.mainui= self
        self.logview = MyLogView(id="logview")
        self.logview.mainuui = self
        yield self.logview
        yield self.symbol_listview
        countries = ["history", "symbol", "open"]
        suggester = SuggestFromList(countries, case_sensitive=False)
        v = CommandInput(placeholder=" ".join(countries),
                         type="text",
                         suggester=suggester)
        v.mainui = self
        yield v

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        self.refresh_symbol_view()

    def refresh_history_view(self):
        self.symbol_listview_type = HISTORY_LISTVIEW_TYPE
        aa = map(lambda x: ListItem(Label(x)), list(self.history.list))
        self.symbol_listview.clear()
        self.symbol_listview.extend(aa)

    def refresh_symbol_view(self):
        self.symbol_listview_type = SYMBOL_LISTVIEW_TYPE
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
            self.history.add(self.codeview_file)
            if self.symbol_listview_type==HISTORY_LISTVIEW_TYPE:
                self.refresh_history_view()

    def action_open_file(self) -> None:
        if self.lsp.currentfile.file != self.codeview_file:
            self.changefile(self.codeview_file)

        pass

    def action_refer(self) -> None:
        # if self.thread!=None:
        #     if self.thread.is_alive():
        #         self.logview.write_line("Wait for previous call finished")
        #         return
        def my_function(lsp, q: Query, toFile, toUml):
            try:
                lsp.currentfile.refer(q.data, toFile=toFile)
            except Exception as e:
                self.logview.write_line(str(e))
                pass
            self.logview.write_line("Call Job finished")

        import threading
        sym = self.lsp.currentfile.symbols_list[self.symbol_listview.index]
        q = Query(sym.symbol_display_name(), "r")
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
        def my_function(lsp, q: Query, toFile, toUml):
            lsp.currentfile.call(q.data,
                                 once=False,
                                 uml=True,
                                 toFile=toFile,
                                 toUml=toUml)
            self.logview.write_line("Call Job finished")

        import threading
        sym = self.lsp.currentfile.symbols_list[self.symbol_listview.index]
        q = Query(sym.symbol_display_name(), "callin")
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
