from cpp_impl import LspFuncParameter_cpp
from common import Body 
import lspcpp
from lspcpp import SymbolKindName, Token, WorkSpaceSymbol, from_file, lspcppclient, lspcppserver, project_config, to_file
from pylspclient.lsp_pydantic_strcuts import DocumentSymbol, TextDocumentIdentifier, TextDocumentItem, LanguageIdentifier, Position, Range, CompletionTriggerKind, CompletionContext, SymbolInformation, ReferenceParams, TextDocumentPositionParams, SymbolKind, ReferenceContext, Location
import os
DEFAULT_ROOT = os.path.join(os.path.dirname(__file__),"cpp/test-workspace")

workspace_root= os.path.join(os.path.dirname(__file__),"cpp/")
cfg = project_config(
    workspace_root=workspace_root, 
    compile_database=os.path.join(os.path.dirname(__file__),"cpp","/compile_commands.json")
)

def test_export_png():
    file="/home/z/dev/lsp/pylspclient/export/navigation_throttle_h:140_WillStartRequest/NavigationRequest::CancelDeferredNavigationInternalnavigation_request.cc:6537.puml"
    # planuml_to_image
    from planuml import planuml_to_image
    planuml_to_image(file,"")
    


def test_client_init():
    lspcppserver = lspcpp.lspcppserver(cfg.workspace_root)
    client = lspcppserver.newclient(cfg)
    assert (client != None)
    client.close()


# def test_client_compile_database():
#     srv = lspcpp.lspcppserver(cfg.workspace_root)
#     client = srv.newclient(cfg)
#     assert (client != None)
#     wk = cfg.create_workspace(client)
#     assert (len(wk.source_list) == 2)
#     client.close()


def test_client_signature_help():
    srv = lspcpp.lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = workspace_root+"/test_main.cpp"
    source = client.open_file(file)
    ss = source.symbols
    assert (len(ss) > 0)
    for i in ss:
        print(i)
    s3 = client.get_document_symbol(file)
    file = to_file(file)
    for s in s3:
        if s.kind == SymbolKind.Function or s.kind == SymbolKind.Method:
            tt = Token(s.location).data
            name = s.name
            begin = s.location.range.start.character
            sss = []
            while begin < s.location.range.end.character:
                ret = client.lsp_client.signatureHelp(textDocument=TextDocumentIdentifier(
                    uri=file), position=Position(character=begin, line=s.location.range.start.line))
                if len(ret.signatures):
                    print("+++%s+++ {%s} begin=%d find=%s ****%s*****" %
                          (tt, name, s.location.range.start.character, begin, tt[begin:]))
                    print(ret.signatures)
                    sss = ret.signatures
                    begin = 10000
                    break
                begin = begin+1

            if len(sss) == 0:
                print("!!!!", "%s +++%s+++" % (name, tt), ":", s.location.uri,
                      s.location.range.start.line+1, SymbolKindName(s.kind))

    client.close()




def test_client_symbol_param():
    srv = lspcpp.lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    source = client.open_file(file)
    s3 = client.get_document_symbol(file)
    for s in s3:
        body = Body(s.location)
        name = s.name
        kind = SymbolKindName(s.kind)
        if s.kind == SymbolKind.Method or SymbolKind.Function == s.kind:
            print("name=%s\n kind=%s\n block=++%s--" % (name, kind, str(body)))
            print("parameters:", name, "(", LspFuncParameter_cpp(s), ")")
        else:
            # print("xxx name=%s\n kind=%s\n token=%s" % (name, kind, str(body)))
            pass
    client.close()


def test_client_symbol():
    srv = lspcpp.lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    source = client.open_file(file)
    s3 = client.get_document_symbol(file)
    for s in s3:
        name = s.name
        kind = SymbolKindName(s.kind)
        token = Token(s.location)
        print("name=%s\n kind=%s\n token=%s" % (name, kind, token.data))
    client.close()


def test_client_reference():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    ss = client.open_file(file).symbols
    assert (len(ss) > 0)
    for i in ss:
        if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
            sss = client.get_symbol_reference(i)
            for ss in sss:
                print("!!!", i.name, i.location.range, ss.range)

    client.close()

def test_callin_2():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"d.h")
    client.open_file(file)    
    symbols = client.get_document_symbol(file)
    for s in symbols:
        print(s.name)
        if s.name.find("call_1")>-1:
            prepare = client.lsp_client.callHierarchyPrepare(sym=s)
            def print_prepare(prepare):
                print(prepare[0].name,
                  prepare[0].range.start.line,
                  prepare[0].selectionRange.start.line)
            
            assert(len(prepare)==1)
            print_prepare(prepare)
            prepare = client.lsp_client.callIncoming(prepare[0])
            assert(len(prepare)==1)
            print_prepare(prepare)
            
            prepare = client.lsp_client.callIncoming(prepare[0])
            assert(len(prepare)==1)
            print_prepare(prepare)
            prepare = client.lsp_client.callIncoming(prepare[0])
            assert(len(prepare)==1)
            print_prepare(prepare)
            return
    assert(False)


def test_callin_3():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    client.open_file(file)
    symbols = client.get_document_symbol(file)
    for s in symbols:
        print(s.name)
        if s.name.find("call_3")>-1:
            prepare = client.lsp_client.callHierarchyPrepare(sym=s)
            assert(len(prepare)==1)
            prepare = client.lsp_client.callIncoming(prepare[0])
            print(prepare[0].name)
            assert(len(prepare)==1)
            print(prepare[0].name)
            return

    assert(False)


def test_client_reference_extern():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"d.cpp")
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
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    wk = cfg.create_workspace(client=client)
    file =os.path.join(workspace_root, "d.cpp")
    source_file = client.open_file(file)
    for a in source_file.class_symbol:
        walk = lspcpp.CallerWalker(client, wk)
        for m in a.all_call_symbol():
            ret = walk.get_caller(m)
            for a in ret:
                a.resolve_all(wk)
                # a.print()
    client.close()


def test_client_code_action():
    srv = lspcppserver(cfg.workspace_root)
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    ret = client.lsp_client.code_action(file)
    client.close()


def test_client_index():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    ret = client.lsp_client.process()
    print(ret)
    client.close()


# def test_client_did_changed():
#     cfg = project_config(
#         workspace_root="/home/z/dev/lsp/pylspclient/tests/cpp/",
#         compile_database=None)
#     # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
#     srv = lspcppserver(cfg.workspace_root)
#     client = srv.newclient(cfg)
#     file = "/home/z/dev/lsp/pylspclient/tests/cpp/test_main.cpp"
#     ret = client.lsp_client.didChange(file)
#     print(ret)
#     client.close()

def test_client_open():
    # open='/chrome/buildcef/chromium/src/chrome/browser/first_party_sets/first_party_sets_navigation_throttle.cc'
    # cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    ss = client.open_file(file).symbols
    ret = client.lsp_client.workspace_symbol("a")
    client.close()


def test_client_synax_full():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    ss = client.open_file(file).symbols
    token = client.lsp_client.document_semantictokens_full(file)
    ret = client.lsp_client.document_semantictokens_delta(file, token)
    client.close()


def test_client_workspacesymbol():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    ss = client.open_file(file).symbols
    ret = client.lsp_client.workspace_symbol("a")
    client.close()


def test_client_prepare():
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)
    file = os.path.join(workspace_root,"test_main.cpp")
    ss = client.open_file(file).symbols
    assert (len(ss) > 0)
    for i in ss:
        if i.kind == SymbolKind.Method or SymbolKind.Function == i.kind:
            sss = client.lsp_client.callHierarchyPrepare(i)
            for ss in sss:
                print("!!!", i.name, i.location.range, ss.range)

    client.close()


def test_args():
    file = os.path.join(workspace_root,"d.cpp")
    method = "class_c::run_class_c"

    cfg = project_config(workspace_root=workspace_root)
    srv = lspcppserver(cfg.workspace_root)
    client = srv.newclient(cfg)

    wk = cfg.create_workspace(client=client)
    client.open_file(file)
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
        # a.print()
