from _pydevd_bundle.pydevd_constants import IS_PY3K

LIB_FILE = 1
PYDEV_FILE = 2

DONT_TRACE = {
  # commonly used things from the stdlib that we don't want to trace
  'Queue.py':LIB_FILE,
  'queue.py':LIB_FILE,
  'socket.py':LIB_FILE,
  'weakref.py':LIB_FILE,
  '_weakrefset.py':LIB_FILE,
  'linecache.py':LIB_FILE,
  'threading.py':LIB_FILE,

  # thirs party libs that we don't want to trace
  '_pydev_pluginbase.py':PYDEV_FILE,
  '_pydev_pkgutil_old.py':PYDEV_FILE,
  '_pydev_uuid_old.py':PYDEV_FILE,

  #things from pydev that we don't want to trace
  '_pydev_execfile.py':PYDEV_FILE,
  '_pydev_threading':PYDEV_FILE,
  '_pydev_Queue':PYDEV_FILE,
  'django_debug.py':PYDEV_FILE,
  'jinja2_debug.py':PYDEV_FILE,
  'pydev_log.py':PYDEV_FILE,
  'pydev_monkey.py':PYDEV_FILE,
  'pydev_monkey_qt.py':PYDEV_FILE,
  'pydevd.py':PYDEV_FILE,
  'pydevd_additional_thread_info.py':PYDEV_FILE,
  'pydevd_breakpoints.py':PYDEV_FILE,
  'pydevd_comm.py':PYDEV_FILE,
  'pydevd_console.py':PYDEV_FILE,
  'pydevd_constants.py':PYDEV_FILE,
  'pydevd_custom_frames.py':PYDEV_FILE,
  'pydevd_dont_trace.py':PYDEV_FILE,
  'pydevd_exec.py':PYDEV_FILE,
  'pydevd_exec2.py':PYDEV_FILE,
  'pydevd_file_utils.py':PYDEV_FILE,
  'pydevd_frame.py':PYDEV_FILE,
  'pydevd_import_class.py':PYDEV_FILE,
  'pydevd_io.py':PYDEV_FILE,
  'pydevd_process_net_command.py':PYDEV_FILE,
  'pydevd_psyco_stub.py':PYDEV_FILE,
  'pydevd_referrers.py':PYDEV_FILE,
  'pydevd_reload.py':PYDEV_FILE,
  'pydevd_resolver.py':PYDEV_FILE,
  'pydevd_save_locals.py':PYDEV_FILE,
  'pydevd_signature.py':PYDEV_FILE,
  'pydevd_stackless.py':PYDEV_FILE,
  'pydevd_traceproperty.py':PYDEV_FILE,
  'pydevd_tracing.py':PYDEV_FILE,
  'pydevd_utils.py':PYDEV_FILE,
  'pydevd_vars.py':PYDEV_FILE,
  'pydevd_vm_type.py':PYDEV_FILE,
  'pydevd_xml.py':PYDEV_FILE,
}

if IS_PY3K:
    # if we try to trace io.py it seems it can get halted (see http://bugs.python.org/issue4716)
    DONT_TRACE['io.py'] = LIB_FILE

    # Don't trace common encodings too
    DONT_TRACE['cp1252.py'] = LIB_FILE
    DONT_TRACE['utf_8.py'] = LIB_FILE
