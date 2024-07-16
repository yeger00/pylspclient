from cpp_impl import to_file
from lspcpp import Symbol, SymbolLocation
from pylspclient.lsp_pydantic_strcuts import Location

class SourceCodeSearch(object):
    index = 0

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
        self.pattern = pattern
        with open(self.file, "r") as fp:
            index = 0
            for line in fp.readlines():
                pos = line.find(pattern)
                if pos > 1:
                    result = SourceCodeSearch.Pos(
                        index, pos, line[max(pos - 20, 0):min(pos + len(pattern)+20, len(line))])
                    result.text =result.text.replace(pattern,'''[b][u]%s[/u][/b]'''%(pattern)) 
                    ret.append(result)
                index = index + 1
        self.index = 0
        return ret

class SourceCode:
    #
    search: SourceCodeSearch

    def __init__(self, file) -> None:
        self.file = file
        self.search = SourceCodeSearch(file)
        pass
class ResultItem:

    def __init__(self) -> None:
        pass


class ResultItemRefer(ResultItem):
    item: SymbolLocation

    def __init__(self, item: SymbolLocation) -> None:
        super().__init__()
        self.item = item

    def __str__(self) -> str:
        return str(self.item)
    def loc(self) -> Location:
        return Location(uri=to_file(self.item.file), range=self.item.range)


class ResultItemString(ResultItem):

    def __init__(self, s) -> None:
        super().__init__()
        self.__str = s

    def __str__(self) -> str:
        return self.__str


class ResultItemSearch(ResultItem):
    item: SourceCodeSearch.Pos

    def __init__(self, item: SourceCodeSearch.Pos) -> None:
        super().__init__()
        self.item = item

    def __str__(self) -> str:
        return str(self.item)


class ResultItemSymbo(ResultItem):

    def __init__(self, s: Symbol) -> None:
        super().__init__()
        self.symbol = s


class SearchResults:
    data: list[ResultItem]
    status :str=""
    def get(self, i):
        try:
            return self.data[i]
        except:
            return None

    def result_number(self):
        return len(self.data)

    def is_empyt(self):
        return len(self.data) > 0

    def isType(self, Class):
        if len(self.data) == 0:
            return False
        index = 0
        return isinstance(self.data[index], Class)

    def on_select(self, index):
        self.index = index
        return self.data[index]

    def __init__(self, data: list[ResultItem] = []):
        self.data = data
        self.index = 0

    def search_prev(self) -> ResultItem:
        self.index -= 1
        if self.index < 0:
            self.index = len(self.data)-1
        return self.data[self.index]

    def search_next(self) -> ResultItem:
        self.index += 1
        if self.index > len(self.data)-1:
            self.index = 0
        return self.data[self.index]


