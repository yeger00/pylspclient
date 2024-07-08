import subprocess
import pylspclient
import threading
from os import path
from pylspclient.lsp_pydantic_strcuts import TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext

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


class ReadPipe(threading.Thread):

    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            print('pipe:', line)
            line = self.pipe.readline().decode('utf-8')


def to_file(path: str) -> str:
    if path.startswith("file://"):
        return path
    return f"file://{path}"


class project_config:
    data_path: None | str
    DEFAULT_ROOT: None | str

    def __init__(self) -> None:
        self.DEFAULT_ROOT = None
        self.data_path = None


class lspcppclient:

    def __init__(self, config: project_config,
                 json_rpc_endpoint: pylspclient.JsonRpcEndpoint) -> None:
        lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)
        lsp_client = pylspclient.LspClient(lsp_endpoint)
        process_id = None
        root_path = None
        assert (config.DEFAULT_ROOT != None)
        root_uri = to_file(config.DEFAULT_ROOT)
        data_path = config.data_path
        initialization_options = {
            "compilationDatabasePath": data_path
        } if data_path != None else None
        capabilities = DEFAULT_CAPABILITIES
        trace = "off"
        workspace_folders = None
        initialize_response = lsp_client.initialize(process_id, root_path,
                                                    root_uri,
                                                    initialization_options,
                                                    capabilities, trace,
                                                    workspace_folders)
        if initialize_response['serverInfo']['name'] != 'clangd':
            raise RuntimeError("failed to initialize lsp_client")
        lsp_client.initialized()
        self.lsp_client = lsp_client
        pass

    def close(self):
        self.lsp_client.exit()

    def get_symbol(self, file):
        uri = to_file(file)
        relative_file_path = path.join(DEFAULT_ROOT, file)
        uri = to_file(relative_file_path)
        text = open(relative_file_path, "r").read()
        version = 1
        self.lsp_client.didOpen(
            TextDocumentItem(uri=uri,
                             languageId=LanguageIdentifier.CPP,
                             version=version,
                             text=text))
        symbols = self.lsp_client.documentSymbol(
            TextDocumentIdentifier(uri=uri))
        return symbols


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

    def __init__(self) -> None:
        self.serv = lspcppserver()
        config = project_config()
        config.DEFAULT_ROOT = DEFAULT_ROOT
        self.client = self.serv.newclient(config)
        pass


DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/test-workspace"
if __name__ == "__main__":
    srv = lspcppserver()
    cfg = project_config()
    cfg.DEFAULT_ROOT = DEFAULT_ROOT
    cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ss = client.get_symbol(file)
    assert (len(ss) > 0)
    for i in ss:
        print(i.name, i.kind)
    client.close()
