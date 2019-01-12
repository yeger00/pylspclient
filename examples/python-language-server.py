import pylspclient
import subprocess
import threading


# In order to run this example, you need to have python-language-server module installed.
# See more information on the project page: https://github.com/palantir/python-language-server


class ReadPipe(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            print(line)
            line = self.pipe.readline().decode('utf-8')

if __name__ == "__main__":
    pyls_cmd = ["python", "-m", "pyls"]
    p = subprocess.Popen(pyls_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    read_pipe = ReadPipe(p.stderr)
    read_pipe.start()
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(p.stdin, p.stdout)
    # To work with socket: sock_fd = sock.makefile()
    lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)

    lsp_client = pylspclient.LspClient(lsp_endpoint)
    capabilities = {'textDocument': {'codeAction': {'dynamicRegistration': True},
    'codeLens': {'dynamicRegistration': True},
    'colorProvider': {'dynamicRegistration': True},
    'completion': {'completionItem': {'commitCharactersSupport': True,
        'documentationFormat': ['markdown', 'plaintext'],
        'snippetSupport': True},
    'completionItemKind': {'valueSet': [1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25]},
    'contextSupport': True,
    'dynamicRegistration': True},
    'definition': {'dynamicRegistration': True},
    'documentHighlight': {'dynamicRegistration': True},
    'documentLink': {'dynamicRegistration': True},
    'documentSymbol': {'dynamicRegistration': True,
    'symbolKind': {'valueSet': [1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26]}},
    'formatting': {'dynamicRegistration': True},
    'hover': {'contentFormat': ['markdown', 'plaintext'],
    'dynamicRegistration': True},
    'implementation': {'dynamicRegistration': True},
    'onTypeFormatting': {'dynamicRegistration': True},
    'publishDiagnostics': {'relatedInformation': True},
    'rangeFormatting': {'dynamicRegistration': True},
    'references': {'dynamicRegistration': True},
    'rename': {'dynamicRegistration': True},
    'signatureHelp': {'dynamicRegistration': True,
    'signatureInformation': {'documentationFormat': ['markdown', 'plaintext']}},
    'synchronization': {'didSave': True,
    'dynamicRegistration': True,
    'willSave': True,
    'willSaveWaitUntil': True},
    'typeDefinition': {'dynamicRegistration': True}},
    'workspace': {'applyEdit': True,
    'configuration': True,
    'didChangeConfiguration': {'dynamicRegistration': True},
    'didChangeWatchedFiles': {'dynamicRegistration': True},
    'executeCommand': {'dynamicRegistration': True},
    'symbol': {'dynamicRegistration': True,
    'symbolKind': {'valueSet': [1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26]}},'workspaceEdit': {'documentChanges': True},
    'workspaceFolders': True}}
    root_uri = 'file:///path/to/python/project'
    workspace_folders = [{'name': 'python-lsp', 'uri': root_uri}]
    print(lsp_client.initialize(p.pid, None, root_uri, None, capabilities, "off", workspace_folders))
    print(lsp_client.initialized())

    lsp_client.shutdown()
    lsp_client.exit()
