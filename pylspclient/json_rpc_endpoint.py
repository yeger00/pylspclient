from __future__ import print_function
import json
import re
from pylspclient import lsp_structs
import threading

JSON_RPC_REQ_FORMAT = "Content-Length: {json_string_len}\r\n\r\n{json_string}\r\n\r\n"
JSON_RPC_RES_REGEX = "Content-Length: ([0-9]*)\r\n"
# TODO: add content-type


class MyEncoder(json.JSONEncoder):
    """
    Encodes an object in JSON
    """
    def default(self, o):
        return o.__dict__ 


class JsonRpcEndpoint(object):
    '''
    Thread safe JSON RPC endpoint implementation. Responsible to recieve and send JSON RPC messages, as described in the
    protocol. More information can be found: https://www.jsonrpc.org/
    '''
    def __init__(self, stdin, stdout):
        self.stdin = stdin
        self.stdout = stdout
        self.read_lock = threading.Lock() 
        self.write_lock = threading.Lock() 

    @staticmethod
    def __add_header(json_string):
        return JSON_RPC_REQ_FORMAT.format(json_string_len=len(json_string), json_string=json_string)


    def send_request(self, message):
        '''
        :param dict message: The message to send.            
        '''
        json_string = json.dumps(message, cls=MyEncoder)
        print("sending:", json_string)
        jsonrpc_req = self.__add_header(json_string)
        with self.write_lock:
            self.stdin.write(jsonrpc_req.encode())
            self.stdin.flush()


    def recv_response(self):
        '''
        '''
        with self.read_lock:
            line = self.stdout.readline()
            if line is None:
                return None
            line = line.decode()
            # TODO: handle content type as well.
            match = re.match(JSON_RPC_RES_REGEX, line)
            if match is None or not match.groups():
                # TODO: handle
                print("error1: ", line)
                return None
            size = int(match.groups()[0])
            line = self.stdout.readline()
            if line is None:
                return None
            line = line.decode()
            if line != "\r\n":
                # TODO: handle
                print("error2")
                return None
            jsonrpc_res = self.stdout.read(size)
            return json.loads(jsonrpc_res)
