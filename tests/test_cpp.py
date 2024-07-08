import lspcpp
from os import path

DEFAULT_ROOT = "/home/z/dev/lsp/pylspclient/tests/cpp/test-workspace"


def test_client_init():
    lspcppserver = lspcpp.lspcppserver()
    cfg = lspcpp.project_config()
    cfg.DEFAULT_ROOT = DEFAULT_ROOT
    cfg.data_path = "/home/z/dev/lsp/pylspclient/tests/cpp/compile_commands.json"
    client = lspcppserver.newclient(cfg)
    assert (client != None)


def test_client_init():
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
        print(s.name,s.kind)
