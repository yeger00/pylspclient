import os
from pathlib import Path


class code_search(object):

    class Pos:
        def __init__(self, line, col):
            self.line = line
            self.col = col

    def __init__(self, file, pattern) -> None:
        self.file = file
        self.pattern = pattern
        pass

    def search(self) -> list['code_search.Pos']:
        ret = []
        with open(self.file, "r") as fp:
            index = 0
            for line in fp.readline():
                pos = line.find(self.pattern)
                if pos > 1:
                    ret.append(code_search.Pos(line, pos))
                index = index + 1
        return ret
