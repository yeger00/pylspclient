from typing import Optional
from os import path, listdir
import pytest
import subprocess
import threading

import pylspclient
from pylspclient.lsp_pydantic_strcuts import TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext


def to_file(path: str) -> str:
    if path.startswith("file://"):
        return path
    return f"file://{path}"
def to_uri(path: str) -> str:
    if path.startswith("uri://"):
        return path
    return f"uri://{path}"

def from_file(path: str) -> str:
    return path.replace("file://", "").replace("file:", "")


def from_uri(path: str) -> str:
    return path.replace("uri://", "").replace("uri:", "")


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
    pylsp_cmd = ["/home/z/.local/share/nvim/mason/bin/clangd"]
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
DEFAULT_ROOT = path.abspath("./tests/test-workspace/")


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
    root_uri = to_file(DEFAULT_ROOT)
    initialization_options = None
    capabilities = DEFAULT_CAPABILITIES
    trace = "off"
    workspace_folders = None
    initialize_response = lsp_client.initialize(process_id, root_path, root_uri, initialization_options, capabilities, trace, workspace_folders)
    if initialize_response['serverInfo']['name'] != 'clangd':
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
    assert initialize_response['serverInfo']['name'] == 'clangd'
    lsp_client.shutdown()
    lsp_client.exit()


def test_document_symbol(lsp_client: pylspclient.LspClient):
    file_path = "test_main.cpp"
    relative_file_path = path.join(DEFAULT_ROOT, file_path)
    uri = to_file(relative_file_path)
    text = open(relative_file_path, "r").read()
    languageId = LanguageIdentifier.CPP
    version = 1
    lsp_client.didOpen(TextDocumentItem(uri=uri, languageId=languageId, version=version, text=text))
    symbols = lsp_client.documentSymbol(TextDocumentIdentifier(uri=uri))
    for i in symbols:
        print(i)
    # assert set(symbol.name for symbol in symbols) == set(expected_symbols)


def add_dir(lsp_client: pylspclient.LspClient, root: str):
    for filename in listdir(root):
        if filename.endswith(".cpp"):
            add_file(lsp_client, path.join(root, filename))


def add_file(lsp_client: pylspclient.LspClient, relative_file_path: str):
    uri = to_file(relative_file_path)
    text = open(relative_file_path, "r").read()
    languageId = LanguageIdentifier.CPP
    version = 1
    # First need to open the file, and then iterate over the docuemnt's symbols
    lsp_client.didOpen(TextDocumentItem(uri=uri, languageId=languageId, version=version, text=text))


def string_in_text_to_position(text: str, string: str) -> Optional[Position]:
    for i, line in enumerate(text.splitlines()):
        char = line.find(string)
        if char != -1:
            return Position(line=i, character=char)
    return None


def range_in_text_to_string(text: str, range_: Range) -> Optional[str]:
    lines = text.splitlines()
    if range_.start.line == range_.end.line:
        # Same line
        return lines[range_.start.line][range_.start.character:range_.end.character]
    raise NotImplementedError


def test_definition(lsp_client: pylspclient.LspClient):
    add_dir(lsp_client, DEFAULT_ROOT)
    file_path = "test_main.cpp"
    relative_file_path = path.join(DEFAULT_ROOT, file_path)
    uri = to_file(relative_file_path)
    file_content = open(relative_file_path, "r").read()
    position = string_in_text_to_position(file_content, "send_notification")
    definitions = lsp_client.definition(TextDocumentIdentifier(uri=uri), position)
    assert len(definitions) == 1
    result_path = from_file(definitions[0].uri)
    result_file_content = open(result_path, "r").read()
    result_definition = range_in_text_to_string(result_file_content, definitions[0].range)
    assert result_definition == "send_notification"


def test_completion(lsp_client: pylspclient.LspClient):
    add_dir(lsp_client, DEFAULT_ROOT)
    file_path = "test_main.cpp"
    relative_file_path = path.join(DEFAULT_ROOT, file_path)
    uri = to_file(relative_file_path)
    file_content = open(relative_file_path, "r").read()
    to_complete = "send_"
    position = string_in_text_to_position(file_content, to_complete + " ")
    position.character += len(to_complete)
    context = CompletionContext(triggerKind=CompletionTriggerKind.Invoked)
    completion_result = lsp_client.completion(TextDocumentIdentifier(uri=uri), position, context)
    assert all([i.insertText.startswith(to_complete) for i in completion_result.items])
