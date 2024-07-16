from textual.widgets import Label, ListItem, ListView, Tree

from lspcpp import task_call_in


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
    job: task_call_in

    def __init__(self) -> None:
        self.tree = Tree("call heritage")

    # mainui:uicallback
    def update_job(self, job: task_call_in):
        self.job = job
        root = self.tree.root.add(job.method.name, expand=True,data=job.method)
        for a in job.callin_all:
            root.add_leaf(a.displayname(),data=a)
