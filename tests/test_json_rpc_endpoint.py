import pylspclient
from pytest_mock import mocker 


class StdinMock(object):
    def write(self, s):
        pass

    def flush(self):
        pass


def test_sanity(mocker):
    stdin_mock = StdinMock();
    mocker.patch.object(stdin_mock, 'write') 
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(stdin_mock, None)
    json_rpc_endpoint.send_request({"key_num":1, "key_str":"some_string"})
    stdin_mock.write.assert_called()

    assert(stdin_mock.write.call_args not in [
        '''Content-Length: 40\r\n\r\n{"key_str": "some_string", "key_num": 1}\r\n\r\n'''.encode("utf-8"),
        '''Content-Length: 40\r\n\r\n{"key_num": 1, "key_str": "some_string"}\r\n\r\n'''.encode("utf-8")
    ])


def test_class(mocker):
    class RpcClass(object):
        def __init__(self, value_num, value_str):
            self.key_num = value_num
            self.key_str = value_str
        
    stdin_mock = StdinMock();
    mocker.patch.object(stdin_mock, 'write') 
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(stdin_mock, None)
    json_rpc_endpoint.send_request(RpcClass(1, "some_string"))
    stdin_mock.write.assert_called()

    assert(stdin_mock.write.call_args not in [
        '''Content-Length: 40\r\n\r\n{"key_str": "some_string", "key_num": 1}\r\n\r\n'''.encode("utf-8"),
        '''Content-Length: 40\r\n\r\n{"key_num": 1, "key_str": "some_string"}\r\n\r\n'''.encode("utf-8")
    ])

# content of test_sample.py
def func(x):
    return x + 1
