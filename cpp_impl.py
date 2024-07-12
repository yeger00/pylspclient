from pylspclient.lsp_pydantic_strcuts import Location, Position, SymbolInformation
def from_file(path: str) -> str:
    return path.replace("file://", "").replace("file:", "")


def to_file(path: str) -> str:
    if path.startswith("file://"):
        return path
    return f"file://{path}"

def range_before(before: Position, after: Position):
    if before.line < after.line:
        return True
    elif before.line == after.line:
        return before.character <= after.character
    else:
        return False


def SubLine(begin, end, lines):
    subline = lines[begin.line:end.line+1]
    if begin.line == end.line:
        subline[0] = subline[0][begin.character:end.character+1]
    else:
        subline[0] = subline[0][begin.character:]
        subline[-1] = subline[-1][:end.character+1]
    return subline


class Body:
    subline: list[str] = []
    location: Location

    def __init__(self, location: Location) -> None:
        self.data = ""
        self.location = location
        range = location.range
        begin = range.start
        end = range.end
        with open(from_file(location.uri), "r") as fp:
            lines = fp.readlines()
            subline = SubLine(begin, end, lines)
            self.subline = subline

    def __str__(self) -> str:
        return "\n".join(self.subline)


class LspFuncParameter:
    lspsym: SymbolInformation

    def __init__(self, sym: SymbolInformation):
        self.lspsym = sym

    def parse(self) -> str:
        return ""

    def displayname(self):
        return str(self)


class LspFuncParameter_cpp(LspFuncParameter):
    def __init__(self, sym: SymbolInformation):
        super().__init__(sym)
        self.__data = ""
        self.parse()

    def parse(self):
        body = Body(self.lspsym.location)
        begin = None
        end = None
        for i in range(0, len(body.subline)):
            s = body.subline[i]
            if begin == None:
                p = s.find("(")
                if p >= 0:
                    begin = Position(line=i, character=p)
            if end == None:
                p = s.find(")")
                if p >= 0:
                    end = Position(line=i, character=p)
            if end != None and begin != None:
                break
        if begin == None or end == None:
            return ""
        if range_before(begin, end) == False:
            return ""
        self.param = " ".join(SubLine(begin, end, body.subline))

        def ss(s):
            return " ".join(filter(lambda x: len(x) > 0, s.split(" ")))
        self._displayname = ",".join(map(ss, self.param.split(","))).replace("\n","")
        return self.param

    def displayname(self):
        return self._displayname

    def __str__(self) -> str:
        return self.param
