from pydev_imports import xmlrpclib
import sys

#=======================================================================================================================
# Null
#=======================================================================================================================
class Null:
    """
    Gotten from: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/68205
    """

    def __init__(self, *args, **kwargs):
        return None

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, mname):
        return self

    def __setattr__(self, name, value):
        return self

    def __delattr__(self, name):
        return self

    def __repr__(self):
        return "<Null>"

    def __str__(self):
        return "Null"
    
    def __len__(self):
        return 0
    
    def __getitem__(self):
        return self
    
    def __setitem__(self, *args, **kwargs):
        pass
    
    def write(self, *args, **kwargs):
        pass
    
    def __nonzero__(self):
        return 0
    
    

#=======================================================================================================================
# BaseStdIn
#=======================================================================================================================
class BaseStdIn:
    
    def __init__(self, *args, **kwargs):
        try:
            self.encoding = sys.stdin.encoding
        except:
            #Not sure if it's available in all Python versions...
            pass
    
    def readline(self, *args, **kwargs):
        #sys.stderr.write('Cannot readline out of the console evaluation\n') -- don't show anything
        #This could happen if the user had done input('enter number).<-- upon entering this, that message would appear,
        #which is not something we want.
        return '\n'
    
    def isatty(self):    
        return False #not really a file
        
    def write(self, *args, **kwargs):
        pass #not available StdIn (but it can be expected to be in the stream interface)
        
    def flush(self, *args, **kwargs):
        pass #not available StdIn (but it can be expected to be in the stream interface)
       
    def read(self, *args, **kwargs):
        #in the interactive interpreter, a read and a readline are the same.
        return self.readline()
    
#=======================================================================================================================
# StdIn
#=======================================================================================================================
class StdIn(BaseStdIn):
    '''
        Object to be added to stdin (to emulate it as non-blocking while the next line arrives)
    '''
    
    def __init__(self, interpreter, host, client_port):
        BaseStdIn.__init__(self)
        self.interpreter = interpreter
        self.client_port = client_port
        self.host = host
    
    def readline(self, *args, **kwargs):
        #Ok, callback into the client to get the new input
        server = xmlrpclib.Server('http://%s:%s' % (self.host, self.client_port))
        requested_input = server.RequestInput()
        if not requested_input:
            return '\n' #Yes, a readline must return something (otherwise we can get an EOFError on the input() call).
        return requested_input
    
    
    

#=======================================================================================================================
# BaseInterpreterInterface
#=======================================================================================================================
class BaseInterpreterInterface:
    def __init__(self, server):
        self.server = server
    
    def createStdIn(self):
        return StdIn(self, self.host, self.client_port)

    def addExec(self, line):
        #f_opened = open('c:/temp/a.txt', 'a')
        #f_opened.write(line+'\n')
        original_in = sys.stdin
        try:
            help = None
            if 'pydoc' in sys.modules:
                pydoc = sys.modules['pydoc'] #Don't import it if it still is not there.
                
                
                if hasattr(pydoc, 'help'):
                    #You never know how will the API be changed, so, let's code defensively here
                    help = pydoc.help
                    if not hasattr(help, 'input'):
                        help = None
        except:
            #Just ignore any error here
            pass
            
        more = False
        try:
            sys.stdin = self.createStdIn()
            try:
                if help is not None:
                    #This will enable the help() function to work.
                    try:
                        try:
                            help.input = sys.stdin 
                        except AttributeError:
                            help._input = sys.stdin 
                    except:
                        help = None
                        if not self._input_error_printed:
                            self._input_error_printed = True
                            sys.stderr.write('\nError when trying to update pydoc.help.input\n')
                            sys.stderr.write('(help() may not work -- please report this as a bug in the pydev bugtracker).\n\n')
                            import traceback;traceback.print_exc()
                
                try:
                    more = self.doAddExec(line)
                finally:
                    if help is not None:
                        try:
                            try:
                                help.input = original_in
                            except AttributeError:
                                help._input = original_in
                        except:
                            pass
                        
            finally:
                sys.stdin = original_in
        except SystemExit:
            raise
        except:
            import traceback;traceback.print_exc()
        
        #it's always false at this point
        need_input = False
        return more, need_input
    
    
    def doAddExec(self, line):
        '''
        Subclasses should override.
        
        @return: more (True if more input is needed to complete the statement and False if the statement is complete).
        '''
        raise NotImplementedError()
    
    
    def getNamespace(self):
        '''
        Subclasses should override.
        
        @return: dict with namespace.
        '''
        raise NotImplementedError()
    
        
    
    def getDescription(self, text):
        try:
            obj = None
            if '.' not in text:
                try:
                    obj = self.getNamespace()[text]
                except KeyError:
                    return ''
                    
            else:
                try:
                    splitted = text.split('.')
                    obj = self.getNamespace()[splitted[0]]
                    for t in splitted[1:]:
                        obj = getattr(obj, t)
                except:
                    return ''
                    
                
            if obj is not None:
                try:
                    if sys.platform.startswith("java"):
                        #Jython
                        doc = obj.__doc__
                        if doc is not None:
                            return doc
                        
                        import _pydev_jy_imports_tipper
                        is_method, infos = _pydev_jy_imports_tipper.ismethod(obj)
                        ret = ''
                        if is_method:
                            for info in infos:
                                ret += info.getAsDoc()
                            return ret
                            
                    else:
                        #Python and Iron Python
                        import inspect #@UnresolvedImport
                        doc = inspect.getdoc(obj) 
                        if doc is not None:
                            return doc
                except:
                    pass
                    
            try:
                #if no attempt succeeded, try to return repr()... 
                return repr(obj)
            except:
                try:
                    #otherwise the class 
                    return str(obj.__class__)
                except:
                    #if all fails, go to an empty string 
                    return ''
        except:
            import traceback;traceback.print_exc()
            return ''


    def _findFrame(self, thread_id, frame_id):
        '''
        Used to show console with variables connection.
        Always return a frame where the locals map to our internal namespace.
        '''
        VIRTUAL_FRAME_ID = "1" # matches PyStackFrameConsole.java
        VIRTUAL_CONSOLE_ID = "console_main" # matches PyThreadConsole.java
        if thread_id == VIRTUAL_CONSOLE_ID and frame_id == VIRTUAL_FRAME_ID:
            f = FakeFrame()
            f.f_globals = {} #As globals=locals here, let's simply let it empty (and save a bit of network traffic).
            f.f_locals = self.getNamespace()
            return f
        else:
            return self.orig_findFrame(thread_id, frame_id)
        
    def connectToDebugger(self, debuggerPort):
        '''
        Used to show console with variables connection.
        Mainly, monkey-patches things in the debugger structure so that the debugger protocol works.
        '''
        try:
            # Try to import the packages needed to attach the debugger
            import pydevd
            import pydevd_vars
            import threading
        except:
            # This happens on Jython embedded in host eclipse 
            import traceback;traceback.print_exc()
            return ('pydevd is not available, cannot connect',)
        
        import pydev_localhost
        threading.currentThread().__pydevd_id__ = "console_main"
        
        self.orig_findFrame = pydevd_vars.findFrame
        pydevd_vars.findFrame = self._findFrame
        
        self.debugger = pydevd.PyDB()
        try:
            self.debugger.connect(pydev_localhost.get_localhost(), debuggerPort)
            self.debugger.prepareToRun()
        except:
            return ('Failed to connect to target debugger.')
        
        # Register to process commands when idle
        self.debugrunning = False
        try:
            self.server.setDebugHook(self.debugger.processInternalCommands)
        except:
            return ('Version of Python does not support debuggable Interactive Console.')
        
        return ('connect complete',)
        
    def hello(self, input_str):
        # Don't care what the input string is
        return ("Hello eclipse",)
    
    def enableGui(self, guiname):
        ''' Enable the GUI specified in guiname (see inputhook for list).
            As with IPython, enabling multiple GUIs isn't an error, but
            only the last one's main loop runs and it may not work
        '''
        from pydev_versioncheck import versionok_for_gui
        if versionok_for_gui():
            try:
                from pydev_ipython.inputhook import enable_gui
                enable_gui(guiname)
            except:
                sys.stderr.write("Failed to enable GUI event loop integration for '%s'\n" % guiname)
                import traceback;traceback.print_exc()
        elif guiname not in ['none', '', None]:
            # Only print a warning if the guiname was going to do something
            sys.stderr.write("PyDev console: Python version does not support GUI event loop integration for '%s'\n" % guiname)
        # Return value does not matter, so return back what was sent
        return guiname

#=======================================================================================================================
# FakeFrame
#=======================================================================================================================
class FakeFrame:
    '''
    Used to show console with variables connection.
    A class to be used as a mock of a frame.
    '''
