import traceback

from _pydev_bundle.pydev_is_thread_alive import is_thread_alive
from _pydev_imps import _pydev_threading as threading
from _pydevd_bundle.pydevd_additional_thread_info import PyDBAdditionalThreadInfo
from _pydevd_bundle.pydevd_constants import get_thread_id
from _pydevd_bundle.pydevd_dont_trace_files import DONT_TRACE
from _pydevd_bundle.pydevd_kill_all_pydevd_threads import kill_all_pydev_threads
from pydevd_file_utils import get_filename_and_base


threadingCurrentThread = threading.currentThread
get_file_type = DONT_TRACE.get

def trace_dispatch(py_db, frame, event, arg):
    ''' This is the callback used when we enter some context in the debugger.

    We also decorate the thread we are in with info about the debugging.
    The attributes added are:
        pydev_state
        pydev_step_stop
        pydev_step_cmd
        pydev_notify_kill

    :param PyDB py_db:
        This is the global debugger (this method should actually be added as a method to it).
    '''
    # IFDEF CYTHON
    # cdef str filename;
    # cdef str base;
    # ENDIF

    try:
        if py_db._finishDebuggingSession and not py_db._terminationEventSent:
            #that was not working very well because jython gave some socket errors
            try:
                if py_db.output_checker is None:
                    kill_all_pydev_threads()
            except:
                traceback.print_exc()
            py_db._terminationEventSent = True
            return None

        filename, base = get_filename_and_base(frame)

        if py_db.thread_analyser is not None:
            py_db.thread_analyser.log_event(frame)

        if py_db.asyncio_analyser is not None:
            py_db.asyncio_analyser.log_event(frame)

        file_type = get_file_type(base) #we don't want to debug threading or anything related to pydevd

        #print('trace_dispatch', base, frame.f_lineno, event, frame.f_code.co_name, is_file_to_ignore)
        if file_type is not None:
            if file_type == 1: # inlining LIB_FILE = 1
                if py_db.not_in_scope(filename):
                    return None
            else:
                return None

        #try:
        t = threadingCurrentThread()
        #except:
        #this could give an exception (python 2.5 bug), but should not be there anymore...
        #see http://mail.python.org/pipermail/python-bugs-list/2007-June/038796.html
        #and related bug: http://bugs.python.org/issue1733757
        #frame.f_trace = py_db.trace_dispatch
        #return py_db.trace_dispatch

        try:
            additional_info = t.additional_info
            if additional_info is None:
                raise AttributeError()
        except:
            additional_info = t.additional_info = PyDBAdditionalThreadInfo()

        if additional_info.is_tracing:
            f = frame
            while f is not None:
                if 'trace_dispatch' == f.f_code.co_name:
                    _fname, bs = get_filename_and_base(f)
                    if bs == 'pydevd_frame.py':
                        return None  #we don't wan't to trace code invoked from pydevd_frame.trace_dispatch
                f = f.f_back

        # if thread is not alive, cancel trace_dispatch processing
        if not is_thread_alive(t):
            py_db._process_thread_not_alive(get_thread_id(t))
            return None  # suspend tracing

        # each new frame...
        # IFDEF CYTHON
        # # Note that on Cython we only support more modern idioms (no support for < Python 2.5)
        # return PyDBFrame((py_db, filename, additional_info, t)).trace_dispatch(frame, event, arg)
        # ELSE
        return additional_info.create_db_frame((py_db, filename, additional_info, t, frame)).trace_dispatch(frame, event, arg)
        # ENDIF

    except SystemExit:
        return None

    except Exception:
        if py_db._finishDebuggingSession:
            return None # Don't log errors when we're shutting down.
        # Log it
        try:
            if traceback is not None:
                # This can actually happen during the interpreter shutdown in Python 2.7
                traceback.print_exc()
        except:
            # Error logging? We're really in the interpreter shutdown...
            # (https://github.com/fabioz/PyDev.Debugger/issues/8)
            pass
        return None
