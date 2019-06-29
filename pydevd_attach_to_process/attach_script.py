

def load_python_helper_lib():
    import sys
    try:
        import ctypes
    except ImportError:
        ctypes = None

    import platform
    import os
    IS_64BIT_PROCESS = sys.maxsize > (2 ** 32)
    IS_WINDOWS = sys.platform == 'win32'
    IS_LINUX = sys.platform in ('linux', 'linux2')
    IS_MAC = sys.platform == 'darwin'
    IS_CPYTHON = platform.python_implementation() == 'CPython'

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
        return ctypes.cdll.LoadLibrary(filename)
    except:
        return None


def attach(port, host, protocol=''):
    try:
        import sys
        lib = load_python_helper_lib()
        lib.PrintDebugInfo()

#         if 'threading' not in sys.modules:
#             if lib is not None:
#                 lib.ImportThreadingOnMain()

        import threading
        print(threading.current_thread().ident)
        try:
            print(threading._shutdown.im_self.ident)  # @UndefinedVariable
        except:
            print(threading.main_thread().ident)  # @UndefinedVariable
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
