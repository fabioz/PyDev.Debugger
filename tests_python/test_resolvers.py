from _pydevd_bundle.pydevd_resolver import DictResolver
from tests_python.debug_constants import IS_PY2


def test_dict_resolver():
    dict_resolver = DictResolver()
    dct = {(1, 2): 2, u'22': 22}
    contents_debug_adapter_protocol = dict_resolver.get_contents_debug_adapter_protocol(dct)
    if IS_PY2:
        assert contents_debug_adapter_protocol == [
            ('(1, 2)', 2, '[(1, 2)]'), (u"u'22'", 22, u"[u'22']"), ('__len__', 2, '.__len__()')]
    else:
        assert contents_debug_adapter_protocol == [
            ("'22'", 22, "['22']"), ('(1, 2)', 2, '[(1, 2)]'), ('__len__', 2, '.__len__()')]
