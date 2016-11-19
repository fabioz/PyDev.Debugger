if __name__ == '__main__':
    import subprocess
    import sys
    from tests_python import _debugger_case_remote_2
    subprocess.check_call([sys.executable, '-u', _debugger_case_remote_2.__file__])
    print('finished')