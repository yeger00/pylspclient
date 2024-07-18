from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from textual.message import Message
from textual.widgets import Tree
from baseview import uicallback
from codesearch import to_file
from codeview import code_message_decl
from event import log_message, message_open_file
from lspcpp import CallNode, Position, Range, task_call_in


class callinopen(Message):

    def __init__(self, node: object) -> None:
        super().__init__()
        self.node = node


class CallTreeNode:
    callnode: CallNode
    treenode_id: Optional[str] = None
    firstcall = False

    # job_id: int

    def __init__(self, callnode: CallNode, jobid: int = 0) -> None:
        self.callnode = callnode
        self.focused = False
        # self.job_id = jobid
        pass


class RootCallTreeNode(CallTreeNode):
    task: task_call_in
    nodecount: int = 0
    __subnode: set[int] = set()

    def __init__(self, task: task_call_in, jobid: int) -> None:
        self.task = task
        self.focused = False
        # self.job_id = jobid
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
            self.__action_select_cursor_1()
        except:
            pass

    def __action_select_cursor_1(self):
        if self.cursor_node != None and self.cursor_node.data != None:
            n: CallTreeNode = self.cursor_node.data
            if n != None:
                open = False
                if n.firstcall == False:
                    open = True
                else:
                    open = n.focused == False
                    n.focused = open
                if open:
                    self.app.post_message(callinopen(n.callnode))
                else:
                    self.cursor_node.toggle_all()

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

    call_tree_node_list = {}

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

    def update_exists_node_(self, msg: task_call_in.message):
        try:
            return self.__update_exists_node_setlabel(msg)
        except:
            return False

    def __update_exists_node_setlabel(self, message: task_call_in.message):
        if message.node != None:
            call_tree_node = self.call_tree_node_list[message.node.id]
            if call_tree_node != None:
                stacks = message.node.callstack()
                for stacknode in stacks:
                    call_tree_node = self.call_tree_node_list[stacknode.id]
                    treenode = self.tree.get_node_by_id(
                        int(call_tree_node.treenode_id))  # type: ignore
                    treenode.set_label(stacknode.displayname())
                    self.tree.post_message(log_message(str(treenode.label)))
                root = self.call_tree_node_list[message.node.id]
                root.set_label("%d %s" %
                               (len(stacks), message.node.displayname()))
        return True

    def __update_exists_node_(self, message: task_call_in.message):
        if message.node != None:
            call_tree_node = self.call_tree_node_list[message.node.id]
            # call_tree_node:CallTreeNode=self.tree_node_list[stacknode.id]
            if call_tree_node != None:
                root = treenode = self.tree.get_node_by_id(
                    int(call_tree_node.treenode_id))  # type: ignore
                treenode.remove_children()
                a = call_tree_node.callnode
                a = a.callee
                cout = 1
                while a != None:
                    self.tree.post_message(
                        log_message("displayname:" + a.displayname()))
                    treenode, a = self.add_node(treenode, a)
                    if treenode == None:
                        continue
                    cout += 1
                    self.tree.post_message(log_message(str(treenode.label)))
                    # print(" "*cout, treenode.label)
                root.set_label("%d %s" % (cout, message.node.displayname()))
        return True

    #     return True
    def remove_callnode_list(self, a):
        i = 0
        if a.data != None:
            if isinstance(a.data, CallNode):
                try:
                    n: CallNode = a.data
                    self.call_tree_node_list.pop(n.id)
                    i += 1
                except:
                    pass
        for a in a.children:
            i += self.remove_callnode_list(a)
        return i

    # mainui:uicallback
    def update_job(self, message: task_call_in.message):
        job = message.task
        self.job = job
        jobid = job.id
        for child in self.tree.root.children:
            if child.data is None:
                continue
            if isinstance(child.data, RootCallTreeNode):
                c: RootCallTreeNode = child.data
                task: task_call_in = c.task
                if task.id == job.id:
                    if c.nodecount == job.all_stacknode_cout():
                        if self.update_exists_node_(message):
                            return
                        # yes,ret = self.update_exists_node(job) # type: ignore
                        # if yes:
                        #     for a in ret:
                        #         a.refresh()
                        #     return
                    self.remove_callnode_list(child)
                    child.remove()
                    break
        root_call_tree = RootCallTreeNode(job, jobid=jobid)
        root = self.tree.root.add(job.method.name,
                                  expand=True,
                                  data=root_call_tree)
        root_call_tree.treenode_id = str(root.id)
        # self.tree_node_list.append(root_call_tree)
        for a in job.callin_all:
            level = 1
            node, a = self.add_node(root, a)
            if node != None and node.data != None:
                top: CallTreeNode = node.data
                top.firstcall = True
            if node is None:
                break
            subroot = node
            while a != None:
                level += 1
                node, a = self.add_node(node, a)
            ss = subroot.label
            subroot.label = "%d %s" % (level, ss)

    def add_node(self, root_dom_node, callnode: Optional[CallNode]):
        if callnode is None:
            return (None, None)
        data = CallTreeNode(callnode)
        if callnode.callee is None:
            root_dom_node = root_dom_node.add_leaf(callnode.displayname(),
                                                   data=data)
        else:
            root_dom_node = root_dom_node.add(callnode.displayname(),
                                              data=data)
        data.treenode_id = str(root_dom_node.id)
        self.call_tree_node_list[callnode.id] = data
        return (root_dom_node if callnode != None else None, callnode.callee)
class filenode:

    def __init__(self, file) -> None:
        self.file = file
        self.name = os.path.basename(file)


class plumresult:
    name: str
    files: list[filenode] = []

    def __init__(self, name) -> None:
        self.name = os.path.basename(name)
        pass

import os
def find_seq() -> list[plumresult]:
    root = os.path.join(os.path.dirname(__file__), "export")
    dirs = os.listdir(root)

    ret = []
    for dir in dirs:
        dir = os.path.join(root, dir)
        if os.path.isdir(dir) == False:
            continue
        b = plumresult(dir)
        for a in os.listdir(dir):
            if a.endswith(".utxt"):
                b.files.append(filenode(os.path.join(dir, a)))
        if len(b.files):
            ret.append(b)
    return ret


class ResultTree(Tree):

    def __init__(self):
        Tree.__init__(self, id="sequence-tree", label="sequence")

    def update(self):
        ret = find_seq()
        self.root.expand()
        self.root.remove_children()
        for a in ret:
            root = self.root.add(a.name)
            for b in a.files:
                root.add_leaf(b.name, data=b)

    def action_select_cursor(self):
        if self.cursor_node is None: return
        if self.cursor_node.data is None:
            return
        if isinstance(self.cursor_node.data, filenode):
            self.post_message(message_open_file(self.cursor_node.data.file))
