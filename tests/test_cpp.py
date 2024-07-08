import lspcpp
from lspcpp import lspcppclient,lspcppserver,project_config
from os import path
from pylspclient.lsp_pydantic_strcuts import DocumentSymbol, TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext, SymbolInformation, ReferenceParams, TextDocumentPositionParams, SymbolKind, ReferenceContext, Location

DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/test-workspace"


def test_client_init():
    lspcppserver = lspcpp.lspcppserver()
    cfg = lspcpp.project_config()
    cfg.DEFAULT_ROOT = DEFAULT_ROOT
    cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = lspcppserver.newclient(cfg)
    assert (client != None)
    client.close()


def test_client_symbol():
    lspcppserver = lspcpp.lspcppserver()
    cfg = lspcpp.project_config()
    cfg.DEFAULT_ROOT = DEFAULT_ROOT
    cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = lspcppserver.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ss = client.get_symbol(file)
    assert (len(ss) > 0)
    for i in ss:
        print(i)

    s3 = client.get_document_symbol(file)

    for s in s3:
        print(s.name, s.kind)
    client.close()


def test_client_reference():
    srv = lspcppserver()
    cfg = project_config()
    cfg.DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/"
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ss = client.get_symbol(file)
    assert (len(ss) > 0)
    for i in ss:
        if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
            sss = client.get_symbol_reference(i)
            for ss in sss:
                print("!!!", i.name, i.location.range, ss.range)

    client.close()
