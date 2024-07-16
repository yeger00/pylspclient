class history:
    datalist: list[str]

    def __init__(self, file=None) -> None:
        self._data = set()
        self.datalist = list(self._data)
        self.file = file
        if file != None:
            try:
                self.datalist = list(
                    map(lambda x: x.replace("\n", ""),
                        open(file, "r").readlines()))
                self._data = set(self.datalist)
            except:
                pass
        pass

    def add_to_history(self, data, barckforward=False):
        self._data.add(data)
        self.datalist = list(filter(lambda x: x != data, self.datalist))
        self.datalist.insert(0, data)
        if self.file != None:
            open(self.file, "w").write("\n".join(self.datalist))


class BackFoward:

    def __init__(self, h: history) -> None:
        self.history = h
        self.index = 0
        pass

    def goback(self) -> str:
        self.index += 1
        self.index = min(len(self.history.datalist) - 1, self.index)
        ret = self.history.datalist[self.index]
        return ret

    def goforward(self) -> str:
        self.index -= 1
        self.index = max(0, self.index)
        ret = self.history.datalist[self.index]
        return ret

