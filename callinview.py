from typing import Optional
from textual.app import App
from textual.message import Message
from textual.validation import Failure
from textual.widgets import Label, ListItem, ListView, Tree

from lspcpp import CallNode, task_call_in


class uicallback:

    def on_select_list(self, list: ListView):
        pass


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


CallTreeNodeExpand = 3
CallTreeNodeFocused = 2
CallTreeNodeCollapse = 1


class callinopen(Message):

    def __init__(self, node: CallNode) -> None:
        super().__init__()
        self.node = node


class CallTreeNode:
    callnode: CallNode

    def __init__(self, callnode: CallNode, expanded: bool) -> None:
        self.callnode = callnode
        self.focused = False
        pass


class _calltree(Tree, uicallback):
    BINDINGS = [
        ("enter", "open_file", "Open"),
    ]

    def __init__(self):
        Tree.__init__(self, "call heritage")

    def action_toggle_node(self):
        pass

    def action_enter(self):
        pass

    def action_select_cursor(self):
        try:
            self.__action_select_cursor()
        except:
            pass

    def __action_select_cursor(self):
        if self.cursor_node != None and self.cursor_node.data != None:
            n: CallTreeNode = self.cursor_node.data
            if n != None:
                open = n.focused == False
                if n.focused:
                    n.focused = False
                else:
                    n.focused = True
                if open:
                    self.app.post_message(callinopen(n.callnode))
                else:
                    if self.cursor_node.is_expanded:
                        cur = self.cursor_node
                        child = cur.children[0] if len(cur.children) else None
                        while child != None:
                            call = child.data
                            if call != None:
                                call.focused = False
                            child = child.children[0] if len(
                                child.children) else None

                    self.cursor_node.toggle_all()

    def __action_select_cursor_(self):
        if self.cursor_node != None and self.cursor_node.data != None:
            n: CallTreeNode = self.cursor_node.data
            if self.cursor_node.is_expanded:
                c = self.cursor_node
                child = None
                if c != None and len(c.children) > 0:
                    child = c.children[0]
                yes = None
                while child != None:
                    if child.is_expanded == False:
                        yes = child
                        break
                    if len(child.children) > 0:
                        child = child.children[0]
                    else:
                        break
                if yes != None:
                    yes.toggle_all()
                    return
                node: Optional[CallTreeNode] = c.data if c != None else None
                if node != None:
                    yes = node.focused
                    node.focused = node.focused == False
                    if yes == False:
                        self.app.post_message(callinopen(node.callnode))
                        return
                self.cursor_node.toggle_all()
                return
            self.cursor_node.toggle_all()
        pass


class callinview:
    job: task_call_in

    def __init__(self) -> None:
        self.tree = _calltree()

    # mainui:uicallback
    def update_job(self, job: task_call_in):
        self.job = job
        for child in self.tree.root.children:
            if child.data == job.displayname():
                child.remove()
                return
        root = self.tree.root.add(job.method.name,
                                  expand=True,
                                  data=job.displayname())
        for a in job.callin_all:
            node = root.add(a.displayname(),
                            data=CallTreeNode(a, False),
                            expand=False)
            a = a.callee
            while a != None:
                if a.callee is None:
                    node = node.add_leaf(a.displayname(),
                                         data=CallTreeNode(a, False))
                    break
                else:
                    node = node.add(a.displayname(),
                                    data=CallTreeNode(a, False))
                a = a.callee
