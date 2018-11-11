class Message(object):
    """
    JSON RPC Base message class
    """
    def __init__(self, jsonrpc):
        """
        Constructs a new Message instance.

        :param string jsonrpc: jsonrpc version. Should be 2.0
        """
        super(Message, self)
        self.jsonrpc = jsonrpc


class RequestMessage(Message):
    '''
    JSON RPC Request message class
    '''
    def __init__(self, jsonrpc, request_id, method, params):
        '''
        Constructs a new RequestMessage instance.

        :param string jsonrpc: jsonrpc version. Should be 2.0
        :param int request_id: The request id.
        :param string method: The method to be invoked.
        :param list params: The method's params.
        '''
        super(RequestMessage, self).__init__(jsonrpc)
        self.id = request_id
        self.method = method
        self.params = params


class ResponseMessage(Message):
    '''
    JSON RPC Response message class
    '''
    def __init__(self, jsonrpc, request_id, result, error):
        '''
        Constructs a new ResponseMessage instance.

        :param string jsonrpc: jsonrpc version. Should be 2.0
        :param int request_id: The request id.
        :param result: The result of a request. This can be omitted in the case of an error.
        :param ResponseError error: The error object in case a request fails.
        '''
        super(ResponseMessage, self).__init__(jsonrpc)
        self.id = request_id
        self.result = result
        self.error = error


class ResponseError(object):
    '''
    '''
    def __init__(self, code, message, data):
        '''
        Constructs a new ResponseError instance.

        :param int code: A number indicating the error type that occurred.
        :param string message: A string providing a short description of the error.
        :param data: A Primitive or Structured value that contains additional information about the error. Can be omitted.
        '''
        super(ResponseError, self).__init__()
        self.code = code
        self.message = message
        self.data = data


class ErrorCodes(object):
    '''
    '''
    # Defined by JSON RPC
    ParseError= -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    serverErrorStart = -32099
    serverErrorEnd = -32000
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001   

    # Defined by the protocol.
    RequestCancelled= -32800


class NotificationMessage(Message):
    '''
    '''
    def __init__(self, jsonrpc, method, params):
        '''
        Constructs a new NotificationMessage instance.

        :param string jsonrpc: jsonrpc version. Should be 2.0
        :param string method: The method to be invoked.
        :param list ResponseError params: The notification's params.
        '''
        super(NotificationMessage, self).__init__(jsonrpc)
        self.method = method
        self.params = params


class CancelParams(object):
    '''
    '''
    def __init__(self, request_id):
        '''
        Constructs a new CancelParams instance.

        :param int request_id: The request id to cancel.
        '''
        self.id = request_id
