from concurrent.futures import ThreadPoolExecutor
from math import exp
from re import sub
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

    def __init__(self, node: object) -> None:
        super().__init__()
        self.node = node


class CallTreeNode:
    callnode: Optional[CallNode | task_call_in]

    def __init__(self, callnode:        Optional[CallNode | task_call_in], expanded: bool) -> None:
        self.callnode = callnode
        self.focused = False
        pass


class _calltree(Tree, uicallback):
    BINDINGS = [
        ("r", "refer", "resolve"),
        ("a", "resolve_all", "resolve_all"),
    ]
    def action_resolve_all(self)->None:
        try:
            for child in self.root.children:
                if child!=self.cursor_node:
                    continue
                if child.data is None:
                    continue
                parent: CallTreeNode = child.data
                if parent is None or isinstance(parent.callnode, task_call_in) == False:
                    continue
                task: task_call_in = parent.callnode  # type: ignore
                ThreadPoolExecutor(1).submit(task.deep_resolve)
                return
        except:
            pass
        pass
    def action_refer(self) -> None:
        try:
            for child in self.root.children:
                if child.data is None:
                    continue
                parent: CallTreeNode = child.data
                if parent is None or isinstance(parent.callnode, task_call_in) == False:
                    continue
                task: task_call_in = parent.callnode  # type: ignore
                index = child.children.index(self.cursor_node)  # type: ignore
                if index >= 0:
                    aa = child.children[index]
                    if aa.data != None:
                        def fn(task, index):
                            task.deep_resolve_at(index)
                        ThreadPoolExecutor(1).submit(fn, task, index)
                    break

        except:
            pass
        pass

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


class callinview:
    job: task_call_in

    def __init__(self) -> None:
        self.tree = _calltree()

    # mainui:uicallback
    def update_job(self, job: task_call_in):
        self.job = job
        for child in self.tree.root.children:
            if child.data is None:
                continue
            c: CallTreeNode = child.data
            if isinstance(c.callnode, task_call_in):
                task: task_call_in = c.callnode
                if task.id == job.id:
                    child.remove()
                    break
        root = self.tree.root.add(job.method.name,
                                  expand=True,
                                  data=CallTreeNode(job, True))
        for a in job.callin_all:
            level = 1
            subroot = node = root.add(a.displayname(),
                                      data=CallTreeNode(a, False),
                                      expand=False)
            a = a.callee
            while a != None:
                level += 1
                if a.callee is None:
                    node = node.add_leaf(a.displayname(),
                                         data=CallTreeNode(a, False))
                    break
                else:
                    node = node.add(a.displayname(),
                                    data=CallTreeNode(a, False))
                a = a.callee
            ss = subroot.label
            subroot.label = "%d %s" % (level, ss)
