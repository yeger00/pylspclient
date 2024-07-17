from collections.abc import Iterable
from common import Body, SubLine, range_before
from pylspclient.lsp_pydantic_strcuts import Location, Position, SymbolInformation
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
        subline :list[str]= SubLine(begin, end, body.subline)
        subline[0]=subline[0][1:]
        subline[-1]=subline[-1][:-1]
        self.param = " ".join(subline)
    
        def justtype(s):
            sss = list(filter(lambda x: len(x) > 0, s.split(" ")))
            return " ".join(sss[:-1])
        def ss(s):
            return " ".join(filter(lambda x: len(x) > 0, s.split(" ")))
        d  = ",".join(map(justtype, self.param.split(","))).replace("\n","")
        self._displayname = "(%s)"%(d)
        return self.param

    def displayname(self):
        return self._displayname

    def __str__(self) -> str:
        return self.param
