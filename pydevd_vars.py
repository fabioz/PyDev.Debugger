""" pydevd_vars deals with variables:
    resolution/conversion to XML.
"""
from pydevd_constants import *  #@UnusedWildImport
from types import *  #@UnusedWildImport
from pydevd_custom_frames import getCustomFrame
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import sys  #@Reimport
import threading
import pydevd_resolver
import traceback
import pydevd_save_locals
from pydev_imports import Exec, quote, execfile

try:
    import types
    frame_type = types.FrameType
except:
    frame_type = None


#-------------------------------------------------------------------------- defining true and false for earlier versions

try:
    __setFalse = False
except:
    import __builtin__
    setattr(__builtin__, 'True', 1)
    setattr(__builtin__, 'False', 0)

#------------------------------------------------------------------------------------------------------ class for errors

class VariableError(RuntimeError):pass
class FrameNotFoundError(RuntimeError):pass


#------------------------------------------------------------------------------------------------------ resolvers in map

if not sys.platform.startswith("java"):
    typeMap = [
        #None means that it should not be treated as a compound variable

        #isintance does not accept a tuple on some versions of python, so, we must declare it expanded
        (type(None), None,),
        (int, None),
        (float, None),
        (complex, None),
        (str, None),
        (tuple, pydevd_resolver.tupleResolver),
        (list, pydevd_resolver.tupleResolver),
        (dict, pydevd_resolver.dictResolver),
    ]

    try:
        typeMap.append((long, None))
    except:
        pass  #not available on all python versions

    try:
        typeMap.append((unicode, None))
    except:
        pass  #not available on all python versions

    try:
        typeMap.append((set, pydevd_resolver.setResolver))
    except:
        pass  #not available on all python versions

    try:
        typeMap.append((frozenset, pydevd_resolver.setResolver))
    except:
        pass  #not available on all python versions

    try:
        import numpy
        typeMap.append((numpy.ndarray, pydevd_resolver.ndarrayResolver))
    except:
        pass  #numpy may not be installed

    if frame_type is not None:
        typeMap.append((frame_type, pydevd_resolver.frameResolver))


else:  #platform is java
    from org.python import core  #@UnresolvedImport
    typeMap = [
        (core.PyNone, None),
        (core.PyInteger, None),
        (core.PyLong, None),
        (core.PyFloat, None),
        (core.PyComplex, None),
        (core.PyString, None),
        (core.PyTuple, pydevd_resolver.tupleResolver),
        (core.PyList, pydevd_resolver.tupleResolver),
        (core.PyDictionary, pydevd_resolver.dictResolver),
        (core.PyStringMap, pydevd_resolver.dictResolver),
    ]

    if hasattr(core, 'PyJavaInstance'):
        #Jython 2.5b3 removed it.
        typeMap.append((core.PyJavaInstance, pydevd_resolver.instanceResolver))


def getType(o):
    """ returns a triple (typeObject, typeString, resolver
        resolver != None means that variable is a container,
        and should be displayed as a hierarchy.
        Use the resolver to get its attributes.

        All container objects should have a resolver.
    """

    try:
        type_object = type(o)
        type_name = type_object.__name__
    except:
        #This happens for org.python.core.InitModule
        return 'Unable to get Type', 'Unable to get Type', None

    try:

        if type_name == 'org.python.core.PyJavaInstance':
            return (type_object, type_name, pydevd_resolver.instanceResolver)

        if type_name == 'org.python.core.PyArray':
            return (type_object, type_name, pydevd_resolver.jyArrayResolver)

        for t in typeMap:
            if isinstance(o, t[0]):
                return (type_object, type_name, t[1])
    except:
        traceback.print_exc()

    #no match return default
    return (type_object, type_name, pydevd_resolver.defaultResolver)


def makeValidXmlValue(s):
    return s.replace("&", "&amp;").replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def varToXML(v, name, additionalInXml=''):
    """ single variable or dictionary to xml representation """
    type, typeName, resolver = getType(v)

    try:
        if hasattr(v, '__class__'):
            if v.__class__ == frame_type:
                value = pydevd_resolver.frameResolver.getFrameName(v)
            else:
                try:
                    cName = str(v.__class__)
                    if cName.find('.') != -1:
                        cName = cName.split('.')[-1]

                    elif cName.find("'") != -1:  #does not have '.' (could be something like <type 'int'>)
                        cName = cName[cName.index("'") + 1:]

                    if cName.endswith("'>"):
                        cName = cName[:-2]
                except:
                    cName = str(v.__class__)
                value = '%s: %s' % (cName, v)
        else:
            value = str(v)
    except:
        try:
            value = repr(v)
        except:
            value = 'Unable to get repr for %s' % v.__class__

    xml = '<var name="%s" type="%s"' % (makeValidXmlValue(name), makeValidXmlValue(typeName))

    if value:
        #cannot be too big... communication may not handle it.
        if len(value) > MAXIMUM_VARIABLE_REPRESENTATION_SIZE:
            value = value[0:MAXIMUM_VARIABLE_REPRESENTATION_SIZE]
            value += '...'

        #fix to work with unicode values
        try:
            if not IS_PY3K:
                if isinstance(value, unicode):
                    value = value.encode('utf-8')
            else:
                if isinstance(value, bytes):
                    value = value.encode('utf-8')
        except TypeError:  #in java, unicode is a function
            pass

        xmlValue = ' value="%s"' % (makeValidXmlValue(quote(value, '/>_= \t')))
    else:
        xmlValue = ''

    if resolver is not None:
        xmlCont = ' isContainer="True"'
    else:
        xmlCont = ''

    return ''.join((xml, xmlValue, xmlCont, additionalInXml, ' />\n'))


if USE_PSYCO_OPTIMIZATION:
    try:
        import psyco
        varToXML = psyco.proxy(varToXML)
    except ImportError:
        if hasattr(sys, 'exc_clear'):  #jython does not have it
            sys.exc_clear()  #don't keep the traceback -- clients don't want to see it


def frameVarsToXML(frame):
    """ dumps frame variables to XML
    <var name="var_name" scope="local" type="type" value="value"/>
    """
    xml = ""

    keys = frame.f_locals.keys()
    if hasattr(keys, 'sort'):
        keys.sort()  #Python 3.0 does not have it
    else:
        keys = sorted(keys)  #Jython 2.1 does not have it

    for k in keys:
        try:
            v = frame.f_locals[k]
            xml += varToXML(v, str(k))
        except Exception:
            traceback.print_exc()
            sys.stderr.write("Unexpected error, recovered safely.\n")
    return xml

def iterFrames(initialFrame):
    '''NO-YIELD VERSION: Iterates through all the frames starting at the specified frame (which will be the first returned item)'''
    #cannot use yield
    frames = []

    while initialFrame is not None:
        frames.append(initialFrame)
        initialFrame = initialFrame.f_back

    return frames

def dumpFrames(thread_id):
    sys.stdout.write('dumping frames\n')
    if thread_id != GetThreadId(threading.currentThread()) :
        raise VariableError("findFrame: must execute on same thread")

    curFrame = GetFrame()
    for frame in iterFrames(curFrame):
        sys.stdout.write('%s\n' % id(frame))


#===============================================================================
# AdditionalFramesContainer
#===============================================================================
class AdditionalFramesContainer:
    lock = threading.Lock()
    additional_frames = {}  #dict of dicts


def addAdditionalFrameById(thread_id, frames_by_id):
    AdditionalFramesContainer.additional_frames[thread_id] = frames_by_id


def removeAdditionalFrameById(thread_id):
    del AdditionalFramesContainer.additional_frames[thread_id]




def findFrame(thread_id, frame_id):
    """ returns a frame on the thread that has a given frame_id """
    try:
        curr_thread_id = GetThreadId(threading.currentThread())
        if thread_id != curr_thread_id :
            try:
                return getCustomFrame(thread_id, frame_id)  #I.e.: thread_id could be a stackless frame id + thread_id.
            except:
                pass

            raise VariableError("findFrame: must execute on same thread (%s != %s)" % (thread_id, curr_thread_id))

        lookingFor = int(frame_id)

        if AdditionalFramesContainer.additional_frames:
            if DictContains(AdditionalFramesContainer.additional_frames, thread_id):
                frame = AdditionalFramesContainer.additional_frames[thread_id].get(lookingFor)
                if frame is not None:
                    return frame

        curFrame = GetFrame()
        if frame_id == "*":
            return curFrame  # any frame is specified with "*"

        frameFound = None

        for frame in iterFrames(curFrame):
            if lookingFor == id(frame):
                frameFound = frame
                del frame
                break

            del frame

        #Important: python can hold a reference to the frame from the current context
        #if an exception is raised, so, if we don't explicitly add those deletes
        #we might have those variables living much more than we'd want to.

        #I.e.: sys.exc_info holding reference to frame that raises exception (so, other places
        #need to call sys.exc_clear())
        del curFrame

        if frameFound is None:
            msgFrames = ''
            i = 0

            for frame in iterFrames(GetFrame()):
                i += 1
                msgFrames += str(id(frame))
                if i % 5 == 0:
                    msgFrames += '\n'
                else:
                    msgFrames += '  -  '

            errMsg = '''findFrame: frame not found.
    Looking for thread_id:%s, frame_id:%s
    Current     thread_id:%s, available frames:
    %s\n
    ''' % (thread_id, lookingFor, curr_thread_id, msgFrames)

            sys.stderr.write(errMsg)
            return None

        return frameFound
    except:
        import traceback
        traceback.print_exc()
        return None


def getVariable(thread_id, frame_id, scope, attrs):
    """
    returns the value of a variable

    :scope: can be BY_ID, EXPRESSION, GLOBAL, LOCAL, FRAME

    BY_ID means we'll traverse the list of all objects alive to get the object.

    :attrs: after reaching the proper scope, we have to get the attributes until we find
            the proper location (i.e.: obj\tattr1\tattr2)

    :note: when BY_ID is used, the frame_id is considered the id of the object to find and
           not the frame (as we don't care about the frame in this case).
    """
    if scope == 'BY_ID':
        if thread_id != GetThreadId(threading.currentThread()) :
            raise VariableError("getVariable: must execute on same thread")

        try:
            import gc
            objects = gc.get_objects()
        except:
            pass  #Not all python variants have it.
        else:
            frame_id = int(frame_id)
            for var in objects:
                if id(var) == frame_id:
                    if attrs is not None:
                        attrList = attrs.split('\t')
                        for k in attrList:
                            _type, _typeName, resolver = getType(var)
                            var = resolver.resolve(var, k)

                    return var

        #If it didn't return previously, we coudn't find it by id (i.e.: alrceady garbage collected).
        sys.stderr.write('Unable to find object with id: %s\n' % (frame_id,))
        return None

    frame = findFrame(thread_id, frame_id)
    if frame is None:
        return {}

    if attrs is not None:
        attrList = attrs.split('\t')
    else:
        attrList = []

    if scope == 'EXPRESSION':
        for count in range(len(attrList)):
            if count == 0:
                # An Expression can be in any scope (globals/locals), therefore it needs to evaluated as an expression
                var = evaluateExpression(thread_id, frame_id, attrList[count], False)
            else:
                _type, _typeName, resolver = getType(var)
                var = resolver.resolve(var, attrList[count])
    else:
        if scope == "GLOBAL":
            var = frame.f_globals
            del attrList[0]  # globals are special, and they get a single dummy unused attribute
        else:
            var = frame.f_locals

        for k in attrList:
            _type, _typeName, resolver = getType(var)
            var = resolver.resolve(var, k)

    return var


def resolveCompoundVariable(thread_id, frame_id, scope, attrs):
    """ returns the value of the compound variable as a dictionary"""

    var = getVariable(thread_id, frame_id, scope, attrs)

    try:
        _type, _typeName, resolver = getType(var)
        return resolver.getDictionary(var)
    except:
        sys.stderr.write('Error evaluating: thread_id: %s\nframe_id: %s\nscope: %s\nattrs: %s\n' % (
            thread_id, frame_id, scope, attrs,))
        traceback.print_exc()


def customOperation(thread_id, frame_id, scope, attrs, style, code_or_file, operation_fn_name):
    """
    We'll execute the code_or_file and then search in the namespace the operation_fn_name to execute with the given var.

    code_or_file: either some code (i.e.: from pprint import pprint) or a file to be executed.
    operation_fn_name: the name of the operation to execute after the exec (i.e.: pprint)
    """
    expressionValue = getVariable(thread_id, frame_id, scope, attrs)

    try:
        namespace = {'__name__': '<customOperation>'}
        if style == "EXECFILE":
            namespace['__file__'] = code_or_file
            execfile(code_or_file, namespace, namespace)
        else:  # style == EXEC
            namespace['__file__'] = '<customOperationCode>'
            Exec(code_or_file, namespace, namespace)

        return str(namespace[operation_fn_name](expressionValue))
    except:
        traceback.print_exc()


def evaluateExpression(thread_id, frame_id, expression, doExec):
    '''returns the result of the evaluated expression
    @param doExec: determines if we should do an exec or an eval
    '''
    frame = findFrame(thread_id, frame_id)
    if frame is None:
        return

    expression = str(expression.replace('@LINE@', '\n'))

    #Not using frame.f_globals because of https://sourceforge.net/tracker2/?func=detail&aid=2541355&group_id=85796&atid=577329
    #(Names not resolved in generator expression in method)
    #See message: http://mail.python.org/pipermail/python-list/2009-January/526522.html
    updated_globals = {}
    updated_globals.update(frame.f_globals)
    updated_globals.update(frame.f_locals)  #locals later because it has precedence over the actual globals

    try:

        if doExec:
            try:
                #try to make it an eval (if it is an eval we can print it, otherwise we'll exec it and
                #it will have whatever the user actually did)
                compiled = compile(expression, '<string>', 'eval')
            except:
                Exec(expression, updated_globals, frame.f_locals)
                pydevd_save_locals.save_locals(frame)
            else:
                result = eval(compiled, updated_globals, frame.f_locals)
                if result is not None:  #Only print if it's not None (as python does)
                    sys.stdout.write('%s\n' % (result,))
            return

        else:
            result = None
            try:
                result = eval(expression, updated_globals, frame.f_locals)
            except Exception:
                s = StringIO()
                traceback.print_exc(file=s)
                result = s.getvalue()

                try:
                    try:
                        etype, value, tb = sys.exc_info()
                        result = value
                    finally:
                        etype = value = tb = None
                except:
                    pass

                # Ok, we have the initial error message, but let's see if we're dealing with a name mangling error...
                try:
                    if '__' in expression:
                        # Try to handle '__' name mangling...
                        split = expression.split('.')
                        curr = frame.f_locals.get(split[0])
                        for entry in split[1:]:
                            if entry.startswith('__') and not hasattr(curr, entry):
                                entry = '_%s%s' % (curr.__class__.__name__, entry)
                            curr = getattr(curr, entry)
                            
                        result = curr
                except:
                    pass


            return result
    finally:
        #Should not be kept alive if an exception happens and this frame is kept in the stack.
        del updated_globals
        del frame


def changeAttrExpression(thread_id, frame_id, attr, expression):
    '''Changes some attribute in a given frame.
    @note: it will not (currently) work if we're not in the topmost frame (that's a python
    deficiency -- and it appears that there is no way of making it currently work --
    will probably need some change to the python internals)
    '''
    frame = findFrame(thread_id, frame_id)
    if frame is None:
        return

    try:
        expression = expression.replace('@LINE@', '\n')



        if attr[:7] == "Globals":
            attr = attr[8:]
            if attr in frame.f_globals:
                frame.f_globals[attr] = eval(expression, frame.f_globals, frame.f_locals)
        else:
            if pydevd_save_locals.is_save_locals_available():
                frame.f_locals[attr] = eval(expression, frame.f_globals, frame.f_locals)
                pydevd_save_locals.save_locals(frame)
                return
            
            #default way (only works for changing it in the topmost frame)
            Exec('%s=%s' % (attr, expression), frame.f_globals, frame.f_locals)


    except Exception:
        traceback.print_exc()





