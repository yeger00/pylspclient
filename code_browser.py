"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

from textual import on
import argparse
from logging import root
import sys
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

    def __init__(self, name) -> None:
        self.data = name
        pass

    def __eq__(self, value: object) -> bool:
        return self.data == value.data

class CommandInput(Input):
    mainui:'CodeBrowser' 
    def on_input_submitted(self) -> None:
        if self.mainui!=None:
            self.mainui.on_command_input(self.value)
        pass
class CodeBrowser(App):
    root: str
    symbol_query = Query("")
    codeview_file: str

    def __init__(self, root, file):
        App.__init__(self)
        self.thread = None
        self.lsp = LspMain(root=root, file=file)
        self.root = root
        self.tofile = None
        self.toUml = None
        self.codeview_file = self.sub_title = file
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
    def changefile(self,file):
        self.lsp.changefile(file)
        self.refresh_symbol_view()
        self.logview.write_line("open %s"%(file))

    def on_command_input(self,value):
        args = value.split(" ")
        self.logview.write_line(value)
        if len(args)==1:
            if args[0]=="open":
                self.changefile(self.codeview_file) 
                return
        parser = argparse.ArgumentParser()
        parser.add_argument("-o", "--file", help="root path")
        parser.parse_args(args)
        if args.file!=None:
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
        self.symbol_listview = ListView(id="symbol-list")
        self.logview = Log(id="logview")
        yield self.logview
        yield self.symbol_listview
        v = CommandInput(placeholder="A number", type="text")
        v.mainui = self
        yield v

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        self.refresh_symbol_view()
        
    def refresh_symbol_view(self):
        aa = map(lambda x: ListItem(Label(x)),
                 self.lsp.currentfile.symbol_list_string())
        self.symbol_listview.clear()
        self.symbol_listview.extend(aa)
        self.logview.write_line("open %s"%(self.lsp.currentfile.file))

    def on_directory_tree_file_selected(
            self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
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
            self.sub_title = str(event.path)
            self.codeview_file = self.sub_title
            self.logview.write_line("tree open %s"%(self.sub_title))

    def action_open_file(self) -> None:
        if self.lsp.currentfile.file != self.codeview_file:
            self.changefile(self.codeview_file)

        pass

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
        q = Query(sym.symbol_display_name())
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--root", help="root path")
    parser.add_argument("-f", "--file", help="root path")
    args = parser.parse_args()
    CodeBrowser(root=args.root, file=args.file).run()
