
try:
    import trace
except ImportError:
    pass
else:
    trace._warn = lambda *args: None   # workaround for http://bugs.python.org/issue17143 (PY-8706)

from _pydevd_bundle.pydevd_comm import CMD_SIGNATURE_CALL_TRACE, NetCommand
from _pydevd_bundle import pydevd_vars
from _pydevd_bundle.pydevd_constants import xrange
from _pydevd_bundle import pydevd_utils
from _pydevd_bundle.pydevd_utils import get_clsname_for_code

class Signature(object):
    def __init__(self, file, name):
        self.file = file
        self.name = name
        self.args = []
        self.args_str = []

    def add_arg(self, name, type):
        self.args.append((name, type))
        self.args_str.append("%s:%s"%(name, type))

    def __str__(self):
        return "%s %s(%s)"%(self.file, self.name, ", ".join(self.args_str))


class SignatureFactory(object):
    def __init__(self):
        self._caller_cache = {}
        self._ignore_module_name = ('__main__', '__builtin__', 'builtins')

    def is_in_scope(self, filename):
        return not pydevd_utils.not_in_project_roots(filename)

    def create_signature(self, frame):
        try:
            code = frame.f_code
            locals = frame.f_locals
            filename, modulename, funcname = self.file_module_function_of(frame)
            res = Signature(filename, funcname)
            for i in xrange(0, code.co_argcount):
                name = code.co_varnames[i]
                tp = type(locals[name])
                class_name = tp.__name__
                if class_name == 'instance':  # old-style classes
                    tp = locals[name].__class__
                    class_name = tp.__name__

                if hasattr(tp, '__module__') and tp.__module__ and tp.__module__ not in self._ignore_module_name:
                    class_name = "%s.%s"%(tp.__module__, class_name)

                res.add_arg(name, class_name)
            return res
        except:
            import traceback
            traceback.print_exc()


    def file_module_function_of(self, frame): #this code is take from trace module and fixed to work with new-style classes
        code = frame.f_code
        filename = code.co_filename
        if filename:
            modulename = trace.modname(filename)
        else:
            modulename = None

        funcname = code.co_name
        clsname = None
        if code in self._caller_cache:
            if self._caller_cache[code] is not None:
                clsname = self._caller_cache[code]
        else:
            self._caller_cache[code] = None
            clsname = get_clsname_for_code(code, frame)
            if clsname is not None:
                # cache the result - assumption is that new.* is
                # not called later to disturb this relationship
                # _caller_cache could be flushed if functions in
                # the new module get called.
                self._caller_cache[code] = clsname

        if clsname is not None:
            funcname = "%s.%s" % (clsname, funcname)

        return filename, modulename, funcname

def create_signature_message(signature):
    cmdTextList = ["<xml>"]

    cmdTextList.append('<call_signature file="%s" name="%s">' % (pydevd_vars.make_valid_xml_value(signature.file), pydevd_vars.make_valid_xml_value(signature.name)))

    for arg in signature.args:
        cmdTextList.append('<arg name="%s" type="%s"></arg>' % (pydevd_vars.make_valid_xml_value(arg[0]), pydevd_vars.make_valid_xml_value(arg[1])))

    cmdTextList.append("</call_signature></xml>")
    cmdText = ''.join(cmdTextList)
    return NetCommand(CMD_SIGNATURE_CALL_TRACE, 0, cmdText)

def send_signature_call_trace(dbg, frame, filename):
    if dbg.signature_factory.is_in_scope(filename):
        dbg.writer.add_command(create_signature_message(dbg.signature_factory.create_signature(frame)))



