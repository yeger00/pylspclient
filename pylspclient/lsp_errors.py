from typing import Any
from enum import IntEnum


class ErrorCodes(IntEnum):
    # Defined by JSON RPC
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    serverErrorStart = -32099
    serverErrorEnd = -32000
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001

    # Defined by the protocol.
    RequestCancelled = -32800
    ContentModified = -32801


class ResponseError(Exception):
    def __init__(self, code: ErrorCodes, message: str, data: Any = None):
        self.code = code
        self.message = message
        if data:
            self.data = data
