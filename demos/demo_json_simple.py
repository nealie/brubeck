#!/usr/bin/env python

#import os.path
#import sys
#
#sys.path.insert(0, os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../brubeck"))))

from brubeck.request_handling import Brubeck
#from brubeck.connections import Mongrel2Connection
from brubeck.jsonrpc import JsonRpcHandler, embed_methods, method, JsonRpcConnection


@embed_methods
class DemoJsonHandler(JsonRpcHandler):
    @method
    def hello(self, name):
        print "Hello", name
        return "Hello {0}".format(name)

config = {
    "msg_conn": JsonRpcConnection("tcp://127.0.0.1:9997", "tcp://127.0.0.1:9996"),
    "handler_tuples": [
        ("/api", DemoJsonHandler)
    ]
}
app = Brubeck(**config)
app.run()

