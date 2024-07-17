from typing import Optional
from textual.message import Message
from callinview import task_call_in
from codesearch import Symbol, SymbolLocation
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
    symbols_list: list[Symbol]

    def __init__(self, data, symbols_list: list[Symbol], file: str) -> None:
        super().__init__()
        self.file = file
        self.data = data
        self.symbols_list = symbols_list


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
