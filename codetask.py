class taskbase:
    def __init__(self) -> None:
        pass

    def run(self):
        pass



class TaskManager:
    tasklist: list[taskbase] = []

    def __init__(self) -> None:
        pass

    def add(self, task: taskbase) -> taskbase:
        self.tasklist.append(task)
        return task
