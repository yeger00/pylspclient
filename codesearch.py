import os
from pathlib import Path


class SourceCodeSearch(object):

    class Pos:

        def __init__(self, line, col, text):
            self.line = line
            self.col = col
            self.text = text

        def __str__(self) -> str:
            return "%d:%d %s" % (self.line, self.col, self.text)

    def __init__(self, file) -> None:
        self.file = file
        self.pattern = ""
        pass

    def search(self, pattern) -> list['SourceCodeSearch.Pos']:
        ret = []
        self.pattern =pattern
        with open(self.file, "r") as fp:
            index = 0
            for line in fp.readlines():
                pos = line.find(pattern)
                if pos > 1:
                    result = SourceCodeSearch.Pos(
                        index, pos, line[pos - 10:pos + len(pattern)+10])
                    ret.append(result)
                index = index + 1
        return ret


class SourceCode:
    #
    search: SourceCodeSearch

    def __init__(self, file) -> None:
        self.file = file
        self.search = SourceCodeSearch(file)
        pass
