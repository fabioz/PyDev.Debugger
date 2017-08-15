from _pydev_bundle import pydev_log
import traceback
from _pydevd_bundle import pydevd_extension_utils
from _pydevd_bundle import pydevd_resolver
import sys
from _pydevd_bundle.pydevd_constants import dict_iter_items, dict_keys, IS_PY3K, \
    MAXIMUM_VARIABLE_REPRESENTATION_SIZE, RETURN_VALUES_DICT
from _pydevd_bundle.pydevd_extension_api import TypeResolveProvider, StrPresentationProvider
try:
    import types
    frame_type = types.FrameType
except:
    frame_type = None


def make_valid_xml_value(s):
    return s.replace("&", "&amp;").replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class _TranslatorBuilder:
    _always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                    'abcdefghijklmnopqrstuvwxyz'
                    '0123456789' '_.-~')

    _translation_map = {}
    for i, c in zip(range(256), bytes(bytearray(range(256)))):
        _translation_map[c] = chr(i) if (i < 128 and chr(i) in _always_safe) else '%{0:02X}'.format(i)

    def __init__(self):
        self.translation_map = self._translation_map.copy()

    def make_safe(self, safe):
        safe = safe.encode('utf-8')
        translation_map = self.translation_map
        for c in bytes(safe):
            translation_map[c] = chr(c) if IS_PY3K else c
        return self

    def add_translations(self, translations):
        translation_map = self.translation_map
        for c in dict_keys(translations):
            key = c.encode('utf-8')[0]
            translation_map[key] = translations[c]
        return self

    def build(self):
        replace_dict = self.translation_map.copy()
        safe =[]
        for i, c in zip(range(256), bytes(bytearray(range(256)))):
            if replace_dict[c] == chr(i):
                safe.append(chr(i))
        safe_chars = ''.join(safe)
        is_py3k = IS_PY3K

        def translator(in_str):
            """

            :type in_str: str
            """
            if not in_str.rstrip(safe_chars):
                if is_py3k:
                    return in_str
                return in_str if isinstance(in_str, str) else in_str.encode('utf-8')
            if not isinstance(in_str, bytes):
                in_str = in_str.encode('utf-8')

            return ''.join(map(replace_dict.__getitem__, in_str))

        return translator

_xml_escape_dict = {'"': '&quot;', '>' : '&lt;'}
xml_quote = _TranslatorBuilder().make_safe("'/>_= '\t").add_translations(_xml_escape_dict).build()
#version that keeps tab for backwards compat
xml_quote_2 = _TranslatorBuilder().make_safe("'/>_= '").add_translations(_xml_escape_dict).build()



class ExceptionOnEvaluate:
    def __init__(self, result):
        self.result = result

_IS_JYTHON = sys.platform.startswith("java")

def _create_default_type_map():
    if not _IS_JYTHON:
        default_type_map = [
            # None means that it should not be treated as a compound variable
    
            # isintance does not accept a tuple on some versions of python, so, we must declare it expanded
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
            default_type_map.append((long, None))  # @UndefinedVariable
        except:
            pass #not available on all python versions
    
        try:
            default_type_map.append((unicode, None))  # @UndefinedVariable
        except:
            pass #not available on all python versions
    
        try:
            default_type_map.append((set, pydevd_resolver.setResolver))
        except:
            pass #not available on all python versions
    
        try:
            default_type_map.append((frozenset, pydevd_resolver.setResolver))
        except:
            pass #not available on all python versions
    
        try:
            from django.utils.datastructures import MultiValueDict
            default_type_map.insert(0, (MultiValueDict, pydevd_resolver.multiValueDictResolver))
            #we should put it before dict
        except:
            pass  #django may not be installed
    
        try:
            from django.forms import BaseForm
            default_type_map.insert(0, (BaseForm, pydevd_resolver.djangoFormResolver))
            #we should put it before instance resolver
        except:
            pass  #django may not be installed
    
        try:
            from collections import deque
            default_type_map.append((deque, pydevd_resolver.dequeResolver))
        except:
            pass
    
        if frame_type is not None:
            default_type_map.append((frame_type, pydevd_resolver.frameResolver))
    
    else:
        from org.python import core  # @UnresolvedImport
        default_type_map = [
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
            # Jython 2.5b3 removed it.
            default_type_map.append((core.PyJavaInstance, pydevd_resolver.instanceResolver))

    return default_type_map

class TypeResolveHandler(object):
    
    NO_PROVIDER = [] # Sentinel value (any mutable object to be used as a constant would be valid).

    def __init__(self):
        # Note: don't initialize with the types we already know about so that the extensions can override
        # the default resolvers that are already available if they want.
        self._type_to_resolver_cache = {}
        self._type_to_str_provider_cache = {}
        self._initialized = False
        
    def _initialize(self):
        self._default_type_map = _create_default_type_map()
        self._resolve_providers = pydevd_extension_utils.extensions_of_type(TypeResolveProvider)
        self._str_providers = pydevd_extension_utils.extensions_of_type(StrPresentationProvider)
        self._initialized = True

    def get_type(self,o):
        try:
            try:
                # Faster than type(o) as we don't need the function call.
                type_object = o.__class__
            except:
                # Not all objects have __class__ (i.e.: there are bad bindings around).
                type_object = type(o)
                
            type_name = type_object.__name__
        except:
            # This happens for org.python.core.InitModule
            return 'Unable to get Type', 'Unable to get Type', None
        
        return self._get_type(o, type_object, type_name)

    def _get_type(self, o, type_object, type_name):
        resolver = self._type_to_resolver_cache.get(type_object)
        if resolver is not None:
            return type_object, type_name, resolver
        
        if not self._initialized:
            self._initialize()
            
        try:
            for resolver in self._resolve_providers:
                if resolver.can_provide(type_object, type_name):
                    # Cache it
                    self._type_to_resolver_cache[type_object] = resolver
                    return type_object, type_name, resolver

            for t in self._default_type_map:
                if isinstance(o, t[0]):
                    # Cache it
                    resolver = t[1]
                    self._type_to_resolver_cache[type_object] = resolver
                    return (type_object, type_name, resolver)
        except:
            traceback.print_exc()

        # No match return default (and cache it).
        resolver = pydevd_resolver.defaultResolver
        self._type_to_resolver_cache[type_object] = resolver
        return type_object, type_name, resolver
    
    if _IS_JYTHON:
        _base_get_type = _get_type
        
        def _get_type(self, o, type_object, type_name):
            if type_name == 'org.python.core.PyJavaInstance':
                return type_object, type_name, pydevd_resolver.instanceResolver

            if type_name == 'org.python.core.PyArray':
                return type_object, type_name, pydevd_resolver.jyArrayResolver
            
            return self._base_get_type(o, type_name, type_name)


    def str_from_providers(self,  o, type_object, type_name):
        provider = self._type_to_str_provider_cache.get(type_object)
        
        if provider is self.NO_PROVIDER:
            return None
        
        if provider is not None:
            return provider
        
        if not self._initialized:
            self._initialize()
        
        for provider in self._str_providers:
            if provider.can_provide(type_object, type_name):
                self._type_to_str_provider_cache[type_object] = provider
                return provider.get_str(o)
            
        self._type_to_str_provider_cache[type_object] = self.NO_PROVIDER
        return None


_TYPE_RESOLVE_HANDLER = TypeResolveHandler()

""" 
def get_type(o):
    Receives object and returns a triple (typeObject, typeString, resolver).
    
    resolver != None means that variable is a container, and should be displayed as a hierarchy.
    
    Use the resolver to get its attributes.
    
    All container objects should have a resolver.
"""
get_type = _TYPE_RESOLVE_HANDLER.get_type

_str_from_providers = _TYPE_RESOLVE_HANDLER.str_from_providers


def return_values_from_dict_to_xml(return_dict):
    res = ""
    for name, val in dict_iter_items(return_dict):
        res += var_to_xml(val, name, additional_in_xml=' isRetVal="True"')
    return res


def frame_vars_to_xml(frame_f_locals, hidden_ns=None):
    """ dumps frame variables to XML
    <var name="var_name" scope="local" type="type" value="value"/>
    """
    xml = ""

    keys = dict_keys(frame_f_locals)
    if hasattr(keys, 'sort'):
        keys.sort() #Python 3.0 does not have it
    else:
        keys = sorted(keys) #Jython 2.1 does not have it
        
    return_values_xml = ''

    for k in keys:
        try:
            v = frame_f_locals[k]
            if k == RETURN_VALUES_DICT:
                for name, val in dict_iter_items(v):
                    return_values_xml += var_to_xml(val, name, additional_in_xml=' isRetVal="True"')

            else:
                if hidden_ns is not None and k in hidden_ns:
                    xml += var_to_xml(v, str(k), additional_in_xml=' isIPythonHidden="True"')
                else:
                    xml += var_to_xml(v, str(k))
        except Exception:
            traceback.print_exc()
            pydev_log.error("Unexpected error, recovered safely.\n")

    # Show return values as the first entry.
    return return_values_xml + xml


def var_to_xml(val, name, doTrim=True, additional_in_xml=''):
    """ single variable or dictionary to xml representation """

    try:
        # This should be faster than isinstance (but we have to protect against not having a '__class__' attribute).
        is_exception_on_eval = val.__class__ == ExceptionOnEvaluate
    except:
        is_exception_on_eval = False

    if is_exception_on_eval:
        v = val.result
    else:
        v = val

    _type, typeName, resolver = get_type(v)
    type_qualifier = getattr(_type, "__module__", "")
    try:
        str_from_provider = _str_from_providers(v, _type, typeName)
        if str_from_provider is not None:
            value = str_from_provider
        elif hasattr(v, '__class__'):
            if v.__class__ == frame_type:
                value = pydevd_resolver.frameResolver.get_frame_name(v)

            elif v.__class__ in (list, tuple):
                if len(v) > 300:
                    value = '%s: %s' % (str(v.__class__), '<Too big to print. Len: %s>' % (len(v),))
                else:
                    value = '%s: %s' % (str(v.__class__), v)
            else:
                try:
                    cName = str(v.__class__)
                    if cName.find('.') != -1:
                        cName = cName.split('.')[-1]

                    elif cName.find("'") != -1: #does not have '.' (could be something like <type 'int'>)
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

    xml = '<var name="%s" type="%s" ' % (xml_quote_2(name), make_valid_xml_value(typeName))

    if type_qualifier:
        xml_qualifier = 'qualifier="%s"' % make_valid_xml_value(type_qualifier)
    else:
        xml_qualifier = ''

    if value:
        #cannot be too big... communication may not handle it.
        if len(value) > MAXIMUM_VARIABLE_REPRESENTATION_SIZE and doTrim:
            value = value[0:MAXIMUM_VARIABLE_REPRESENTATION_SIZE]
            value += '...'
        xml_value = ' value="%s"' % (xml_quote_2(value))
    else:
        xml_value = ''

    if is_exception_on_eval:
        xml_container = ' isErrorOnEval="True"'
    else:
        if resolver is not None:
            xml_container = ' isContainer="True"'
        else:
            xml_container = ''

    return ''.join((xml, xml_qualifier, xml_value, xml_container, additional_in_xml, ' />\n'))

