import os
import pylspclient
import pytest

JSON_RPC_RESULT_LIST = [
    'Content-Length: 40\r\n\r\n{"key_str": "some_string", "key_num": 1}'.encode("utf-8"),
    'Content-Length: 40\r\n\r\n{"key_num": 1, "key_str": "some_string"}'.encode("utf-8")
]


def test_send_sanity():
    pipein, pipeout = os.pipe()
    pipein = os.fdopen(pipein, "rb")
    pipeout = os.fdopen(pipeout, "wb")
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(pipeout, None)
    json_rpc_endpoint.send_request({"key_num":1, "key_str":"some_string"})
    result = pipein.read(len(JSON_RPC_RESULT_LIST[0]))
    assert(result in JSON_RPC_RESULT_LIST)


def test_send_class():
    class RpcClass(object):
        def __init__(self, value_num, value_str):
            self.key_num = value_num
            self.key_str = value_str
    
    pipein, pipeout = os.pipe()
    pipein = os.fdopen(pipein, "rb")
    pipeout = os.fdopen(pipeout, "wb")
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(pipeout, None)
    json_rpc_endpoint.send_request(RpcClass(1, "some_string"))
    result = pipein.read(len(JSON_RPC_RESULT_LIST[0]))
    assert(result in JSON_RPC_RESULT_LIST)
        

def test_recv_sanity():
    pipein, pipeout = os.pipe()
    pipein = os.fdopen(pipein, "rb")
    pipeout = os.fdopen(pipeout, "wb")
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(None, pipein)
    pipeout.write('Content-Length: 40\r\n\r\n{"key_str": "some_string", "key_num": 1}'.encode("utf-8"))
    pipeout.flush()
    result = json_rpc_endpoint.recv_response()
    assert({"key_num":1, "key_str":"some_string"} == result)


def test_recv_wrong_header():
    pipein, pipeout = os.pipe()
    pipein = os.fdopen(pipein, "rb")
    pipeout = os.fdopen(pipeout, "wb")
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(None, pipein)
    pipeout.write('Contentength: 40\r\n\r\n{"key_str": "some_string", "key_num": 1}'.encode("utf-8"))
    pipeout.flush()
    with pytest.raises(pylspclient.lsp_structs.ResponseError):
        result = json_rpc_endpoint.recv_response()
        print("should never get here", result)


def test_recv_missing_size():
    pipein, pipeout = os.pipe()
    pipein = os.fdopen(pipein, "rb")
    pipeout = os.fdopen(pipeout, "wb")
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(None, pipein)
    pipeout.write('Content-Type: 40\r\n\r\n{"key_str": "some_string", "key_num": 1}'.encode("utf-8"))
    pipeout.flush()
    with pytest.raises(pylspclient.lsp_structs.ResponseError):
        result = json_rpc_endpoint.recv_response()
        print("should never get here", result)


def test_recv_close_pipe():
    pipein, pipeout = os.pipe()
    pipein = os.fdopen(pipein, "rb")
    pipeout = os.fdopen(pipeout, "wb")
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(None, pipein)
    pipeout.close()
    result = json_rpc_endpoint.recv_response()
    assert(result is None)


