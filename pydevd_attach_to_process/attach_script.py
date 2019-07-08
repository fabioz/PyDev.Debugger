

def load_python_helper_lib():
    import sys
    try:
        import ctypes
    except ImportError:
        ctypes = None

    # Note: we cannot use import platform because it may end up importing threading,
    # but that should be ok because at this point we can only be in CPython (other
    # implementations wouldn't get to this point in the attach process).
    # IS_CPYTHON = platform.python_implementation() == 'CPython'
    IS_CPYTHON = True

    import os
    IS_64BIT_PROCESS = sys.maxsize > (2 ** 32)
    IS_WINDOWS = sys.platform == 'win32'
    IS_LINUX = sys.platform in ('linux', 'linux2')
    IS_MAC = sys.platform == 'darwin'

    if not IS_CPYTHON or ctypes is None or sys.version_info[:2] > (3, 7):
        return None

    if IS_WINDOWS:
        if IS_64BIT_PROCESS:
            suffix = 'amd64'
        else:
            suffix = 'x86'

        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pydevd_attach_to_process', 'attach_%s.dll' % (suffix,))

    elif IS_LINUX:
        if IS_64BIT_PROCESS:
            suffix = 'amd64'
        else:
            suffix = 'x86'

        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pydevd_attach_to_process', 'attach_linux_%s.so' % (suffix,))

    elif IS_MAC:
        if IS_64BIT_PROCESS:
            suffix = 'x86_64.dylib'
        else:
            suffix = 'x86.dylib'

        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pydevd_attach_to_process', 'attach_%s' % (suffix,))

    else:
        return None

    if not os.path.exists(filename):
        return None

    try:
        # Load as pydll so that we don't release the gil.
        lib = ctypes.pydll.LoadLibrary(filename)
        lib.list_all_thread_ids.restype = ctypes.c_voidp

        # A helper to cast in the library so that we don't have to import ctypes to do a cast
        # in the caller code.
        lib.cast_to_pyobject.argtypes = (ctypes.c_voidp,)
        lib.cast_to_pyobject.restype = ctypes.py_object
        return lib
    except:
        return None


def attach(port, host, protocol=''):
    try:
        import sys
        lib = load_python_helper_lib()

        if 'threading' not in sys.modules:
            # This means that we weren't able to import threading in the main thread (which most
            # likely means that the main thread is paused or in some very long operation).
            # In this case we'll import threading here and hotfix what may be wrong in the threading
            # module (if we're on Windows where we create a thread to do the attach).
            print('Threading NOT found in sys.modules.')
            import threading

            with threading._active_limbo_lock:

                if hasattr(threading, 'main_thread'):
                    main_thread_instance = threading.main_thread()
                else:
                    main_thread_instance = threading._shutdown.im_self

                secondary_thread_ident = threading.get_ident()
                thread_idents = lib.list_all_thread_ids()
                if thread_idents:
                    for thread_ident in lib.cast_to_pyobject(thread_idents):
                        if thread_ident != secondary_thread_ident:
                            del threading._active[main_thread_instance._ident]
                            main_thread_instance._ident = thread_ident
                            threading._active[main_thread_instance._ident] = main_thread_instance

        else:
            print('Threading found in sys.modules.')

        import threading
        print('current thread id', threading.current_thread().ident)
        try:
            print('main thread id x - ', threading._shutdown.im_self.ident)  # @UndefinedVariable
        except:
            print('main thread id y', threading.main_thread().ident)  # @UndefinedVariable
        print('lib.GetMainThreadId()', lib.GetMainThreadId())

        if protocol:
            from _pydevd_bundle import pydevd_defaults
            pydevd_defaults.PydevdCustomization.DEFAULT_PROTOCOL = protocol

        import pydevd
        pydevd.stoptrace()  # I.e.: disconnect if already connected
        # pydevd.DebugInfoHolder.DEBUG_RECORD_SOCKET_READS = True
        # pydevd.DebugInfoHolder.DEBUG_TRACE_BREAKPOINTS = 3
        # pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL = 3
        pydevd.settrace(
            port=port,
            host=host,
            stdoutToServer=True,
            stderrToServer=True,
            overwrite_prev_trace=True,
            suspend=False,
            trace_only_current_thread=False,
            patch_multiprocessing=False,
        )
    except:
        import traceback
        traceback.print_exc()
