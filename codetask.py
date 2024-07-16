from typing import Optional
from lspcpp import Output, TaskCallBack, callinjob



class TaskBase:
    def __init__(self) -> None:
        pass

    def run(self):
        pass


class TaskCallIn(TaskBase):
    def __init__(self, job: callinjob, cb: TaskCallBack) -> None:
        self.func = job
        self.cb = cb

    def run(self):
        self.func.run()


class TaskManager:
    tasklist: list[TaskBase] = []

    def __init__(self) -> None:
        pass

    def add(self, task: TaskBase) -> TaskBase:
        self.tasklist.append(task)
        return task
