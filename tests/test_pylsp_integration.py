import os.path
import pytest
import subprocess
import threading

import pylspclient


def to_uri(path: str) -> str:
    return f"uri://{path}"


class ReadPipe(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            print(line)
            line = self.pipe.readline().decode('utf-8')


@pytest.fixture
def server_process() -> subprocess.Popen:
    pylsp_cmd = ["python", "-m", "pylsp"]
    p = subprocess.Popen(pylsp_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    yield p
    p.kill()
    p.communicate()


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
DEFAULT_ROOT = "./tests/test-workspace/"


@pytest.fixture
def json_rpc(server_process: subprocess.Popen) -> pylspclient.JsonRpcEndpoint:
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(server_process.stdin, server_process.stdout)
    yield json_rpc_endpoint


@pytest.fixture
def lsp_client(json_rpc: pylspclient.JsonRpcEndpoint) -> pylspclient.LspClient:
    lsp_endpoint = pylspclient.LspEndpoint(json_rpc)
    lsp_client = pylspclient.LspClient(lsp_endpoint)
    process_id = None
    root_path = None
    root_uri = to_uri(DEFAULT_ROOT)
    initialization_options = None
    capabilities = DEFAULT_CAPABILITIES
    trace = "off"
    workspace_folders = None
    initialize_response = lsp_client.initialize(process_id, root_path, root_uri, initialization_options, capabilities, trace, workspace_folders)
    if initialize_response['serverInfo']['name'] != 'pylsp':
        raise RuntimeError("failed to initialize lsp_client")
    lsp_client.initialized()
    yield lsp_client
    lsp_client.shutdown()
    lsp_client.exit()


def test_initialize(json_rpc: pylspclient.JsonRpcEndpoint):
    lsp_endpoint = pylspclient.LspEndpoint(json_rpc)
    lsp_client = pylspclient.LspClient(lsp_endpoint)
    process_id = None
    root_path = None
    root_uri = ".."
    initialization_options = None
    capabilities = DEFAULT_CAPABILITIES
    trace = "off"
    workspace_folders = None
    initialize_response = lsp_client.initialize(process_id, root_path, root_uri, initialization_options, capabilities, trace, workspace_folders)
    lsp_client.initialized()
    assert initialize_response['serverInfo']['name'] == 'pylsp'
    lsp_client.shutdown()
    lsp_client.exit()


def test_type_definition(lsp_client: pylspclient.LspClient):
    file_path = "lsp_client.py"
    relative_file_path = os.path.join(DEFAULT_ROOT, file_path)
    uri = to_uri(relative_file_path)
    text = open(relative_file_path, "r").read()
    languageId = pylspclient.lsp_structs.LANGUAGE_IDENTIFIER.PYTHON
    version = 1
    # First need to open the file, and then iterate over the docuemnt's symbols
    symbols = lsp_client.documentSymbol(pylspclient.lsp_structs.TextDocumentIdentifier(uri))
    assert set(symbol.name for symbol in symbols) == set([])
    lsp_client.didOpen(pylspclient.lsp_structs.TextDocumentItem(uri, languageId, version, text))
    symbols = lsp_client.documentSymbol(pylspclient.lsp_structs.TextDocumentIdentifier(uri))
    expected_symbols = [
        '__init__',
        'declaration',
        'definition',
        'shutdown',
        'result_dict',
        'signatureHelp',
        'lsp_endpoint',
        'typeDefinition',
        'initialize',
        'didOpen',
        'initialized',
        'sym',
        'result',
        'LspClient',
        'didChange',
        'lsp_structs',
        'exit',
        'completion',
        'documentSymbol'
    ]
    assert set(symbol.name for symbol in symbols) == set(expected_symbols)
