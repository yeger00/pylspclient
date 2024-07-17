from lspcpp import LspMain


class symbolload:
    file: str

    def __init__(self, filepath: str, lsp: LspMain) -> None:
        self.filepath = filepath
        self.lsp = lsp

    def symbols_list(self, file: str):
        if file != self.filepath:
            raise Exception("%s!=%s" % (file, self.filepath))
        a = self.lsp.find_symbol_file(self.filepath)
        return [] if a is None else a.symbols_list

    def need_refresh(self, file: str):
        return True if self.filepath != file else False
