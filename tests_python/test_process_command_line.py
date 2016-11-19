import unittest

class Test(unittest.TestCase):
    
    def testProcessCommandLine(self):
        from _pydevd_bundle.pydevd_command_line_handling import process_command_line, setup_to_argv
        setup = process_command_line(['pydevd.py', '--port', '1', '--save-threading'])
        assert setup['save-threading']
        assert setup['port'] == 1
        assert not setup['qt-support']
        
        argv = setup_to_argv(setup)
        assert argv[0].endswith('pydevd.py')
        argv = argv[1:]
        assert argv == ['--port', '1', '--save-threading']
        