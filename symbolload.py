from codesearch import Symbol


class symbolload:
    symbols_list: list[Symbol]
    file: str

    def __init__(self, symbols_list: list[Symbol], filepath: str) -> None:
        self.symbols_list = symbols_list
        self.filepath = filepath

    def need_refresh(self, file: str):
        if self.filepath != file: return True
        return len(self.symbols_list) == 0

