from textual.widgets import Label, ListItem, ListView, Tree

from codetask import TaskCallIn
from lspcpp import CallNode


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


class callinview:
    job: TaskCallIn
    def __init__(self) -> None:
        self.tree = Tree("call heritage")
    # mainui:uicallback
    def update_job(self, job: TaskCallIn):
        self.job = job
        root = self.tree.root.add(job.name, expand=True)
        for a in job.job.callin_all:
            root.add_leaf(a.displayname())
