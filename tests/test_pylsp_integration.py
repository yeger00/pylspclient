import pytest
import threading
import subprocess

import pylspclient


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


@pytest.fixture
def json_rpc(server_process: subprocess.Popen) -> pylspclient.JsonRpcEndpoint:
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(server_process.stdin, server_process.stdout)
    yield json_rpc_endpoint


def test_initialize(json_rpc: pylspclient.JsonRpcEndpoint):
    lsp_endpoint = pylspclient.LspEndpoint(json_rpc)
    lsp_client = pylspclient.LspClient(lsp_endpoint)
    process_id = None
    root_path = None
    root_uri = ".."
    initialization_options = None
    capabilities = {
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
    trace = "off"
    workspace_folders = None
    initialize_response = lsp_client.initialize(process_id, root_path, root_uri, initialization_options, capabilities, trace, workspace_folders)
    _ = lsp_client.initialized()
    assert initialize_response['serverInfo']['name'] == 'pylsp'
    lsp_client.shutdown()
    lsp_client.exit()
