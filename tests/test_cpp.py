import lspcpp
from lspcpp import WorkSpaceSymbol, lspcppclient, lspcppserver, project_config
from os import path
from pylspclient.lsp_pydantic_strcuts import DocumentSymbol, TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext, SymbolInformation, ReferenceParams, TextDocumentPositionParams, SymbolKind, ReferenceContext, Location

DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/test-workspace"


def test_client_init():
    cfg = lspcpp.project_config(
        workspace_root=DEFAULT_ROOT,
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    lspcppserver = lspcpp.lspcppserver(cfg.workspace_root)
    client = lspcppserver.newclient(cfg)
    assert (client != None)
    client.close()


def test_client_compile_database():
    cfg = lspcpp.project_config(
        workspace_root=DEFAULT_ROOT,
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    srv = lspcpp.lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    assert (client != None)
    wk = cfg.create_workspace(client)
    assert (len(wk.source_list) == 2)
    client.close()


def test_client_symbol():
    cfg = lspcpp.project_config(
        workspace_root=DEFAULT_ROOT,
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    srv = lspcpp.lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
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
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    srv = lspcppserver(cfg.workspace_root)
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


def test_client_reference_extern():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/d.cpp"
    symbols = client.open_file(file).symbols
    assert (len(symbols) > 0)
    for i in symbols:
        if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
            sss = client.get_symbol_reference(i)
            for a in sss:
                t = lspcpp.Token(a)
                print("!!!", t.data, a.range, t, a.uri)
            assert (len(sss) > 0)

    client.close()


def test_client_call_extern():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=
        "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json")
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    wk = cfg.create_workspace(client=client)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/d.cpp"
    source_file = client.open_file(file)
    for a in source_file.class_symbol:
        walk = lspcpp.CallerWalker(client, wk)
        for m in a.all_call_symbol():
            ret = walk.get_caller(m)
            for a in ret:
                a.resolve_all(wk)
                a.print()
    client.close()


def test_client_code_action():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    srv = lspcppserver(cfg.workspace_root)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ret = client.lsp_client.code_action(file)
    client.close()

def test_client_index():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    ret = client.lsp_client.process()
    print(ret)
    client.close()


def test_client_did_changed():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ret = client.lsp_client.didChange(file)
    print(ret)
    client.close()


def test_client_workspacesymbol():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
    ss = client.open_file(file).symbols
    ret = client.lsp_client.workspace_symbol()
    client.close()


def test_client_prepare():
    cfg = project_config(
        workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
        compile_database=None)
    srv = lspcppserver(cfg.workspace_root)
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


def test_args():
    root = "/home/z/dev/lsp/pylspclient/tests/cpp/"
    file = "/home/z/dev/lsp/pylspclient/tests/cpp/d.cpp"
    method = "class_c::run_class_c"

    cfg = project_config(workspace_root=root)
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)

    wk = cfg.create_workspace(client=client)

    symbols_list = client.get_document_symbol(file)

    def find_fn(x: SymbolInformation):
        if x.name == method:
            return True
        return False

    symbo = list(filter(find_fn, symbols_list))
    walk = lspcpp.CallerWalker(client, wk)
    ret = walk.get_caller(lspcpp.Symbol(symbo[0]))
    for a in ret:
        a.resolve_all(wk)
        a.print()
