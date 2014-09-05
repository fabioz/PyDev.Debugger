import sys
import os

def process_command_line(argv):
    setup = {}
    setup['port'] = 5678  # Default port for PyDev remote debugger
    setup['pid'] = 0
    setup['host'] = '127.0.0.1'
    
    i = 0
    while i < len(argv):
        if argv[i] == '--port':
            del argv[i]
            setup['port'] = int(argv[i])
            del argv[i]
            
        elif argv[i] == '--pid':
            del argv[i]
            setup['pid'] = int(argv[i])
            del argv[i]
            
        elif argv[i] == '--host':
            del argv[i]
            setup['host'] = int(argv[i])
            del argv[i]
            
            
    if not setup['pid']:
        sys.stderr.write('Expected --pid to be passed.\n')
        sys.exit(1)
    return setup
            
            
def main(setup):
    import add_code_to_python_process
    
    pydevd_dirname = os.path.dirname(os.path.dirname(__file__))
    
    setup['pythonpath'] = pydevd_dirname
    python_code = '''import threading
try:
    import sys;sys.path.append(%(pythonpath)r)
    import pydevd
    # pydevd.DebugInfoHolder.DEBUG_RECORD_SOCKET_READS = True
    # pydevd.DebugInfoHolder.DEBUG_TRACE_BREAKPOINTS = 3
    # pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL = 3
    pydevd.settrace(port=%(port)s, host=%(host)r, overwrite_prev_trace=True, suspend=False, trace_only_current_thread=False, patch_multiprocessing=False)
except:
    import traceback;traceback.print_exc()
''' % setup
    
    python_code = python_code.replace('\'', '"')
    add_code_to_python_process.run_python_code(setup['pid'], python_code, connect_debugger_tracing=True)
    
if __name__ == '__main__':
    main(process_command_line(sys.argv[1:]))
