from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import files
from typing import Optional
from textual.message import Message
from textual.validation import Failure
from textual.widgets import Label, ListItem, ListView, Tree

from lspcpp import CallNode, task_call_in


class uicallback:

    def on_vi_command(self, value: str):
        pass

    def on_command_input(self, value):
        pass

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


class callinopen(Message):

    def __init__(self, node: object) -> None:
        super().__init__()
        self.node = node


class CallTreeNode:
    callnode: CallNode
    treenode_id: Optional[str] = None
    job_id: int

    def __init__(self, callnode: CallNode,
                 jobid: int) -> None:
        self.callnode = callnode
        self.focused = False
        self.job_id = jobid
        pass


class RootCallTreeNode(CallTreeNode):
    task: task_call_in
    nodecount: int = 0
    __subnode: set[int] = set()

    def __init__(self, task: task_call_in, jobid: int) -> None:
        self.task = task
        self.focused = False
        self.job_id = jobid
        self.nodecount = task.all_stacknode_cout()

    def add(self, node: CallNode):
        self.__subnode.add(node.id)


class _calltree(Tree, uicallback):
    BINDINGS = [
        ("r", "refer", "resolve"),
        ("a", "resolve_all", "resolve_all"),
    ]

    def action_resolve_all(self) -> None:
        try:
            for child in self.root.children:
                if child != self.cursor_node:
                    continue
                if child.data is None:
                    continue
                parent: Optional[RootCallTreeNode] = child.data if isinstance(
                    child.data, RootCallTreeNode) else None
                if parent is None:
                    continue
                task: task_call_in = parent.task
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
                parent: Optional[RootCallTreeNode] = child.data if isinstance(
                    child.data, RootCallTreeNode) else None
                if parent is None:
                    continue
                task: task_call_in = parent.task
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
    status: str = ""
    findresult = []
    index = 0
    
    tree_node_list={}

    def __init__(self) -> None:
        self.tree = _calltree()

    def goto_next(self):
        if len(self.findresult):
            self.index += 1
            self.index = self.index % len(self.findresult)
            self.tree.select_node(self.findresult[self.index])  # type: ignore

    def find_text(self, text):
        self.index = 0

        def find_node(node, key) -> list:
            if node is None:
                return []
            ret = []
            if str(node.label).lower().find(key) > -1:
                ret.append(node)
            if node.is_expanded:
                for c in node.children:
                    ret.extend(find_node(c, key))
            return ret

        self.findresult = find_node(self.tree.root, text)
        if len(self.findresult):
            self.tree.select_node(self.findresult[self.index])  # type: ignore

    def update_exists_node(self, job: task_call_in):
        for a in job.resolve_task_list:
            for stacknode in a.node.callstack():
                try:
                    node =self.tree_node_list[stacknode.id]
                    treenode = self.tree.get_node_by_id(
                        int(node.treenode_id))  # type: ignore
                    if treenode is None:
                        return False
                    s= stacknode.displayname()
                    if str(treenode.label) != s:
                        treenode.set_label(s)
                except Exception as e:
                    return False
        return True

    # mainui:uicallback
    def update_job(self, job: task_call_in):
        self.job = job
        jobid = job.id
        for child in self.tree.root.children:
            if child.data is None:
                continue
            if isinstance(child.data, RootCallTreeNode):
                c: RootCallTreeNode = child.data
                task: task_call_in = c.task
                if task.id == job.id:
                    if c.nodecount == job.all_stacknode_cout() and self.update_exists_node(job):
                        return
                    child.remove()
                    break
        root_call_tree = RootCallTreeNode(job, jobid=jobid)
        root = self.tree.root.add(
            job.method.name, expand=True, data=root_call_tree)
        root_call_tree.treenode_id = str(root.id)
        # self.tree_node_list.append(root_call_tree)
        for a in job.callin_all:
            level = 1
            node, a = self.add_node(root, a, jobid,root_call_tree)
            if node is None:
                break
            subroot = node 
            while a != None:
                level += 1
                node, a = self.add_node(node, a, jobid,root_call_tree)
            ss = subroot.label
            subroot.label = "%d %s" % (level, ss)

    def add_node(self, root_dom_node, callnode:Optional[CallNode], jobid:int,root:RootCallTreeNode):
        if callnode is None:
            return (None,None)
        data = CallTreeNode(callnode, jobid=jobid)
        if callnode.callee is None:
            root_dom_node = root_dom_node.add_leaf(callnode.displayname(), data=data)
        else:
            root_dom_node = root_dom_node.add(callnode.displayname(), data=data)
        root.add(callnode)
        data.treenode_id = str(root_dom_node.id)
        self.tree_node_list[callnode.id] = data
        return (root_dom_node if callnode != None else None, callnode.callee)
