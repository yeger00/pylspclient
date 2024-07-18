from typing import Optional
from textual.message import Message
from codesearch import Symbol, SymbolLocation
from lspcpp import task_call_in
from pylspclient.lsp_pydantic_strcuts import Location
class log_message(Message):
    log: str = ""

    def __init__(self, log: str) -> None:
        super().__init__()
        self.log = log

class mymessage(Message):

    def __init__(self, s: list[str]) -> None:
        super().__init__()
        self.s = s


class changelspmessage(Message):
    loc: Optional[Location] = None

    def __init__(self,
                 file,
                 loc: Optional[Location] = None,
                 refresh=True) -> None:
        super().__init__()
        self.loc = loc
        self.file = file
        self.refresh_symbol_view = refresh

    pass


class symbolsmessage(Message):
    data = []
    file: str

    def __init__(self, data,  file: str) -> None:
        super().__init__()
        self.file = file
        self.data = data


class callin_message(Message):
    taskmsg: task_call_in.message

    def __init__(self, message: task_call_in.message) -> None:
        super().__init__()
        self.taskmsg = message


class refermessage(Message):
    s: list[SymbolLocation]
    query: str

    def __init__(self, s: list[SymbolLocation], key: str) -> None:
        super().__init__()
        self.query = key
        self.s = s

class message_get_symbol(Message):
    sym: Symbol

    def __init__(self, sym: Symbol) -> None:
        super().__init__()
        self.sym = sym






class message_get_symbol_callin(message_get_symbol):
    pass


class message_get_symbol_refer(message_get_symbol):
    pass
           
           
class message_line_change(Message):

    def __init__(self, line, file) -> None:
        super().__init__()
        self.line = line
        self.file = file 