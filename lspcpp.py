import subprocess
import json

from pydantic import BaseModel
import pylspclient
import threading
from os import path
from pylspclient import LspClient, LspEndpoint
from pylspclient.lsp_pydantic_strcuts import DocumentSymbol, TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext, SymbolInformation, ReferenceParams, TextDocumentPositionParams, SymbolKind, ReferenceContext, Location

DEFAULT_CAPABILITIES = {
    'textDocument': {
        'completion': {
            'completionItem': {
                'commitCharactersSupport': True,
                'documentationFormat': ['markdown', 'plaintext'],
                'snippetSupport': True
            }
        }
    }
}


class PrepareReturn(BaseModel):
    data: str
    kind: SymbolKind
    range: Range
    selectionRange: Range
    uri: str
    name: str

    @staticmethod
    def create(data: dict, sym: SymbolInformation):
        ret = PrepareReturn(range=Range.parse_obj(data["range"]),
                            selectionRange=Range.parse_obj(
                                data["selectionRange"]),
                            kind=SymbolKind(data["kind"]),
                            data=data["data"],
                            uri=sym.location.uri,
                            name=sym.name)
        return ret

    def in_range(self, sym: SymbolInformation):
        if sym.location.uri != self.uri:
            return False
        if sym.kind != self.kind:
            return False
        if self.range.start.line != sym.location.range.start.line:
            return False
        if sym.name != self.name:
            return False
        return True


class Symbol:
    sym: SymbolInformation
    members: list['Symbol']

    def __init__(self, sym: SymbolInformation) -> None:
        self.sym = sym
        self.members = []
        self.cls = None

    def find(self, node: 'CallNode'):
        if node.sym.in_range(self.sym):
            return self
        for a in self.members:
            yes = node.sym.in_range(a.sym)
            if yes:
                return a
        return None

    def __str__(self) -> str:
        cls = self.cls.sym.name + "::" if self.cls != None else ""
        return cls + self.sym.name + " %s::%d" % (from_file(
            self.sym.location.uri), self.sym.location.range.start.line)

    def is_call(self):
        return self.sym.kind == SymbolKind.Method or self.sym.kind == SymbolKind.Function

    def is_method(self):
        return self.sym.kind == SymbolKind.Method

    def find_members(self, syms: list[SymbolInformation]):
        yes = self.sym.kind == SymbolKind.Class or self.sym.kind == SymbolKind.Struct
        if yes == False:
            return syms
        while len(syms):
            s = syms[0]
            if s.kind == SymbolKind.Method or s.kind == SymbolKind.Constructor:
                s1 = Symbol(s)
                s1.cls = self
                self.members.append(s1)
                syms = syms[1:]
            elif s.kind == SymbolKind.Field:
                s1 = Symbol(s)
                self.members.append(s1)
                self.cls = self
                syms = s1.find_members(syms[1:])
            else:
                return syms
        return syms


class ReadPipe(threading.Thread):

    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            # print('pipe:', line)
            line = self.pipe.readline().decode('utf-8')


def from_file(path: str) -> str:
    return path.replace("file://", "").replace("file:", "")


def to_file(path: str) -> str:
    if path.startswith("file://"):
        return path
    return f"file://{path}"


class CallHierarchyItem(BaseModel):
    name: str
    kind: SymbolKind
    range: Range
    uri: TextDocumentIdentifier
    selectionRange: Range

    def setvalue(self, sym: SymbolInformation):
        self.name = sym.name
        self.kind = sym.kind
        self.uri = TextDocumentIdentifier(uri=sym.location.uri)
        self.range = sym.location.range

        self.range.end = self.range.start
        self.range.end.character = self.range.start.character + len(self.name)
        self.range.end.character = self.range.start.character + len(self.name)
        self.selectionRange = self.range


class SymbolParser:
    symbol_col: int = -1
    location: Location

    def __init__(self, sym: SymbolInformation):
        self.name = sym.name
        self.location = sym.location
        self.kind = sym.kind
        self.symbol_line = self.location.range.start.line
        with open(from_file(self.location.uri), "r") as fp:
            lines = fp.readlines()
            line = lines[self.location.range.start.line]
            self.symbol_col = line[self.location.range.start.character:].index(
                self.name) + self.location.range.start.character


class LspClient2(LspClient):
    endpoint: LspEndpoint

    def __init__(self, lsp_endpoint: LspEndpoint):
        """

        Args:
            lsp_endpoint:
        """
        LspClient.__init__(self, lsp_endpoint)
        self.endpoint = lsp_endpoint

    def callIncomingTree(self, param: PrepareReturn):
        for a in self.callIncoming(param):
            print(a.name)
            self.callIncomingTree(a)

    def callIncoming(self, param: PrepareReturn) -> list[PrepareReturn]:
        sss = dict(param)
        ret = self.endpoint.call_method("callHierarchy/incomingCalls",
                                        item=sss)

        def convert(s):
            try:
                from_ = s["from"]
                return PrepareReturn(data=from_["data"],
                                     kind=from_["kind"],
                                     range=Range.parse_obj(from_["range"]),
                                     selectionRange=Range.parse_obj(
                                         from_["selectionRange"]),
                                     uri=from_["uri"],
                                     name=from_["name"])
            except Exception as e:
                print(e)
                return None

        return list(filter(lambda x: x != None, map(convert, ret)))

    def callHierarchyPrepare(self, sym: SymbolInformation):
        s = SymbolParser(sym)
        col = s.symbol_col
        line = s.symbol_line
        ret = self.endpoint.call_method(
            "textDocument/prepareCallHierarchy",
            textDocument=TextDocumentIdentifier(uri=sym.location.uri),
            position={
                "character": col,
                "line": line
            })
        ret = list(map(lambda x: PrepareReturn.create(x, sym), ret))
        return ret

    def call_hierarchy_incoming_calls(self):
        self.endpoint.call_method("callHierarchy/incomingCalls")

    def references(self, file, col: int, line: int) -> list[Location]:

        def convert(s):
            try:
                return Location.parse_obj(s)
            except:
                return None

        ret = self.endpoint.call_method(
            'textDocument/references',
            textDocument=TextDocumentIdentifier(uri=to_file(file)),
            context={"includeDeclaration": True},
            position={
                "character": col,
                "line": line
            })
        return list(
            filter(lambda x: x != None and x.range.start.line != line,
                   map(convert, ret)))


class project_config:
    data_path: None | str
    DEFAULT_ROOT: None | str

    def __init__(self) -> None:
        self.DEFAULT_ROOT = None
        self.data_path = None


class lspcppclient:
    lsp_client: LspClient2

    def __init__(self, config: project_config,
                 json_rpc_endpoint: pylspclient.JsonRpcEndpoint) -> None:
        lsp_endpoint = LspEndpoint(json_rpc_endpoint)
        lsp_client = LspClient2(lsp_endpoint)
        process_id = None
        root_path = None
        assert (config.DEFAULT_ROOT != None)
        root_uri = to_file(config.DEFAULT_ROOT)
        data_path = config.data_path
        initialization_options = {
            "compilationDatabasePath": data_path
        } if data_path != None else None
        capabilities = {
            'textDocument': {
                'completion': {
                    'completionItem': {
                        'commitCharactersSupport': True,
                        'snippetSupport': True
                    }
                }
            }
        }

        trace = "off"
        workspace_folders = None
        initialize_response = lsp_client.initialize(process_id, root_path,
                                                    root_uri,
                                                    initialization_options,
                                                    capabilities, trace,
                                                    workspace_folders)
        print(json.dumps(initialize_response, indent=4))
        if initialize_response['serverInfo']['name'] != 'clangd':
            raise RuntimeError("failed to initialize lsp_client")
        lsp_client.initialized()
        self.lsp_client = lsp_client
        pass

    def close(self):
        self.lsp_client.exit()

    def get_class_symbol(self, file) -> list[Symbol]:
        ret = []
        symbols = self.get_document_symbol(file)
        while len(symbols):
            s = symbols[0]
            if s.kind == SymbolKind.Class or s.kind == SymbolKind.Struct:
                s1 = Symbol(s)
                symbols = s1.find_members(symbols[1:])
                ret.append(s1)
            else:
                s1 = Symbol(s)
                ret.append(s1)
                symbols = symbols[1:]
        return ret

    def get_document_symbol(self, file: str) -> list[SymbolInformation]:
        x = TextDocumentIdentifier(uri=to_file(file))
        symbol = self.lsp_client.documentSymbol(x)
        return symbol

    def get_symbol_reference(self,
                             symbol: SymbolInformation) -> list[Location]:
        s = SymbolParser(symbol)
        rets = self.get_reference(symbol.location.uri, s.symbol_col,
                                  s.symbol_line)
        return rets

    def get_reference(self, file, col: int, line: int) -> list[Location]:
        return self.lsp_client.references(file, col, line)

    def open_file(self, file):
        uri = to_file(file)
        relative_file_path = file
        import os
        if os.path.isabs(file) == False:
            relative_file_path = path.join(DEFAULT_ROOT, file)
        uri = to_file(relative_file_path)
        text = open(relative_file_path, "r").read()
        version = 2
        self.lsp_client.didOpen(
            TextDocumentItem(uri=uri,
                             languageId=LanguageIdentifier.CPP,
                             version=version,
                             text=text))
        return SourceCode(relative_file_path, self)


class lspcppserver:
    process = None

    def __init__(self):
        cmd = ["/home/z/.local/share/nvim/mason/bin/clangd"]
        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        read_pipe = ReadPipe(p.stderr)
        read_pipe.start()
        self.json_rpc_endpoint = pylspclient.JsonRpcEndpoint(p.stdin, p.stdout)

    def newclient(self, confg: project_config) -> lspcppclient:
        return lspcppclient(confg, self.json_rpc_endpoint)


DEFAULT_ROOT = path.abspath("./tests/test-workspace/cpp")


class lspcpp:

    def __init__(self, default_root) -> None:
        self.serv = lspcppserver()
        config = project_config()
        config.DEFAULT_ROOT = default_root
        self.client = self.serv.newclient(config)
        pass


class CallNode:

    def __init__(self, sym: PrepareReturn) -> None:
        self.sym = sym
        self.callee = None
        self.detail = ""

    def print(self, level=0):
        print(" " * level + "->", self.detail)
        if self.callee != None:
            self.callee.print(level + 1)


class CallerWalker:

    def __init__(self, client: lspcppclient, workspaceSymbol) -> None:
        self.caller_set = []
        self.client = client
        self.workspaceSymbol = workspaceSymbol
        pass

    def __get_caller_next(self, node: CallNode) -> list[CallNode]:
        param = node.sym

        has = list(filter(lambda x: x.range == param.range, self.caller_set))
        self.caller_set.append(param)
        parent = self.client.lsp_client.callIncoming(param)
        caller = list(map(lambda x: CallNode(x), parent))
        if len(has) == True and len(caller):
            return []
        for a in caller:
            a.callee = node
        if len(caller) == 0:
            return [node]
        resolv = self.workspaceSymbol.find(node)
        if resolv != None:
            node.detail = str(resolv)
        ret = []
        for a in caller:
            next = self.__get_caller_next(a)
            ret.extend(next)
        return ret

    def get_caller(self, sym: Symbol):
        if sym.is_call():
            ctx = client.lsp_client.callHierarchyPrepare(sym.sym)
            callser = []
            for a in ctx:
                c = CallNode(a)
                callser.extend(self.__get_caller_next(c))
            for s in callser:
                r = self.workspaceSymbol.find(s)
                if r != None:
                    s.detail = str(r)
            return callser
        return []

    def walk(self, node: CallNode):
        pass


class SourceCode:

    def __init__(self, file, client: lspcppclient) -> None:
        self.file = file
        self.lines = open(file, 'r').readlines()
        self.symbols = client.get_document_symbol(file)
        self.class_symbol = client.get_class_symbol(file)

    def find(self, node: CallNode):
        for a in self.class_symbol:
            r = a.find(node)
            if r != None:
                return r
            pass
        return None


class WorkSpaceSymbol:

    def __init__(self) -> None:
        self.source_list = {}
        pass

    def add(self, s: SourceCode):
        self.source_list[s.file] = s

    def find(self, node: CallNode):
        key = from_file(node.sym.uri)
        try:
            code = self.source_list[key]
            return code.find(node)
        except Exception as e:
            print(e)
        return None


if __name__ == "__main__":
    srv = lspcppserver()
    cfg = project_config()
    cfg.DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/"
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    source_file = client.open_file(file)
    wk = WorkSpaceSymbol()
    wk.add(source_file)
    for a in source_file.class_symbol:
        walk = CallerWalker(client, wk)
        for s in walk.get_caller(a):
            s.print()
        for m in a.members:
            ret = walk.get_caller(m)
            if len(ret) != 0:
                print("\t", m)
                for a in ret:
                    a.print()

    # for i in ss:
    #     if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
    #         sss = client.get_symbol_reference(i)
    #         for ss in sss:
    #             print("!!!", i.name, i.location.range, ss.range)
    #             callcontext = client.lsp_client.callHierarchyPrepare(i)
    #             for a in callcontext:
    #                 tree = client.lsp_client.callIncoming(a)
    #                 print(a.name)
    #                 i = 1
    #                 for t in tree:
    #                     print("\t" * i, "--", t.name)
    #                     i = i + 1
    #                     # print(json.dumps(t))
    #             print(len(callcontext))

    client.close()
