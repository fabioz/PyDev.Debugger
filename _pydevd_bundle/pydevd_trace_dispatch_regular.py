import traceback

from _pydev_bundle.pydev_is_thread_alive import is_thread_alive
from _pydev_imps._pydev_saved_modules import threading
from _pydevd_bundle.pydevd_constants import get_thread_id
from _pydevd_bundle.pydevd_dont_trace_files import DONT_TRACE
from _pydevd_bundle.pydevd_kill_all_pydevd_threads import kill_all_pydev_threads
from pydevd_file_utils import get_abs_path_real_path_and_base_from_frame, NORM_PATHS_AND_BASE_CONTAINER
from pydevd_tracing import SetTrace
# IFDEF CYTHON
# # In Cython, PyDBAdditionalThreadInfo is bundled in the file.
# from cpython.object cimport PyObject
# from cpython.ref cimport Py_INCREF, Py_XDECREF
# ELSE
from _pydevd_bundle.pydevd_additional_thread_info import PyDBAdditionalThreadInfo
from _pydevd_bundle.pydevd_frame import PyDBFrame
# ENDIF

threadingCurrentThread = threading.currentThread
get_file_type = DONT_TRACE.get

# Cache where we should keep that we completely skipped entering some context.
# It needs to be invalidated when:
# - Breakpoints are changed
# It can be used when running regularly (without step over/step in/step return)
global_cache_skips = {}

def trace_dispatch(py_db, frame, event, arg):
    thread = threadingCurrentThread()

    if getattr(thread, 'pydev_do_not_trace', None):
        return None

    try:
        additional_info = thread.additional_info
        if additional_info is None:
            raise AttributeError()
    except:
        additional_info = thread.additional_info = PyDBAdditionalThreadInfo()

    thread_tracer = ThreadTracer((py_db, thread, additional_info, global_cache_skips))
# IFDEF CYTHON
#     thread._tracer = thread_tracer # Hack for cython to keep it alive while the thread is alive (just the method in the SetTrace is not enough).
# ELSE
# ENDIF
    SetTrace(thread_tracer.__call__)
    return thread_tracer.__call__(frame, event, arg)

# IFDEF CYTHON
# cdef class SafeCallWrapper:
#   cdef method_object
#   def __init__(self, method_object):
#       self.method_object = method_object
#   def  __call__(self, *args):
#       #Cannot use 'self' once inside the delegate call since we are borrowing the self reference f_trace field
#       #in the frame, and that reference might get destroyed by set trace on frame and parents
#       cdef PyObject* method_obj = <PyObject*> self.method_object
#       Py_INCREF(<object>method_obj)
#       ret = (<object>method_obj)(*args)
#       Py_XDECREF (method_obj)
#       return SafeCallWrapper(ret) if ret is not None else None
# cdef class ThreadTracer:
#     cdef public tuple _args;
#     def __init__(self, tuple args):
#         self._args = args
# ELSE
class ThreadTracer:
    def __init__(self, args):
        self._args = args
# ENDIF


    def __call__(self, frame, event, arg):
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
        # cdef int pydev_step_cmd;
        # cdef tuple cache_key;
        # cdef dict cache_skips;
        # cdef bint is_stepping;
        # cdef tuple abs_path_real_path_and_base;
        # cdef PyDBAdditionalThreadInfo additional_info;
        # ENDIF
        py_db, t, additional_info, cache_skips = self._args
        pydev_step_cmd = additional_info.pydev_step_cmd
        is_stepping = pydev_step_cmd != -1

        try:
            if py_db._finish_debugging_session:
                if not py_db._termination_event_set:
                    #that was not working very well because jython gave some socket errors
                    try:
                        if py_db.output_checker is None:
                            kill_all_pydev_threads()
                    except:
                        traceback.print_exc()
                    py_db._termination_event_set = True
                return None

            # if thread is not alive, cancel trace_dispatch processing
            if not is_thread_alive(t):
                py_db._process_thread_not_alive(get_thread_id(t))
                return None  # suspend tracing

            try:
                # Make fast path faster!
                abs_path_real_path_and_base = NORM_PATHS_AND_BASE_CONTAINER[frame.f_code.co_filename]
            except:
                abs_path_real_path_and_base = get_abs_path_real_path_and_base_from_frame(frame)

            if py_db.thread_analyser is not None:
                py_db.thread_analyser.log_event(frame)

            if py_db.asyncio_analyser is not None:
                py_db.asyncio_analyser.log_event(frame)
                
            cache_key = (abs_path_real_path_and_base, frame.f_lineno)
            if not is_stepping and cache_key in cache_skips:
                return None

            file_type = get_file_type(abs_path_real_path_and_base[-1]) #we don't want to debug threading or anything related to pydevd

            if file_type is not None:
                if file_type == 1: # inlining LIB_FILE = 1
                    if py_db.not_in_scope(abs_path_real_path_and_base[1]):
                        # print('skipped: trace_dispatch (not in scope)', base, frame.f_lineno, event, frame.f_code.co_name, file_type)
                        cache_skips[cache_key] = 1
                        return None
                else:
                    # print('skipped: trace_dispatch', base, frame.f_lineno, event, frame.f_code.co_name, file_type)
                    cache_skips[cache_key] = 1
                    return None

            if is_stepping:
                if py_db.is_filter_enabled and py_db.is_ignored_by_filters(abs_path_real_path_and_base[1]):
                    # ignore files matching stepping filters
                    return None
                if py_db.is_filter_libraries and py_db.not_in_scope(abs_path_real_path_and_base[1]):
                    # ignore library files while stepping
                    return None

            # print('trace_dispatch', base, frame.f_lineno, event, frame.f_code.co_name, file_type)
            if additional_info.is_tracing:
                return None  #we don't wan't to trace code invoked from pydevd_frame.trace_dispatch

            if event == 'call' and py_db.signature_factory:
                # We can only have a call when entering a context, so, check at this level, not at the PyDBFrame.
                # filename = abs_path_real_path_and_base[1]
                send_signature_call_trace(py_db, frame, abs_path_real_path_and_base[1])

            # Just create PyDBFrame directly (removed support for Python versions < 2.5, which required keeping a weak
            # reference to the frame).
            ret = PyDBFrame((py_db, abs_path_real_path_and_base[1], additional_info, t)).trace_dispatch(frame, event, arg)
            if ret is None:
                print('Cached skip for: %s %s' % (abs_path_real_path_and_base[1], frame.f_code.co_name))
                cache_skips[cache_key] = 1
                return None
            
            # IFDEF CYTHON
            # return SafeCallWrapper(ret)
            # ELSE
            # ENDIF

        except SystemExit:
            return None

        except Exception:
            if py_db._finish_debugging_session:
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
