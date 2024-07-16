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
CallTreeNodeFocus = 2
CallTreeNodeCollapse = 1


class CallTreeNode:
    state: int

    def __init__(self, callnode: CallNode, expanded: bool) -> None:
        self.callnode = callnode
        self.state = CallTreeNodeExpand if expanded else CallTreeNodeCollapse
        pass


class _calltree(Tree):
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
        if self.cursor_node != None and self.cursor_node.data!=None:
            n:CallTreeNode = self.cursor_node.data
            if self.cursor_node.is_expanded :
                if n.state != CallTreeNodeExpand:
                    n.state = CallTreeNodeExpand
                    return
            else:
                if n.state != CallTreeNodeCollapse:
                    n.state = CallTreeNodeCollapse
                    return

            if n.state==CallTreeNodeCollapse:
                n.state = CallTreeNodeFocus
                return
            elif n.state==CallTreeNodeFocus:
                n.state = CallTreeNodeExpand
            else :
                n.state = CallTreeNodeCollapse
            self.cursor_node.toggle_all()
        pass


class callinview:
    job: task_call_in

    def __init__(self) -> None:
        self.tree = _calltree()

    # mainui:uicallback
    def update_job(self, job: task_call_in):
        self.job = job
        for a in self.tree.children:
            a.remove()
        root = self.tree.root.add(job.method.name,
                                  expand=True,
                                  data=job.method)
        for a in job.callin_all:
            node = root.add(a.displayname(),
                            data=CallTreeNode(a, True),
                            expand=True)
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
