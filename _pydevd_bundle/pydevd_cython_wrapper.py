try:
    from _pydevd_bundle.pydevd_cython import trace_dispatch, PyDBAdditionalThreadInfo, global_cache_skips
except ImportError:
    try:
        import struct
        import sys
        try:
            is_python_64bit = (struct.calcsize('P') == 8)
        except:
            # In Jython this call fails, but this is Ok, we don't support Jython for speedups anyways.
            raise ImportError
        plat = '32'
        if is_python_64bit:
            plat = '64'

        # We also accept things as:
        #
        # _pydevd_bundle.pydevd_cython_win32_27_32
        # _pydevd_bundle.pydevd_cython_win32_34_64
        #
        # to have multiple pre-compiled pyds distributed along the IDE
        # (generated by build_tools/build_binaries_windows.py).

        mod_name = 'pydevd_cython_%s_%s%s_%s' % (sys.platform, sys.version_info[0], sys.version_info[1], plat)
        check_name = '_pydevd_bundle.%s' % (mod_name,)
        mod = __import__(check_name)
        mod = getattr(mod, mod_name)
        trace_dispatch, PyDBAdditionalThreadInfo, global_cache_skips = mod.trace_dispatch, mod.PyDBAdditionalThreadInfo, mod.global_cache_skips
    except ImportError:
        raise