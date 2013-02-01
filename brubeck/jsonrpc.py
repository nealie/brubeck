"""
Simple JSON-RPC implementation supporting connections using HTTP POST.
"""

import json
import logging
import sys
import traceback

from brubeck.connections import Mongrel2Connection
from brubeck.request import Request
from brubeck.request_handling import MessageHandler, JSONMessageHandler, render


class JsonRpcError(Exception):
    """
    Base class for all JSON-RPC exceptions.

    All derived classes need to set:
    - status: The status code to report for the error.
    - id: The message id causing the error.
    """
    pass

    @property
    def message(self):
        """
        Must be reimplemented for each derived Exception.
        """
        return None


class MethodNotFoundError(JsonRpcError):
    """
    A message called an invalid method.
    """
    def __init__(self, id, method):
        self.status = -4
        self.id = id
        self.method = method

    @property
    def message(self):
        return "Method '{0}' not found.".format(self.method)


class MalformedV1RequestError(JsonRpcError):
    """
    A JSON-RPC V1.x message was malformed.
    """
    def __init__(self, message, key):
        self.status = JsonRpcHandler._DEFAULT_STATUS
        self.id = None
        self.msg = message
        self.key = key

    @property
    def message(self):
        return "Malformed message'{0}', key '{1}' not found.".format(self.msg, self.key)


class JsonRpcExecError(JsonRpcError):
    """
    An error ocurred executing a method.
    """
    def __init__(self, msgid, method, where, why, how):
        self.status = JsonRpcHandler._SERVER_ERROR
        self.id = msgid
        self.method = method
        self.where = where
        self.why = why
        self.how = how

    @property
    def message(self):
        return "{0}: {1}\n{2}".format(self.where, self.why, self.how)


def embed_methods(cls):
    """
    Decorator to allow JSON-RPC methods to be embedded in a class definition.

    Store the names of the methods decorated with the method decorator.
    """
    for name, method in cls.__dict__.iteritems():
        if hasattr(method, "_jsonrpc_method"):
            cls._method_names.append(name)
    return cls

def method(view):
    """
    Decorator to mark a method as a JSON-RPC method.
    """
    view._jsonrpc_method = True
    return view


class JsonRpcHandler(JSONMessageHandler):

    VERSION = "version"
    JSONRPC = "jsonrpc"

    class __metaclass__(type):
        """
        Metaclass to give each derived class a unique set of methods.
        """
        def __init__(cls, name, bases, dct):
            cls._method_names = []
            type.__init__(cls, name, bases, dct)

    def __init__(self, *args, **kwargs):
        """
        Generate a dict of bound methods from the method names stored at class creation time.
        """
        super(JsonRpcHandler, self).__init__(*args, **kwargs)
        self.methods = {}
        for name in self._method_names:
            self.methods[name] = getattr(self, name)

    def __call__(self):
        """
        Process the message.
        """
        try:
            logging.info("Request: {0}".format(self.message.body))
            data = json.loads(self.message.body)
            if self.JSONRPC in data:
                # Version 2.0
                result = self._process_v2(data)
            else:
                # Version 1.x
                result = self._process_v1(data)
            self.set_status(self._SUCCESS_CODE)
        except JsonRpcError, error:
            self.set_status(error.status)
            result = {
                "id": error.id,
                "error": {
                    "message": error.message
                }
            }
        if self.VERSION in data:
            result[self.VERSION] = self.message.data[self.VERSION]
        elif self.JSONRPC in self.message.data:
            result[self.JSONRPC] = self.message.data[self.JSONRPC]

        logging.info("Response: {0}".format(result))

        self._payload["data"] = result

        return self.render(hide_status=True)

    def _process_v1(self, data):
        """
        Process a JSON-RPC V1.x formatted message.
        """
        try:
            msgid, method, params = data["id"], data["method"], data["params"]
        except KeyError, error:
            raise MalformedV1RequestError(data, error.args[0])
        if method not in self.methods:
            raise MethodNotFoundError(method)
        try:
            result = self.methods[method](*params)
            return {
                "id": msgid,
                "error": None,
                "result": result
            }
        except:
            etype, value, etb = sys.exc_info()
            tb = traceback.format_tb(etb)
            self.set_status(self._SERVER_ERROR)
            raise JsonRpcExecError(msgid, method, etype.__name__, value, "\n".join(tb))

    def _process_v2(self, data):
        """
        Process a JSON-RPC V2.x formatted message.

        At the moment we only support messages formatted like V1.x ;-).
        """
        return self._process_v1(data)
