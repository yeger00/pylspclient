from __future__ import print_function
import subprocess
import json
import re
import threading
import lsp_structs

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


class LspEndpoint(threading.Thread):
    def __init__(self, json_rpc_endpoint, default_callback=print, callbacks={}):
        threading.Thread.__init__(self)
        self.json_rpc_endpoint = json_rpc_endpoint
        self.callbacks = callbacks
        self.default_callback = default_callback
        self.event_dict = {}
        self.response_dict = {}
        self.next_id = 0
        # self.daemon = True
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

            print("recieved message:", jsonrpc_message)
            if "result" in jsonrpc_message or "error" in jsonrpc_message:
                self.handle_result(jsonrpc_message)
            elif "method" in jsonrpc_message:
                if jsonrpc_message["method"] in self.callbacks:
                    self.callbacks[jsonrpc_message["method"]](jsonrpc_message)
                else:
                    self.default_callback(jsonrpc_message)
            else:
                print("unknown jsonrpc message")
            print(jsonrpc_message)
    
    
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
        # TODO: check if error, and throw an exception
        response = self.response_dict[current_id]
        return response["result"]


    def send_notification(self, method_name, **kwargs):
        self.send_message(method_name, kwargs)


class LspClient(object):
    def __init__(self, lpc_endpoint):
        self.lpc_endpoint = lpc_endpoint


    def initialize(self, processId, rootPath, rootUri, initializationOptions, capabilities, trace, workspaceFolders):
        """
        The initialize request is sent as the first request from the client to the server. If the server receives a request or notification 
        before the initialize request it should act as follows:

        1. For a request the response should be an error with code: -32002. The message can be picked by the server.
        2. Notifications should be dropped, except for the exit notification. This will allow the exit of a server without an initialize request.
        
        Until the server has responded to the initialize request with an InitializeResult, the client must not send any additional requests or 
        notifications to the server. In addition the server is not allowed to send any requests or notifications to the client until it has responded 
        with an InitializeResult, with the exception that during the initialize request the server is allowed to send the notifications window/showMessage, 
        window/logMessage and telemetry/event as well as the window/showMessageRequest request to the client.

        The initialize request may only be sent once.

        :param int processId: The process Id of the parent process that started the server. Is null if the process has not been started by another process.
                                If the parent process is not alive then the server should exit (see exit notification) its process.
        :param str rootPath: The rootPath of the workspace. Is null if no folder is open. Deprecated in favour of rootUri.
        :param DocumentUri rootUri: The rootUri of the workspace. Is null if no folder is open. If both `rootPath` and `rootUri` are set
                                    `rootUri` wins.
        :param any initializationOptions: User provided initialization options.
        :param ClientCapabilities capabilities: The capabilities provided by the client (editor or tool).
        :param Trace trace: The initial trace setting. If omitted trace is disabled ('off').
        :param list workspaceFolders: The workspace folders configured in the client when the server starts. This property is only available if the client supports workspace folders.
                                        It can be `null` if the client supports workspace folders but none are configured.
        """
        lsp_endpoint.start()
        return self.lpc_endpoint.call_method("initialize", processId=processId, rootPath=rootPath, rootUri=rootUri, initializationOptions=initializationOptions, capabilities=capabilities, trace=trace, workspaceFolders=workspaceFolders)


    def initialized(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lpc_endpoint.send_notification("initialized")


    def shutdown(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        lsp_endpoint.stop()
        return self.lpc_endpoint.call_method("shutdown")
       
       
    def exit(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lpc_endpoint.send_notification("exit")


    def didOpen(self, textDocument):
        """
        The document open notification is sent from the client to the server to signal newly opened text documents. The document's truth is
        now managed by the client and the server must not try to read the document's truth using the document's uri. Open in this sense 
        means it is managed by the client. It doesn't necessarily mean that its content is presented in an editor. An open notification must
        not be sent more than once without a corresponding close notification send before. This means open and close notification must be 
        balanced and the max open count for a particular textDocument is one. Note that a server's ability to fulfill requests is independent 
        of whether a text document is open or closed.

        The DidOpenTextDocumentParams contain the language id the document is associated with. If the language Id of a document changes, the 
        client needs to send a textDocument/didClose to the server followed by a textDocument/didOpen with the new language id if the server 
        handles the new language id as well.

        :param TextDocumentItem textDocument: The initial trace setting. If omitted trace is disabled ('off').
        """
        return self.lpc_endpoint.send_notification("textDocument/didOpen", textDocument=textDocument)


    def documentSymbol(self, textDocument):
        """
        The document symbol request is sent from the client to the server to return a flat list of all symbols found in a given text document. 
        Neither the symbol's location range nor the symbol's container name should be used to infer a hierarchy.

        :param TextDocumentItem textDocument: The text document.
        """
        result_dict =  self.lpc_endpoint.call_method("textDocument/documentSymbol", textDocument=textDocument)
        return [lsp_structs.SymbolInformation(**sym) for sym in result_dict]


    def definition(self, textDocument, position):
        """
        The goto definition request is sent from the client to the server to resolve the definition location of a symbol at a given text document position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document..
        """
        result_dict = self.lpc_endpoint.call_method("textDocument/definition", textDocument=textDocument, position=position)
        return [lsp_structs.Location(**l) for l in result_dict]


    def typeDefinition(self, textDocument, position):
        """
        The goto type definition request is sent from the client to the server to resolve the type definition location of a symbol at a given text document position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document..
        """
        result_dict = self.lpc_endpoint.call_method("textDocument/definition", textDocument=textDocument, position=position)
        return [lsp_structs.Location(**l) for l in result_dict]


    def signatureHelp(self, textDocument, position):
            """
            The signature help request is sent from the client to the server to request signature information at a given cursor position.            

            :param TextDocumentItem textDocument: The text document.
            :param Position position: The position inside the text document..
            """
            result_dict = self.lpc_endpoint.call_method("textDocument/signatureHelp", textDocument=textDocument, position=position)
            return lsp_structs.SignatureHelp(**result_dict)


########################################### Example Start

# clangd_path = "/usr/bin/clangd-6.0"
clangd_path = "/home/osboxes/projects/build/bin/clangd"
p = subprocess.Popen(clangd_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
json_rpc_endpoint = JsonRpcEndpoint(p.stdin, p.stdout)
# Working with socket:
# sock_fd = sock.makefile()
# json_rpc_endpoint = JsonRpcEndpoint(sock_fd, stext_document_res = lpc_client.send_notification(text_document_message)ock_fd)
lsp_endpoint = LspEndpoint(json_rpc_endpoint)

lsp_client = LspClient(lsp_endpoint)
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
languageId = lsp_structs.LANGUAGE_IDENTIFIER.C
version = 1
lsp_client.didOpen(lsp_structs.TextDocumentItem(uri, languageId, version, text))
lsp_client.documentSymbol(lsp_structs.TextDocumentIdentifier(uri))

lsp_client.definition(lsp_structs.TextDocumentIdentifier(uri), lsp_structs.Position(15, 4))
lsp_client.signatureHelp(lsp_structs.TextDocumentIdentifier(uri), lsp_structs.Position(15, 4))

lsp_client.shutdown()
lsp_client.exit()