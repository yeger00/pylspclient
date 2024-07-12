from typing import Any

__all__: list[Any] = []

from pylspclient.json_rpc_endpoint import JsonRpcEndpoint
from pylspclient.lsp_client import LspClient
from pylspclient.lsp_endpoint import LspEndpoint
from pylspclient import lsp_errors

import logging
logger = logging.getLogger('lsppython')
logger.setLevel(logging.DEBUG)
f_handler = logging.FileHandler('lspcore.log')  # This will log to a file
logger.addHandler(f_handler)
logger.critical('This is a critical message')