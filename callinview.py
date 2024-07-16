from typing import Optional
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


class CallTreeNode:
    state: int

    def __init__(self, callnode: CallNode, expanded: bool) -> None:
        self.callnode = callnode
        self.state = CallTreeNodeExpand if expanded else CallTreeNodeCollapse
        self.focused = False
        pass


class _calltree(Tree,uicallback):
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
        if self.cursor_node != None and self.cursor_node.data != None:
            n: CallTreeNode = self.cursor_node.data
            if self.cursor_node.is_expanded:
                c = self.cursor_node
                child = None
                if c != None and len(c.children) > 0:
                    child = c.children[0]
                yes = None 
                while child != None:
                    if  child.is_expanded == False:
                        yes = child
                        break
                    if len(child.children) > 0:
                        child = child.children[0]
                    else:
                        break
                if yes!=None:
                    yes.toggle_all()
                    return
                node: Optional[CallTreeNode] = c.data if c != None else None
                if node != None :
                     yes = node.focused
                     node.focused = node.focused == False
                     if yes==False:
                         return
                self.cursor_node.toggle_all()
                return
            self.cursor_node.toggle_all()
            n.state = CallTreeNodeExpand if self.cursor_node.is_expanded else CallTreeNodeCollapse
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
