#!/usr/bin/env python

from brubeck.request_handling import Brubeck
from brubeck.connections import Mongrel2Connection
from brubeck.jsonrpc import JsonRpcHandler, embed_methods, method


@embed_methods
class DemoJsonHandler(JsonRpcHandler):
    @method
    def hello(self, name):
        if name == "":
            name = "there"
        return "Hello {0}".format(name)

config = {
    "msg_conn": Mongrel2Connection("tcp://127.0.0.1:9997", "tcp://127.0.0.1:9996"),
    "handler_tuples": [
        ("/api", DemoJsonHandler)
    ]
}
app = Brubeck(**config)
app.run()
