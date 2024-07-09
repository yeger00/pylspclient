import lspcpp
from lspcpp import WorkSpaceSymbol, lspcppclient, lspcppserver, project_config
from os import path
from pylspclient.lsp_pydantic_strcuts import DocumentSymbol, TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext, SymbolInformation, ReferenceParams, TextDocumentPositionParams, SymbolKind, ReferenceContext, Location

DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/test-workspace"


def test_client_init():
    lspcppserver = lspcpp.lspcppserver()
    cfg = lspcpp.project_config(
        workspace_root=DEFAULT_ROOT,
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    client = lspcppserver.newclient(cfg)
    assert (client != None)
    client.close()


def test_client_compile_database():
    lspcppserver = lspcpp.lspcppserver()
    cfg = lspcpp.project_config(
        workspace_root=DEFAULT_ROOT,
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    client = lspcppserver.newclient(cfg)
    assert (client != None)
    wk = cfg.create_workspace(client)
    assert (len(wk.source_list) == 2)
    client.close()


def test_client_symbol():
    lspcppserver = lspcpp.lspcppserver()
    cfg = lspcpp.project_config(
        workspace_root=DEFAULT_ROOT,
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    client = lspcppserver.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    source = client.open_file(file)
    ss = source.symbols
    assert (len(ss) > 0)
    for i in ss:
        print(i)

    s3 = client.get_document_symbol(file)

    for s in s3:
        print(s.name, s.kind)
    client.close()


def test_client_reference():
    srv = lspcppserver()
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ss = client.open_file(file).symbols
    assert (len(ss) > 0)
    for i in ss:
        if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
            sss = client.get_symbol_reference(i)
            for ss in sss:
                print("!!!", i.name, i.location.range, ss.range)

    client.close()


def test_client_prepare():
    srv = lspcppserver()
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ss = client.open_file(file).symbols
    assert (len(ss) > 0)
    for i in ss:
        if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
            sss = client.lsp_client.callHierarchyPrepare(i)
            for ss in sss:
                print("!!!", i.name, i.location.range, ss.range)

    client.close()
