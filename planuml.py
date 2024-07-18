import os
from posix import listdir

from textual.widgets import Tree

from common import where_is_bin


class planmuml_bin:

    def __init__(self) -> None:
        self.jarpath = os.path.join(os.path.dirname(__file__),
                                    "plantuml-1.2024.6.jar")
        self.java = where_is_bin("java")
        pass

    def conver(self, uml, ouput):
        if os.path.exists(self.jarpath) == False:
            raise Exception("Exception jar not found")
        if self.java is None or os.path.exists(self.java) == False:
            raise Exception("Exception java not found")
        os.system("%s -jar %s %s " % (self.java, self.jarpath, uml))
        os.system("%s -jar %s %s -utxt" % (self.java, self.jarpath, uml))


plamuml_jar = planmuml_bin()


def planuml_to_image(file, output):
    plamuml_jar.conver(file, output)


class filenode:

    def __init__(self, file) -> None:
        self.file = file
        self.name = os.path.basename(file)


class plumresult:
    name: str
    files: list[filenode] = []

    def __init__(self, name) -> None:
        self.name = name
        pass


def find_seq() -> list[plumresult]:
    root = os.path.join(os.path.dirname(__file__), "export")
    dirs = os.listdir(root)

    ret = []
    for dir in dirs:
        b = plumresult(dir)
        dir = os.path.join(root, dir)
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
        self.root.remove_children()
        for a in ret:
            root = self.root.add(a.name)
            for b in a.files:
                root.add_leaf(b.name, data=b)
