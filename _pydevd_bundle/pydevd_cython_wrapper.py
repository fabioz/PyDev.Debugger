try:
    from _pydevd_bundle.pydevd_cython import trace_dispatch, PyDBAdditionalThreadInfo
except ImportError:
    try:
        import struct
        import sys
        is_python_64bit = (struct.calcsize('P') == 8)
        plat = '32'
        if is_python_64bit:
            plat = '64'

        check_name = '_pydevd_bundle.pydevd_cython_%s_%s%s_%s' % (sys.platform, sys.version_info[0], sys.version_info[1], plat)
        mod = __import__(check_name)
        trace_dispatch, PyDBAdditionalThreadInfo = mod.trace_dispatch, mod.PyDBAdditionalThreadInfo
    except ImportError:
        raise