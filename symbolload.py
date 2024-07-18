from functools import update_wrapper
from logging import root
import re
from typing import Optional
from textual.geometry import Region
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.text_area import Selection
from baseview import MyListView
from callinview import log_message
from codesearch import Symbol
from codeview import CodeView
from common import from_file
from lspcpp import LspMain, SymbolFile, SymbolKind


class symbolload:
    file: str

    def __init__(self, filepath: str, lsp: LspMain) -> None:
        self.filepath = filepath
        self.lsp = lsp

    def symbols_list(self, file: str):
        if file != self.filepath:
            raise Exception("%s!=%s" % (file, self.filepath))
        a = self.lsp.find_symbol_file(self.filepath)
        return [] if a is None else a.symbols_list

    def need_refresh(self, file: str):
        return True if self.filepath != file else False


class symbol_tree_update(Message):
    symfile: Optional[SymbolFile]

    def __init__(self, symfile: Optional[SymbolFile]) -> None:
        super().__init__()
        self.symfile = symfile


class message_line_change(Message):

    def __init__(self, line, file) -> None:
        super().__init__()
        self.line = line
        self.file = file


class message_get_symbol(Message):
    sym: Symbol

    def __init__(self, sym: Symbol) -> None:
        super().__init__()
        self.sym = sym


class message_get_symbol_impl(message_get_symbol):
    pass


class message_get_symbol_declare(message_get_symbol):
    pass


class message_get_symbol_callin(message_get_symbol):
    pass


class message_get_symbol_refer(message_get_symbol):
    pass


action_refer = 1
action_callin = 2
action_declare = 3
action_define = 4
action_impl = 5


class _symbol_tree_view(Tree):
    BINDINGS = [
        ("r", "refer", "Reference"),
        ("c", "call", "Call in"),
        ("d", "go_declare", "Go to declare"),
        ("D", "go_impl", "Go to Define"),
    ]
    nodemap = {}

    def search_word(self, key):

        def find(root, key):
            ret = []
            if root.data != None:
                if isinstance(root.data, Symbol):
                    s: Symbol = root.data
                    if s.name.lower().find(key) > -1:
                        ret.append(root.id)
            for a in root.children:
                ret.extend(find(a, key))
            return ret

        if len(key) == 0:
            return []
        return find(self.root, key)

    def action_go_impl(self) -> None:
        try:
            self.get_refer_for_symbol_list(action_impl)
        except Exception as e:
            self.post_message(log_message("exception %s" % (str(e))))
            pass

    def action_go_declare(self) -> None:
        try:
            self.get_refer_for_symbol_list(action_declare)
        except Exception as e:
            self.post_message(log_message("exception %s" % (str(e))))
            pass

    def add(self, node, sym: Symbol):
        self.nodemap[node.id] = sym

    def goto_selection(self, selection: CodeView.Selection):
        row = selection.range.start.line
        max = None
        key = None
        for k in self.nodemap:
            sym: Symbol = self.nodemap[k]
            gap = abs(sym.sym.location.range.start.line - row)
            if max is None or max > gap:
                max = gap
                key = k
        if key != None:
            try:
                node = self.get_node_by_id(key)  # type: ignore
                if node == self.cursor_node:
                    return
                self.cursor_line = node.line
                if node.parent != None:
                    node.parent.expand_all()

                self.goto_node(node)
            except Exception as e:
                self.post_message(log_message("exception %s" % (str(e))))
        pass

    def goto_node(self, node):
        region = self._get_label_region(node._line)
        if region is not None:
            r = Region(0, region.y, region.width, region.height)
            self.scroll_to_region(r, animate=False, force=True)

    def goto(self, id: int):
        try:
            self.root.expand_all()
            node = self.get_node_by_id(id)  # type: ignore
            self.cursor_line = node.line
            self.goto_node(node)
        except Exception as e:
            self.post_message(log_message("exception %s" % (str(e))))
        pass

    def get_refer_for_symbol_list(self, action: int):
        root = self.cursor_node
        if root is None:
            return
        sym: Optional[Symbol] = root.data
        if sym is None:
            return
        if action == action_refer:
            self.post_message(message_get_symbol_refer(sym))
        elif action == action_callin:
            self.post_message(message_get_symbol_callin(sym))
        elif action == action_declare:
            self.post_message(message_get_symbol_declare(sym))
        elif action == action_impl:
            self.post_message(message_get_symbol_impl(sym))

    def action_call(self) -> None:
        try:
            self.get_refer_for_symbol_list(action_callin)
        except Exception as e:
            self.post_message(log_message("exception %s" % (str(e))))
            pass

    def action_refer(self) -> None:
        try:
            self.get_refer_for_symbol_list(action_refer)
        except Exception as e:
            self.post_message(log_message("exception %s" % (str(e))))
            pass

    def __init__(self):
        Tree.__init__(self, "", id="symbol-tree")

    def on_symbol_tree_update(self, message: symbol_tree_update):
        if message.symfile is None:
            self.root.remove_children()
            self.loading = True
            self.nodemap = []
            return
        else:
            self.loading = False
            self.set_data(message.symfile)

        pass

    def set_data(self, data: SymbolFile):
        self.nodemap = {}
        symbols = data.get_class_symbol_list()
        root = self.root
        root.remove_children()
        for a in symbols:
            if len(a.members):
                n = root.add(a.symbol_sidebar_displayname(False),
                             data=a,
                             expand=False)
                self.add(n, a)
                self.add_child(n, a)

            else:
                root.add_leaf(a.symbol_sidebar_displayname(False), data=a)
            pass
        root.expand()

    def add_child(self, root, sym: Symbol):
        if len(sym.members):
            for a in sym.members:
                n = root.add_leaf(a.symbol_sidebar_displayname(False), data=a)
                self.add(n, a)

    def action_select_cursor(self):
        root = self.cursor_node
        if root is None:
            return
        sym: Optional[Symbol] = root.data
        if sym is None:
            return
        loc = sym.sym.location
        self.post_message(
            message_line_change(loc.range.start.line, file=from_file(loc.uri)))
        pass
