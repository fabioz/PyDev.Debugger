import sys
from pydev_console_utils import BaseInterpreterInterface
import re

# Uncomment to force PyDev standard shell.
# raise ImportError()

try:
    # Versions of IPython from 0.11 were designed to integrate into tools other
    # that IPython's application terminal frontend
    from pydev_ipython_console_011 import PyDevFrontEnd
except ImportError:
    # Prior to 0.11 we need to be clever about the integration, however this leaves
    # many parts of IPython not fully working
    from pydev_ipython_console_010 import PyDevFrontEnd


#=======================================================================================================================
# InterpreterInterface
#=======================================================================================================================
class InterpreterInterface(BaseInterpreterInterface):
    '''
        The methods in this class should be registered in the xml-rpc server.
    '''

    def __init__(self, host, client_port, server):
        BaseInterpreterInterface.__init__(self, server)
        self.client_port = client_port
        self.host = host
        self.interpreter = PyDevFrontEnd(pydev_host=host, pydev_client_port=client_port)
        self._input_error_printed = False


    def doAddExec(self, line):
        return bool(self.interpreter.addExec(line))


    def getNamespace(self):
        return self.interpreter.getNamespace()


    def getCompletions(self, text, act_tok):
        return self.interpreter.getCompletions(text, act_tok)

    def close(self):
        sys.exit(0)

