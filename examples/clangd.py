import pylspclient
import subprocess


if __name__ == "__main__":
    # clangd_path = "/usr/bin/clangd-6.0"
    clangd_path = "/home/osboxes/projects/build/bin/clangd"
    p = subprocess.Popen(clangd_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(p.stdin, p.stdout)
    # Working with socket:
    # sock_fd = sock.makefile()
    # json_rpc_endpoint = JsonRpcEndpoint(sock_fd, stext_document_res = lpc_client.send_notification(text_document_message)ock_fd)
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
    workspace_folders = [{'name': 'python-lsp', 'uri': 'file:///home/osboxes/projects/ctest'}]
    root_uri = 'file:///home/osboxes/projects/ctest'
    print(lsp_client.initialize(p.pid, None, root_uri, None, capabilities, "off", workspace_folders))
    print(lsp_client.initialized())

    file_path = "/home/osboxes/projects/ctest/test.c"
    uri = "file://" + file_path
    text = open(file_path, "r").read()
    languageId = pylspclient.lsp_structs.LANGUAGE_IDENTIFIER.C
    version = 1
    lsp_client.didOpen(pylspclient.lsp_structs.TextDocumentItem(uri, languageId, version, text))
    lsp_client.documentSymbol(pylspclient.lsp_structs.TextDocumentIdentifier(uri))

    lsp_client.definition(pylspclient.lsp_structs.TextDocumentIdentifier(uri), pylspclient.lsp_structs.Position(15, 4))
    lsp_client.signatureHelp(pylspclient.lsp_structs.TextDocumentIdentifier(uri), pylspclient.lsp_structs.Position(15, 4))

    lsp_client.shutdown()
    lsp_client.exit()
