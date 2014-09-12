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
    python_code = '''import sys;
sys.path.append(\\\"%(pythonpath)s\\\");
import attach_script;
attach_script.attach(port=%(port)s, host=\\\"%(host)s\\\");
'''.replace('\r\n', '').replace('\r', '').replace('\n', '')

    python_code = python_code % setup
    add_code_to_python_process.run_python_code(
        setup['pid'], python_code, connect_debugger_tracing=True)

if __name__ == '__main__':
    main(process_command_line(sys.argv[1:]))
