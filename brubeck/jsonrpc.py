
import json
import logging
import sys
import traceback

from brubeck.connections import Mongrel2Connection
from brubeck.request import Request
from brubeck.request_handling import MessageHandler, JSONMessageHandler


class JsonRpcError(Exception):
    pass


class MethodNotFoundError(JsonRpcError):
    def __init__(self, id, method):
        self.status = -4
        self.id = id
        self.method = method

    @property
    def message(self):
        return "Method '{0}' not found.".format(self.method)


class MalformedV1RequestError(JsonRpcError):
    def __init__(self, message, key):
        self.status = JsonRpcHandler._DEFAULT_STATUS
        self.msg = message
        self.key = key

    @property
    def message(self):
        return "Malformed message'{0}', key '{1}' not found.".format(self.msg, self.key)


#class JsonRpcV2Error(JsonRpcError):
#    def __init__(self, message):
#        self.status = JsonRpcHandler._DEFAULT_STATUS
#        self.msg = message
#
#    @property
#    def message(self):
#        return "JSON-RPC V2.0 not supported: {0}".format(self.mesmsgsage)


class JsonRpcExecError(JsonRpcError):
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
            # Add to the methods dictionary.
            #cls.methods[name] = method
            cls._method_names.append(name)
    return cls

def method(view):
    """
    Decorator to mark as a JSON-RPC method.
    """
    view._jsonrpc_method = True
    return view


class JsonRpcHandler(MessageHandler):

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
        Generate a dict of bound methods from the method names stored at clas creation time.
        """
        super(JsonRpcHandler, self).__init__(*args, **kwargs)
        self.methods = {}
        for name in self._method_names:
            self.methods[name] = getattr(self, name)

    def __call__(self):
        try:
            #data = self.message.data
            data = self.message.body
            print "Got", repr(data)
            data = json.loads(data)
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

        print repr(result)
        #return json.dumps(result)
        return result

    def _process_v1(self, data):
        """
        Process a JSON-RPC V1.x formatted message.
        """
        try:
            msgid, method, params = data["id"], data["method"], data["params"]
            print "ID", msgid, "Method", method, "Params", params
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



from request import to_bytes

class JsonRpcConnection(Mongrel2Connection):
    """
    """

    def process_message(self, application, message):
        print "process_message", message
        request = Request.parse_msg(message)
        print request
        if request.is_disconnect():
            return
        handler = application.route_message(request)
        response = handler()

        print "Response:", repr(response)
        application.msg_conn.reply(request, json.dumps(response))

    def send(self, uuid, conn_id, msg):
        """Raw send to the given connection ID at the given uuid, mostly used
        internally.
        """
        header = "%s %d:%s," % (uuid, len(str(conn_id)), str(conn_id))
        print "Send:", uuid, conn_id, repr(msg)
        print repr(header + ' ' + to_bytes(msg))
        self.out_sock.send(header + ' ' + to_bytes(msg) + "\n\n")
        print "Sent"

    def reply(self, req, msg):
        """Does a reply based on the given Request object and message.
        """
        print "Reply", req, repr(msg)
        self.send(req.sender, req.conn_id, msg)
