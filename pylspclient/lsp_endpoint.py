from __future__ import print_function
import threading
import collections
from pylspclient import lsp_structs


class MethodNotFound(object):
    def __call__(self, jsonrpc_message):
        raise lsp_structs.ResponseError("Method not found: {method}".format(method=jsonrpc_message["method"]), lsp_structs.ErrorCodes.MethodNotFound)


class LspEndpoint(threading.Thread):
    def __init__(self, json_rpc_endpoint, default_method_callback=MethodNotFound(), method_callbacks={}, default_notify_callback=print, notify_callbacks={}):
        threading.Thread.__init__(self)
        self.json_rpc_endpoint = json_rpc_endpoint
        self.notify_callbacks = collections.defaultdict(lambda : default_notify_callback, notify_callbacks)
        self.method_callbacks = collections.defaultdict(lambda : default_method_callback, method_callbacks)
        self.event_dict = {}
        self.response_dict = {}
        self.next_id = 0
        self.shutdown_flag = False


    def handle_result(self, jsonrpc_res):
        self.response_dict[jsonrpc_res["id"]] = jsonrpc_res
        cond = self.event_dict[jsonrpc_res["id"]]
        cond.acquire()
        cond.notify()
        cond.release()


    def stop(self):
        self.shutdown_flag = True


    def run(self):
        while not self.shutdown_flag:
            jsonrpc_message = self.json_rpc_endpoint.recv_response()
            
            if jsonrpc_message is None:
                print("server quit")
                break

            if "result" in jsonrpc_message or "error" in jsonrpc_message:
                self.handle_result(jsonrpc_message)
            elif "method" in jsonrpc_message:
                if "id" in jsonrpc_message:
                    # a call for method
                    try:
                        result = self.method_callbacks[jsonrpc_message["method"]](jsonrpc_message)
                        self.send_response(jsonrpc_message["id"], result, None)
                    except lsp_structs.ResponseError as e:
                        self.send_response(jsonrpc_message["id"], None, e)                         
                else:
                    # a call for notify
                    self.notify_callbacks[jsonrpc_message["method"]](jsonrpc_message)
            else:
                print("unknown jsonrpc message")
   

    def send_response(self, id, result, error):
        message_dict = {}
        message_dict["jsonrpc"] = "2.0"
        message_dict["id"] = id
        if result:
            message_dict["result"] = result
        if error:
            message_dict["error"] = error
        self.json_rpc_endpoint.send_request(message_dict)
   

    def send_message(self, method_name, params, id = None):
        message_dict = {}
        message_dict["jsonrpc"] = "2.0"
        if id is not None:
            message_dict["id"] = id
        message_dict["method"] = method_name
        message_dict["params"] = params
        self.json_rpc_endpoint.send_request(message_dict)
        

    def call_method(self, method_name, **kwargs):
        current_id = self.next_id
        self.next_id += 1
        cond = threading.Condition()
        self.event_dict[current_id] = cond
        cond.acquire()
        self.send_message(method_name, kwargs, current_id)
        cond.wait()
        cond.release()
        response = self.response_dict[current_id]
        if "error" in response:
            error = response["error"]
            raise lsp_structs.ResponseError(error.get("code"), error.get("message"), error.get("data"))
        return response["result"]


    def send_notification(self, method_name, **kwargs):
        self.send_message(method_name, kwargs)
