import pyjd # dummy in pyjs

from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.JSONService import JSONProxy

class JSONRPCExample:
    def onModuleLoad(self):
        self.TEXT_WAITING = "Waiting for response..."
        self.TEXT_ERROR = "Server Error"
        self.METHOD_HELLO = "hello"

        self.methods = [self.METHOD_HELLO]

        self.remote = JSONProxy("../api", ["hello"])

        self.status=Label()
        self.text_area = TextArea()
        self.text_area.setText("""{'Test'} [\"String\"]
\tTest Tab
Test Newline\n
after newline
""" + r"""Literal String:
{'Test'} [\"String\"]
""")
        self.text_area.setCharacterWidth(80)
        self.text_area.setVisibleLines(8)

        self.method_list = ListBox()
        self.method_list.setName("hello")
        self.method_list.setVisibleItemCount(1)
        for method in self.methods:
            self.method_list.addItem(method)
        self.method_list.setSelectedIndex(0)

        method_panel = HorizontalPanel()
        method_panel.add(HTML("Remote string method to call: "))
        method_panel.add(self.method_list)
        method_panel.setSpacing(8)

        self.button_send = Button("Send", self)

        buttons = HorizontalPanel()
        buttons.add(self.button_send)
        buttons.setSpacing(8)

        info = """<h2>JSON-RPC Example</h2>
        <p>This example demonstrates the calling of server services with
           <a href="http://json-rpc.org/">JSON-RPC</a>.
        </p>
        <p>Enter some text below, and press a button to send the text
           to an Echo service on your server. An echo service simply sends the exact same text back that it receives.
           </p>"""

        panel = VerticalPanel()
        panel.add(HTML(info))
        panel.add(self.text_area)
        panel.add(method_panel)
        panel.add(buttons)
        panel.add(self.status)

        RootPanel().add(panel)

    def onClick(self, sender):
        self.status.setText(self.TEXT_WAITING)
        method = self.methods[self.method_list.getSelectedIndex()]
        text = self.text_area.getText()

        # demonstrate proxy & callMethod()
        if method == self.METHOD_HELLO:
            id = self.remote.hello(text, self)

    def onRemoteResponse(self, response, request_info):
        self.status.setText(response)

    def onRemoteError(self, code, errobj, request_info):
        # onRemoteError gets the HTTP error code or 0 and
        # errobj is an jsonrpc 2.0 error dict:
        #     {
        #       'code': jsonrpc-error-code (integer) ,
        #       'message': jsonrpc-error-message (string) ,
        #       'data' : extra-error-data
        #     }
        message = errobj['message']
        if code != 0:
            self.status.setText("HTTP error %d: %s" %
                                (code, message))
        else:
            code = errobj['code']
            self.status.setText("JSONRPC Error %s: %s" %
                                (code, message))


if __name__ == '__main__':
    # for pyjd, set up a web server and load the HTML from there:
    # this convinces the browser engine that the AJAX will be loaded
    # from the same URI base as the URL, it's all a bit messy...
    # Use the second pyjd.setup if you're using apache-php locally
    # as described in the README
    #pyjd.setup("http://127.0.0.1:8000/public/JSONRPCExample.html")
    pyjd.setup("http://127.0.0.1:6767/hello/JSONRPCExample.html")
    app = JSONRPCExample()
    app.onModuleLoad()
    pyjd.run()
