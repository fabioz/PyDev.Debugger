'''
    The idea is that we record the commands sent to the debugger and reproduce them from this script
    (so, this works as the client, which spawns the debugger as a separate process and communicates
    to it as if it was run from the outside)

    Note that it's a python script but it'll spawn a process to run as jython, ironpython and as python.
'''



try:
    from thread import start_new_thread
except ImportError:
    from _thread import start_new_thread  # @UnresolvedImport
CMD_SET_PROPERTY_TRACE, CMD_EVALUATE_CONSOLE_EXPRESSION, CMD_RUN_CUSTOM_OPERATION, CMD_ENABLE_DONT_TRACE = 133, 134, 135, 141
PYTHON_EXE = None
IRONPYTHON_EXE = None
JYTHON_JAR_LOCATION = None
JAVA_LOCATION = None


import unittest
from _pydev_bundle import pydev_localhost

try:
    xrange
except:
    xrange = range

import os

import pydevd
PYDEVD_FILE = pydevd.__file__

import sys

import subprocess
import socket
import threading
import time

import debugger_unittest

#=======================================================================================================================
# WriterThreadCase19 - [Test Case]: Evaluate '__' attributes
#======================================================================================================================
class WriterThreadCase19(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case19.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(8, None)
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        assert line == 8, 'Expected return to be in line 8, was: %s' % line

        self.WriteEvaluateExpression('%s\t%s\t%s' % (thread_id, frame_id, 'LOCAL'), 'a.__var')
        self.WaitForEvaluation('<var name="a.__var" type="int" value="int')
        self.WriteRunThread(thread_id)


        self.finishedOk = True


#=======================================================================================================================
# WriterThreadCase18 - [Test Case]: change local variable
#======================================================================================================================
class WriterThreadCase18(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case18.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(5, 'm2')
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)
        assert line == 5, 'Expected return to be in line 2, was: %s' % line

        self.WriteChangeVariable(thread_id, frame_id, 'a', '40')
        self.WriteRunThread(thread_id)

        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase17 - [Test Case]: dont trace
#======================================================================================================================
class WriterThreadCase17(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case17.py')

    def run(self):
        self.StartSocket()
        self.WriteEnableDontTrace(True)
        self.WriteAddBreakpoint(27, 'main')
        self.WriteAddBreakpoint(29, 'main')
        self.WriteAddBreakpoint(31, 'main')
        self.WriteAddBreakpoint(33, 'main')
        self.WriteMakeInitialRun()

        for i in range(4):
            thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

            self.WriteStepIn(thread_id)
            thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)
            # Should Skip step into properties setter
            assert line == 2, 'Expected return to be in line 2, was: %s' % line
            self.WriteRunThread(thread_id)


        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase17a - [Test Case]: dont trace return
#======================================================================================================================
class WriterThreadCase17a(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case17a.py')

    def run(self):
        self.StartSocket()
        self.WriteEnableDontTrace(True)
        self.WriteAddBreakpoint(2, 'm1')
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)
        # Should Skip step into properties setter
        assert line == 10, 'Expected return to be in line 10, was: %s' % line
        self.WriteRunThread(thread_id)


        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase16 - [Test Case]: numpy.ndarray resolver
#======================================================================================================================
class WriterThreadCase16(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case16.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(9, 'main')
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        # In this test we check that the three arrays of different shapes, sizes and types
        # are all resolved properly as ndarrays.

        # First pass check is that we have all three expected variables defined
        self.WriteGetFrame(thread_id, frame_id)
        self.WaitForVars('<var name="smallarray" type="ndarray" value="ndarray%253A %255B  0.%252B1.j   1.%252B1.j   2.%252B1.j   3.%252B1.j   4.%252B1.j   5.%252B1.j   6.%252B1.j   7.%252B1.j%250A   8.%252B1.j   9.%252B1.j  10.%252B1.j  11.%252B1.j  12.%252B1.j  13.%252B1.j  14.%252B1.j  15.%252B1.j%250A  16.%252B1.j  17.%252B1.j  18.%252B1.j  19.%252B1.j  20.%252B1.j  21.%252B1.j  22.%252B1.j  23.%252B1.j%250A  24.%252B1.j  25.%252B1.j  26.%252B1.j  27.%252B1.j  28.%252B1.j  29.%252B1.j  30.%252B1.j  31.%252B1.j%250A  32.%252B1.j  33.%252B1.j  34.%252B1.j  35.%252B1.j  36.%252B1.j  37.%252B1.j  38.%252B1.j  39.%252B1.j%250A  40.%252B1.j  41.%252B1.j  42.%252B1.j  43.%252B1.j  44.%252B1.j  45.%252B1.j  46.%252B1.j  47.%252B1.j%250A  48.%252B1.j  49.%252B1.j  50.%252B1.j  51.%252B1.j  52.%252B1.j  53.%252B1.j  54.%252B1.j  55.%252B1.j%250A  56.%252B1.j  57.%252B1.j  58.%252B1.j  59.%252B1.j  60.%252B1.j  61.%252B1.j  62.%252B1.j  63.%252B1.j%250A  64.%252B1.j  65.%252B1.j  66.%252B1.j  67.%252B1.j  68.%252B1.j  69.%252B1.j  70.%252B1.j  71.%252B1.j%250A  72.%252B1.j  73.%252B1.j  74.%252B1.j  75.%252B1.j  76.%252B1.j  77.%252B1.j  78.%252B1.j  79.%252B1.j%250A  80.%252B1.j  81.%252B1.j  82.%252B1.j  83.%252B1.j  84.%252B1.j  85.%252B1.j  86.%252B1.j  87.%252B1.j%250A  88.%252B1.j  89.%252B1.j  90.%252B1.j  91.%252B1.j  92.%252B1.j  93.%252B1.j  94.%252B1.j  95.%252B1.j%250A  96.%252B1.j  97.%252B1.j  98.%252B1.j  99.%252B1.j%255D" isContainer="True" />')
        self.WaitForVars('<var name="bigarray" type="ndarray" value="ndarray%253A %255B%255B    0     1     2 ...%252C  9997  9998  9999%255D%250A %255B10000 10001 10002 ...%252C 19997 19998 19999%255D%250A %255B20000 20001 20002 ...%252C 29997 29998 29999%255D%250A ...%252C %250A %255B70000 70001 70002 ...%252C 79997 79998 79999%255D%250A %255B80000 80001 80002 ...%252C 89997 89998 89999%255D%250A %255B90000 90001 90002 ...%252C 99997 99998 99999%255D%255D" isContainer="True" />')
        self.WaitForVars('<var name="hugearray" type="ndarray" value="ndarray%253A %255B      0       1       2 ...%252C 9999997 9999998 9999999%255D" isContainer="True" />')

        # For each variable, check each of the resolved (meta data) attributes...
        self.WriteGetVariable(thread_id, frame_id, 'smallarray')
        self.WaitForVar('<var name="min" type="complex128"')
        self.WaitForVar('<var name="max" type="complex128"')
        self.WaitForVar('<var name="shape" type="tuple"')
        self.WaitForVar('<var name="dtype" type="dtype"')
        self.WaitForVar('<var name="size" type="int"')
        # ...and check that the internals are resolved properly
        self.WriteGetVariable(thread_id, frame_id, 'smallarray\t__internals__')
        self.WaitForVar('<var name="%27size%27')

        self.WriteGetVariable(thread_id, frame_id, 'bigarray')
        self.WaitForVar([
            '<var name="min" type="int64" value="int64%253A 0" />',
            '<var name="min" type="int64" value="int64%3A 0" />',
            '<var name="size" type="int" value="int%3A 100000" />',
        ])
        self.WaitForVar([
            '<var name="max" type="int64" value="int64%253A 99999" />',
            '<var name="max" type="int32" value="int32%253A 99999" />',
            '<var name="max" type="int64" value="int64%3A 99999"'
        ])
        self.WaitForVar('<var name="shape" type="tuple"')
        self.WaitForVar('<var name="dtype" type="dtype"')
        self.WaitForVar('<var name="size" type="int"')
        self.WriteGetVariable(thread_id, frame_id, 'bigarray\t__internals__')
        self.WaitForVar('<var name="%27size%27')

        # this one is different because it crosses the magic threshold where we don't calculate
        # the min/max
        self.WriteGetVariable(thread_id, frame_id, 'hugearray')
        self.WaitForVar([
            '<var name="min" type="str" value="str%253A ndarray too big%252C calculating min would slow down debugging" />',
            '<var name="min" type="str" value="str%3A ndarray too big%252C calculating min would slow down debugging" />',
        ])
        self.WaitForVar([
            '<var name="max" type="str" value="str%253A ndarray too big%252C calculating max would slow down debugging" />',
            '<var name="max" type="str" value="str%3A ndarray too big%252C calculating max would slow down debugging" />',
        ])
        self.WaitForVar('<var name="shape" type="tuple"')
        self.WaitForVar('<var name="dtype" type="dtype"')
        self.WaitForVar('<var name="size" type="int"')
        self.WriteGetVariable(thread_id, frame_id, 'hugearray\t__internals__')
        self.WaitForVar('<var name="%27size%27')

        self.WriteRunThread(thread_id)
        self.finishedOk = True


#=======================================================================================================================
# WriterThreadCase15 - [Test Case]: Custom Commands
#======================================================================================================================
class WriterThreadCase15(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case15.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(22, 'main')
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        # Access some variable
        self.WriteCustomOperation("%s\t%s\tEXPRESSION\tcarObj.color" % (thread_id, frame_id), "EXEC", "f=lambda x: 'val=%s' % x", "f")
        self.WaitForCustomOperation('val=Black')
        assert 7 == self._sequence, 'Expected 7. Had: %s' % self._sequence

        self.WriteCustomOperation("%s\t%s\tEXPRESSION\tcarObj.color" % (thread_id, frame_id), "EXECFILE", debugger_unittest._get_debugger_test_file('_debugger_case15_execfile.py'), "f")
        self.WaitForCustomOperation('val=Black')
        assert 9 == self._sequence, 'Expected 9. Had: %s' % self._sequence

        self.WriteRunThread(thread_id)
        self.finishedOk = True



#=======================================================================================================================
# WriterThreadCase14 - [Test Case]: Interactive Debug Console
#======================================================================================================================
class WriterThreadCase14(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case14.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(22, 'main')
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)
        assert thread_id, '%s not valid.' % thread_id
        assert frame_id, '%s not valid.' % frame_id

        # Access some variable
        self.WriteDebugConsoleExpression("%s\t%s\tEVALUATE\tcarObj.color" % (thread_id, frame_id))
        self.WaitForVar(['<more>False</more>', '%27Black%27'])
        assert 7 == self._sequence, 'Expected 9. Had: %s' % self._sequence

        # Change some variable
        self.WriteDebugConsoleExpression("%s\t%s\tEVALUATE\tcarObj.color='Red'" % (thread_id, frame_id))
        self.WriteDebugConsoleExpression("%s\t%s\tEVALUATE\tcarObj.color" % (thread_id, frame_id))
        self.WaitForVar(['<more>False</more>', '%27Red%27'])
        assert 11 == self._sequence, 'Expected 13. Had: %s' % self._sequence

        # Iterate some loop
        self.WriteDebugConsoleExpression("%s\t%s\tEVALUATE\tfor i in range(3):" % (thread_id, frame_id))
        self.WaitForVar(['<xml><more>True</more></xml>', '<xml><more>1</more></xml>'])
        self.WriteDebugConsoleExpression("%s\t%s\tEVALUATE\t    print(i)" % (thread_id, frame_id))
        self.WriteDebugConsoleExpression("%s\t%s\tEVALUATE\t" % (thread_id, frame_id))
        self.WaitForVar(
            [
                '<xml><more>False</more><output message="0"></output><output message="1"></output><output message="2"></output></xml>',
                '<xml><more>0</more><output message="0"></output><output message="1"></output><output message="2"></output></xml>'
            ]
            )
        assert 17 == self._sequence, 'Expected 19. Had: %s' % self._sequence

        self.WriteRunThread(thread_id)
        self.finishedOk = True


#=======================================================================================================================
# WriterThreadCase13
#======================================================================================================================
class WriterThreadCase13(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case13.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(35, 'main')
        self.Write("%s\t%s\t%s" % (CMD_SET_PROPERTY_TRACE, self.NextSeq(), "true;false;false;true"))
        self.WriteMakeInitialRun()
        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)
        # Should go inside setter method
        assert line == 25, 'Expected return to be in line 25, was: %s' % line

        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)

        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)
        # Should go inside getter method
        assert line == 21, 'Expected return to be in line 21, was: %s' % line

        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)

        # Disable property tracing
        self.Write("%s\t%s\t%s" % (CMD_SET_PROPERTY_TRACE, self.NextSeq(), "true;true;true;true"))
        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)
        # Should Skip step into properties setter
        assert line == 39, 'Expected return to be in line 39, was: %s' % line

        # Enable property tracing
        self.Write("%s\t%s\t%s" % (CMD_SET_PROPERTY_TRACE, self.NextSeq(), "true;false;false;true"))
        self.WriteStepIn(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)
        # Should go inside getter method
        assert line == 8, 'Expected return to be in line 8, was: %s' % line

        self.WriteRunThread(thread_id)

        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase12
#======================================================================================================================
class WriterThreadCase12(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case10.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(2, '')  # Should not be hit: setting empty function (not None) should only hit global.
        self.WriteAddBreakpoint(6, 'Method1a')
        self.WriteAddBreakpoint(11, 'Method2')
        self.WriteMakeInitialRun()

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        assert line == 11, 'Expected return to be in line 11, was: %s' % line

        self.WriteStepReturn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)  # not a return (it stopped in the other breakpoint)

        assert line == 6, 'Expected return to be in line 6, was: %s' % line

        self.WriteRunThread(thread_id)

        assert 13 == self._sequence, 'Expected 13. Had: %s' % self._sequence

        self.finishedOk = True



#=======================================================================================================================
# WriterThreadCase11
#======================================================================================================================
class WriterThreadCase11(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case10.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(2, 'Method1')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit('111')

        self.WriteStepOver(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        assert line == 3, 'Expected return to be in line 3, was: %s' % line

        self.WriteStepOver(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        assert line == 11, 'Expected return to be in line 11, was: %s' % line

        self.WriteStepOver(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        assert line == 12, 'Expected return to be in line 12, was: %s' % line

        self.WriteRunThread(thread_id)

        assert 13 == self._sequence, 'Expected 13. Had: %s' % self._sequence

        self.finishedOk = True



#=======================================================================================================================
# WriterThreadCase10
#======================================================================================================================
class WriterThreadCase10(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case10.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(2, 'None')  # None or Method should make hit.
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit('111')

        self.WriteStepReturn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('109', True)

        assert line == 11, 'Expected return to be in line 11, was: %s' % line

        self.WriteStepOver(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        assert line == 12, 'Expected return to be in line 12, was: %s' % line

        self.WriteRunThread(thread_id)

        assert 11 == self._sequence, 'Expected 11. Had: %s' % self._sequence

        self.finishedOk = True



#=======================================================================================================================
# WriterThreadCase9
#======================================================================================================================
class WriterThreadCase9(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case89.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(10, 'Method3')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit('111')

        self.WriteStepOver(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        assert line == 11, 'Expected return to be in line 11, was: %s' % line

        self.WriteStepOver(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        assert line == 12, 'Expected return to be in line 12, was: %s' % line

        self.WriteRunThread(thread_id)

        assert 11 == self._sequence, 'Expected 11. Had: %s' % self._sequence

        self.finishedOk = True


#=======================================================================================================================
# WriterThreadCase8
#======================================================================================================================
class WriterThreadCase8(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case89.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(10, 'Method3')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit('111')

        self.WriteStepReturn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('109', True)

        assert line == 15, 'Expected return to be in line 15, was: %s' % line

        self.WriteRunThread(thread_id)

        assert 9 == self._sequence, 'Expected 9. Had: %s' % self._sequence

        self.finishedOk = True




#=======================================================================================================================
# WriterThreadCase7
#======================================================================================================================
class WriterThreadCase7(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case7.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(2, 'Call')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit('111')

        self.WriteGetFrame(thread_id, frame_id)

        self.WaitForVars('<xml></xml>')  # no vars at this point

        self.WriteStepOver(thread_id)

        self.WriteGetFrame(thread_id, frame_id)

        self.WaitForVars('<xml><var name="variable_for_test_1" type="int" value="int%253A 10" />%0A</xml>')

        self.WriteStepOver(thread_id)

        self.WriteGetFrame(thread_id, frame_id)

        self.WaitForVars('<xml><var name="variable_for_test_1" type="int" value="int%253A 10" />%0A<var name="variable_for_test_2" type="int" value="int%253A 20" />%0A</xml>')

        self.WriteRunThread(thread_id)

        assert 17 == self._sequence, 'Expected 17. Had: %s' % self._sequence

        self.finishedOk = True



#=======================================================================================================================
# WriterThreadCase6
#=======================================================================================================================
class WriterThreadCase6(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case56.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(2, 'Call2')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteStepReturn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('109', True)

        assert line == 8, 'Expecting it to go to line 8. Went to: %s' % line

        self.WriteStepIn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)

        # goes to line 4 in jython (function declaration line)
        assert line in (4, 5), 'Expecting it to go to line 4 or 5. Went to: %s' % line

        self.WriteRunThread(thread_id)

        assert 13 == self._sequence, 'Expected 15. Had: %s' % self._sequence

        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase5
#=======================================================================================================================
class WriterThreadCase5(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case56.py')

    def run(self):
        self.StartSocket()
        breakpoint_id = self.WriteAddBreakpoint(2, 'Call2')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteRemoveBreakpoint(breakpoint_id)

        self.WriteStepReturn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('109', True)

        assert line == 8, 'Expecting it to go to line 8. Went to: %s' % line

        self.WriteStepIn(thread_id)

        thread_id, frame_id, line = self.WaitForBreakpointHit('107', True)

        # goes to line 4 in jython (function declaration line)
        assert line in (4, 5), 'Expecting it to go to line 4 or 5. Went to: %s' % line

        self.WriteRunThread(thread_id)

        assert 15 == self._sequence, 'Expected 15. Had: %s' % self._sequence

        self.finishedOk = True


#=======================================================================================================================
# WriterThreadCase4
#=======================================================================================================================
class WriterThreadCase4(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case4.py')

    def run(self):
        self.StartSocket()
        self.WriteMakeInitialRun()

        thread_id = self.WaitForNewThread()

        self.WriteSuspendThread(thread_id)

        time.sleep(4)  # wait for time enough for the test to finish if it wasn't suspended

        self.WriteRunThread(thread_id)

        self.finishedOk = True


#=======================================================================================================================
# WriterThreadCase3
#=======================================================================================================================
class WriterThreadCase3(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case3.py')

    def run(self):
        self.StartSocket()
        self.WriteMakeInitialRun()
        time.sleep(.5)
        breakpoint_id = self.WriteAddBreakpoint(4, '')
        self.WriteAddBreakpoint(5, 'FuncNotAvailable')  # Check that it doesn't get hit in the global when a function is available

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteRunThread(thread_id)

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteRemoveBreakpoint(breakpoint_id)

        self.WriteRunThread(thread_id)

        assert 17 == self._sequence, 'Expected 17. Had: %s' % self._sequence

        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase2
#=======================================================================================================================
class WriterThreadCase2(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case2.py')

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(3, 'Call4')  # seq = 3
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteAddBreakpoint(14, 'Call2')

        self.WriteRunThread(thread_id)

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteGetFrame(thread_id, frame_id)

        self.WriteRunThread(thread_id)

        self.log.append('Checking sequence. Found: %s' % (self._sequence))
        assert 15 == self._sequence, 'Expected 15. Had: %s' % self._sequence

        self.log.append('Marking finished ok.')
        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCaseQThread1
#=======================================================================================================================
class WriterThreadCaseQThread1(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case_qthread1.py')

    def run(self):
        self.StartSocket()
        breakpoint_id = self.WriteAddBreakpoint(16, 'run')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteRemoveBreakpoint(breakpoint_id)
        self.WriteRunThread(thread_id)

        self.log.append('Checking sequence. Found: %s' % (self._sequence))
        assert 9 == self._sequence, 'Expected 9. Had: %s' % self._sequence

        self.log.append('Marking finished ok.')
        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCaseQThread2
#=======================================================================================================================
class WriterThreadCaseQThread2(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case_qthread2.py')

    def run(self):
        self.StartSocket()
        breakpoint_id = self.WriteAddBreakpoint(21, 'longRunning')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteRemoveBreakpoint(breakpoint_id)
        self.WriteRunThread(thread_id)

        self.log.append('Checking sequence. Found: %s' % (self._sequence))
        assert 9 == self._sequence, 'Expected 9. Had: %s' % self._sequence

        self.log.append('Marking finished ok.')
        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCaseQThread3
#=======================================================================================================================
class WriterThreadCaseQThread3(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case_qthread3.py')

    def run(self):
        self.StartSocket()
        breakpoint_id = self.WriteAddBreakpoint(19, 'run')
        self.WriteMakeInitialRun()

        thread_id, frame_id = self.WaitForBreakpointHit()

        self.WriteRemoveBreakpoint(breakpoint_id)
        self.WriteRunThread(thread_id)

        self.log.append('Checking sequence. Found: %s' % (self._sequence))
        assert 9 == self._sequence, 'Expected 9. Had: %s' % self._sequence

        self.log.append('Marking finished ok.')
        self.finishedOk = True

#=======================================================================================================================
# WriterThreadCase1
#=======================================================================================================================
class WriterThreadCase1(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_debugger_case1.py')

    def run(self):
        self.StartSocket()

        self.log.append('writing add breakpoint')
        self.WriteAddBreakpoint(6, 'SetUp')

        self.log.append('making initial run')
        self.WriteMakeInitialRun()

        self.log.append('waiting for breakpoint hit')
        thread_id, frame_id = self.WaitForBreakpointHit()

        self.log.append('get frame')
        self.WriteGetFrame(thread_id, frame_id)

        self.log.append('step over')
        self.WriteStepOver(thread_id)

        self.log.append('get frame')
        self.WriteGetFrame(thread_id, frame_id)

        self.log.append('run thread')
        self.WriteRunThread(thread_id)

        self.log.append('asserting')
        try:
            assert 13 == self._sequence, 'Expected 13. Had: %s' % self._sequence
        except:
            self.log.append('assert failed!')
            raise
        self.log.append('asserted')

        self.finishedOk = True

#=======================================================================================================================
# DebuggerBase
#=======================================================================================================================
class DebuggerBase(object):

    def getCommandLine(self):
        raise NotImplementedError

    def CheckCase(self, writer_thread_class):
        port = debugger_unittest.get_free_port()
        writer_thread = writer_thread_class(port)
        writer_thread.start()
        time.sleep(1)

        localhost = pydev_localhost.get_localhost()
        args = self.getCommandLine()
        args += [
            PYDEVD_FILE,
            '--DEBUG_RECORD_SOCKET_READS',
            '--qt-support',
            '--client',
            localhost,
            '--port',
            str(port),
            '--file',
            writer_thread.TEST_FILE,
        ]

        if debugger_unittest.SHOW_OTHER_DEBUG_INFO:
            print('executing', ' '.join(args))

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(PYDEVD_FILE))

        stdout = []
        stderr = []

        def read(stream, buffer):
            for line in stream.readlines():
                if debugger_unittest.IS_PY3K:
                    line = line.decode('utf-8')

                if debugger_unittest.SHOW_STDOUT:
                    print(line)
                buffer.append(line)

        start_new_thread(read, (process.stdout, stdout))


        if debugger_unittest.SHOW_OTHER_DEBUG_INFO:
            print('Both processes started')

        # polls can fail (because the process may finish and the thread still not -- so, we give it some more chances to
        # finish successfully).
        check = 0
        while True:
            if process.poll() is not None:
                break
            else:
                if not writer_thread.isAlive():
                    check += 1
                    if check == 20:
                        print('Warning: writer thread exited and process still did not.')
                    if check == 100:
                        self.fail_with_message(
                            "The other process should've exited but still didn't (timeout for process to exit).",
                            stdout, stderr, writer_thread
                        )
            time.sleep(.2)


        poll = process.poll()
        if poll < 0:
            self.fail_with_message(
                "The other process exited with error code: " + str(poll), stdout, stderr, writer_thread)


        if stdout is None:
            self.fail_with_message(
                "The other process may still be running -- and didn't give any output.", stdout, stderr, writer_thread)

        if 'TEST SUCEEDED' not in ''.join(stdout):
            self.fail_with_message("TEST SUCEEDED not found in stdout.", stdout, stderr, writer_thread)

        for i in xrange(100):
            if not writer_thread.finishedOk:
                time.sleep(.1)

        if not writer_thread.finishedOk:
            self.fail_with_message(
                "The thread that was doing the tests didn't finish successfully.", stdout, stderr, writer_thread)

    def fail_with_message(self, msg, stdout, stderr, writerThread):
        self.fail(msg+
            "\nStdout: \n"+'\n'.join(stdout)+
            "\nStderr:"+'\n'.join(stderr)+
            "\nLog:\n"+'\n'.join(getattr(writerThread, 'log', [])))


    def testCase1(self):
        self.CheckCase(WriterThreadCase1)

    def testCase2(self):
        self.CheckCase(WriterThreadCase2)

    def testCase3(self):
        self.CheckCase(WriterThreadCase3)

    def testCase4(self):
        self.CheckCase(WriterThreadCase4)

    def testCase5(self):
        self.CheckCase(WriterThreadCase5)

    def testCase6(self):
        self.CheckCase(WriterThreadCase6)

    def testCase7(self):
        self.CheckCase(WriterThreadCase7)

    def testCase8(self):
        self.CheckCase(WriterThreadCase8)

    def testCase9(self):
        self.CheckCase(WriterThreadCase9)

    def testCase10(self):
        self.CheckCase(WriterThreadCase10)

    def testCase11(self):
        self.CheckCase(WriterThreadCase11)

    def testCase12(self):
        self.CheckCase(WriterThreadCase12)

    def testCase13(self):
        self.CheckCase(WriterThreadCase13)

    def testCase14(self):
        self.CheckCase(WriterThreadCase14)

    def testCase15(self):
        self.CheckCase(WriterThreadCase15)

    def testCase16(self):
        self.CheckCase(WriterThreadCase16)

    def testCase17(self):
        self.CheckCase(WriterThreadCase17)

    def testCase17a(self):
        self.CheckCase(WriterThreadCase17a)

    def testCase18(self):
        self.CheckCase(WriterThreadCase18)

    def testCase19(self):
        self.CheckCase(WriterThreadCase19)

    def _has_qt(self):
        try:
            from PySide import QtCore  # @UnresolvedImport
            return True
        except:
            try:
                from PyQt4 import QtCore
                return True
            except:
                pass
        return False

    def testCaseQthread1(self):
        if self._has_qt():
            self.CheckCase(WriterThreadCaseQThread1)

    def testCaseQthread2(self):
        if self._has_qt():
            self.CheckCase(WriterThreadCaseQThread2)

    def testCaseQthread3(self):
        if self._has_qt():
            self.CheckCase(WriterThreadCaseQThread3)


class TestPython(unittest.TestCase, DebuggerBase):
    def getCommandLine(self):
        return [PYTHON_EXE]

class TestJython(unittest.TestCase, DebuggerBase):
    def getCommandLine(self):
        return [
                JAVA_LOCATION,
                '-classpath',
                JYTHON_JAR_LOCATION,
                'org.python.util.jython'
            ]

    # This case requires decorators to work (which are not present on Jython 2.1), so, this test is just removed from the jython run.
    def testCase13(self):
        self.skipTest("Unsupported Decorators")

    # This case requires decorators to work (which are not present on Jython 2.1), so, this test is just removed from the jython run.
    def testCase17(self):
        self.skipTest("Unsupported Decorators")

    def testCase18(self):
        self.skipTest("Unsupported assign to local")

    def testCase16(self):
        self.skipTest("Unsupported numpy")

class TestIronPython(unittest.TestCase, DebuggerBase):
    def getCommandLine(self):
        return [
                IRONPYTHON_EXE,
                '-X:Frames'
            ]

    def testCase3(self):
        self.skipTest("Timing issues") # This test fails once in a while due to timing issues on IronPython, so, skipping it.

    def testCase7(self):
        # This test checks that we start without variables and at each step a new var is created, but on ironpython,
        # the variables exist all at once (with None values), so, we can't test it properly.
        self.skipTest("Different behavior on IronPython")

    def testCase13(self):
        self.skipTest("Unsupported Decorators") # Not sure why it doesn't work on IronPython, but it's not so common, so, leave it be.

    def testCase16(self):
        self.skipTest("Unsupported numpy")

    def testCase18(self):
        self.skipTest("Unsupported assign to local")


def GetLocationFromLine(line):
    loc = line.split('=')[1].strip()
    if loc.endswith(';'):
        loc = loc[:-1]
    if loc.endswith('"'):
        loc = loc[:-1]
    if loc.startswith('"'):
        loc = loc[1:]
    return loc


def SplitLine(line):
    if '=' not in line:
        return None, None
    var = line.split('=')[0].strip()
    return var, GetLocationFromLine(line)




import platform
sysname = platform.system().lower()
test_dependent = os.path.join('../../../', 'org.python.pydev.core', 'tests', 'org', 'python', 'pydev', 'core', 'TestDependent.' + sysname + '.properties')

if os.path.exists(test_dependent):
    f = open(test_dependent)
    try:
        for line in f.readlines():
            var, loc = SplitLine(line)
            if 'PYTHON_EXE' == var:
                PYTHON_EXE = loc

            if 'IRONPYTHON_EXE' == var:
                IRONPYTHON_EXE = loc

            if 'JYTHON_JAR_LOCATION' == var:
                JYTHON_JAR_LOCATION = loc

            if 'JAVA_LOCATION' == var:
                JAVA_LOCATION = loc
    finally:
        f.close()
else:
    pass

if IRONPYTHON_EXE is None:
    sys.stderr.write('Warning: not running IronPython tests.\n')
    class TestIronPython(unittest.TestCase):
        pass

if JAVA_LOCATION is None:
    sys.stderr.write('Warning: not running Jython tests.\n')
    class TestJython(unittest.TestCase):
        pass

# if PYTHON_EXE is None:
PYTHON_EXE = sys.executable


if __name__ == '__main__':
    if False:
        assert PYTHON_EXE, 'PYTHON_EXE not found in %s' % (test_dependent,)
        assert IRONPYTHON_EXE, 'IRONPYTHON_EXE not found in %s' % (test_dependent,)
        assert JYTHON_JAR_LOCATION, 'JYTHON_JAR_LOCATION not found in %s' % (test_dependent,)
        assert JAVA_LOCATION, 'JAVA_LOCATION not found in %s' % (test_dependent,)
        assert os.path.exists(PYTHON_EXE), 'The location: %s is not valid' % (PYTHON_EXE,)
        assert os.path.exists(IRONPYTHON_EXE), 'The location: %s is not valid' % (IRONPYTHON_EXE,)
        assert os.path.exists(JYTHON_JAR_LOCATION), 'The location: %s is not valid' % (JYTHON_JAR_LOCATION,)
        assert os.path.exists(JAVA_LOCATION), 'The location: %s is not valid' % (JAVA_LOCATION,)

    if True:
        #try:
        #    os.remove(r'X:\pydev\plugins\org.python.pydev\pysrc\pydevd.pyc')
        #except:
        #    pass
        suite = unittest.TestSuite()

#         suite.addTests(unittest.makeSuite(TestJython)) # Note: Jython should be 2.2.1
#
#         suite.addTests(unittest.makeSuite(TestIronPython))
#
        suite.addTests(unittest.makeSuite(TestPython))




#         suite.addTest(TestIronPython('testCase18'))
#         suite.addTest(TestIronPython('testCase17'))
#         suite.addTest(TestIronPython('testCase3'))
#         suite.addTest(TestIronPython('testCase7'))
#
#         suite.addTest(TestPython('testCaseQthread1'))
#         suite.addTest(TestPython('testCaseQthread2'))
#         suite.addTest(TestPython('testCaseQthread3'))

#         suite.addTest(TestPython('testCase17a'))


#         suite.addTest(TestJython('testCase1'))
#         suite.addTest(TestPython('testCase2'))
#         unittest.TextTestRunner(verbosity=3).run(suite)
    #     suite.addTest(TestPython('testCase17'))
    #     suite.addTest(TestPython('testCase18'))
    #     suite.addTest(TestPython('testCase19'))

        unittest.TextTestRunner(verbosity=3).run(suite)
