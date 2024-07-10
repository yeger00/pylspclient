"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import argparse
from logging import root
import sys

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.color import Lab
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, Static
from textual.widgets import Footer, Label, ListItem, ListView
from lspcpp import LspMain


class CodeBrowser(App):
    root: str

    def __init__(self, root, file):
        App.__init__(self)
        self.lsp = LspMain(root=root, file=file)
        self.root = root

    """Textual code browser app."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
    ]

    show_tree = var(True)

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

        self.a = ListView(ListItem(Label("xx")))
        yield self.a

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()
        aa = map(lambda x: ListItem(Label(x)),
                 self.lsp.currentfile.symbol_list_string())
        self.a.extend(aa)

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

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--root", help="root path")
    parser.add_argument("-f", "--file", help="root path")
    args = parser.parse_args()
    CodeBrowser(root=args.root, file=args.file).run()
