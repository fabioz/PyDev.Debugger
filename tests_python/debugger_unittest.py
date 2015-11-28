from _pydev_bundle.pydev_imports import quote_plus, quote, unquote_plus
from _pydevd_bundle.pydevd_constants import IS_PY3K

import socket
import os
import threading
import time
from _pydev_bundle import pydev_localhost

CMD_SET_PROPERTY_TRACE, CMD_EVALUATE_CONSOLE_EXPRESSION, CMD_RUN_CUSTOM_OPERATION, CMD_ENABLE_DONT_TRACE = 133, 134, 135, 141

SHOW_WRITES_AND_READS = False
SHOW_OTHER_DEBUG_INFO = False
SHOW_STDOUT = False


#=======================================================================================================================
# ReaderThread
#=======================================================================================================================
class ReaderThread(threading.Thread):

    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.sock = sock
        self.lastReceived = ''

    def run(self):
        last_printed = None
        try:
            buf = ''
            while True:
                l = self.sock.recv(1024)
                if IS_PY3K:
                    l = l.decode('utf-8')
                buf += l

                if '\n' in buf:
                    self.lastReceived = buf
                    buf = ''

                if SHOW_WRITES_AND_READS:
                    if last_printed != self.lastReceived.strip():
                        last_printed = self.lastReceived.strip()
                        print('Test Reader Thread Received %s' % last_printed)
        except:
            pass  # ok, finished it

    def DoKill(self):
        self.sock.close()



#=======================================================================================================================
# AbstractWriterThread
#=======================================================================================================================
class AbstractWriterThread(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.finishedOk = False
        self._next_breakpoint_id = 0
        self.log = []
        self.port = port


    def DoKill(self):
        if hasattr(self, 'readerThread'):
            # if it's not created, it's not there...
            self.readerThread.DoKill()
        self.sock.close()

    def Write(self, s):

        last = self.readerThread.lastReceived
        if SHOW_WRITES_AND_READS:
            print('Test Writer Thread Written %s' % (s,))
        msg = s + '\n'
        if IS_PY3K:
            msg = msg.encode('utf-8')
        self.sock.send(msg)
        time.sleep(0.2)

        i = 0
        while last == self.readerThread.lastReceived and i < 10:
            i += 1
            time.sleep(0.1)


    def StartSocket(self):
        if SHOW_WRITES_AND_READS:
            print('StartSocket')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.port))
        s.listen(1)
        if SHOW_WRITES_AND_READS:
            print('Waiting in socket.accept()')
        newSock, addr = s.accept()
        if SHOW_WRITES_AND_READS:
            print('Test Writer Thread Socket:', newSock, addr)

        readerThread = self.readerThread = ReaderThread(newSock)
        readerThread.start()
        self.sock = newSock

        self._sequence = -1
        # initial command is always the version
        self.WriteVersion()
        self.log.append('StartSocket')

    def NextBreakpointId(self):
        self._next_breakpoint_id += 1
        return self._next_breakpoint_id

    def NextSeq(self):
        self._sequence += 2
        return self._sequence


    def WaitForNewThread(self):
        i = 0
        # wait for hit breakpoint
        while not '<xml><thread name="' in self.readerThread.lastReceived or '<xml><thread name="pydevd.' in self.readerThread.lastReceived:
            i += 1
            time.sleep(1)
            if i >= 15:
                raise AssertionError('After %s seconds, a thread was not created.' % i)

        # we have something like <xml><thread name="MainThread" id="12103472" /></xml>
        splitted = self.readerThread.lastReceived.split('"')
        threadId = splitted[3]
        return threadId

    def WaitForBreakpointHit(self, reason='111', get_line=False):
        '''
            108 is over
            109 is return
            111 is breakpoint
        '''
        self.log.append('Start: WaitForBreakpointHit')
        i = 0
        # wait for hit breakpoint
        last = self.readerThread.lastReceived
        while not ('stop_reason="%s"' % reason) in last:
            i += 1
            time.sleep(1)
            last = self.readerThread.lastReceived
            if i >= 10:
                raise AssertionError('After %s seconds, a break with reason: %s was not hit. Found: %s' % \
                    (i, reason, last))

        # we have something like <xml><thread id="12152656" stop_reason="111"><frame id="12453120" ...
        splitted = last.split('"')
        threadId = splitted[1]
        frameId = splitted[7]
        if get_line:
            self.log.append('End(0): WaitForBreakpointHit')
            return threadId, frameId, int(splitted[13])

        self.log.append('End(1): WaitForBreakpointHit')
        return threadId, frameId

    def WaitForCustomOperation(self, expected):
        i = 0
        # wait for custom operation response, the response is double encoded
        expectedEncoded = quote(quote_plus(expected))
        while not expectedEncoded in self.readerThread.lastReceived:
            i += 1
            time.sleep(1)
            if i >= 10:
                raise AssertionError('After %s seconds, the custom operation not received. Last found:\n%s\nExpected (encoded)\n%s' %
                    (i, self.readerThread.lastReceived, expectedEncoded))

        return True

    def WaitForEvaluation(self, expected):
        return self._WaitFor(expected, 'the expected evaluation was not found')


    def WaitForVars(self, expected):
        i = 0
        # wait for hit breakpoint
        while not expected in self.readerThread.lastReceived:
            i += 1
            time.sleep(1)
            if i >= 10:
                raise AssertionError('After %s seconds, the vars were not found. Last found:\n%s' %
                    (i, self.readerThread.lastReceived))

        return True

    def WaitForVar(self, expected):
        self._WaitFor(expected, 'the var was not found')

    def _WaitFor(self, expected, error_msg):
        '''
        :param expected:
            If a list we'll work with any of the choices.
        '''
        if not isinstance(expected, (list, tuple)):
            expected = [expected]

        i = 0
        found = False
        while not found:
            last = self.readerThread.lastReceived
            for e in expected:
                if e in last:
                    found = True
                    break

            last = unquote_plus(last)
            for e in expected:
                if e in last:
                    found = True
                    break

            if found:
                break

            i += 1
            time.sleep(1)
            if i >= 10:
                raise AssertionError('After %s seconds, %s. Last found:\n%s' %
                    (i, error_msg, last))

        return True

    def WaitForMultipleVars(self, expected_vars):
        i = 0
        # wait for hit breakpoint
        while True:
            for expected in expected_vars:
                if expected not in self.readerThread.lastReceived:
                    break  # Break out of loop (and don't get to else)
            else:
                return True

            i += 1
            time.sleep(1)
            if i >= 10:
                raise AssertionError('After %s seconds, the vars were not found. Last found:\n%s' %
                    (i, self.readerThread.lastReceived))

        return True

    def WriteMakeInitialRun(self):
        self.Write("101\t%s\t" % self.NextSeq())
        self.log.append('WriteMakeInitialRun')

    def WriteVersion(self):
        self.Write("501\t%s\t1.0\tWINDOWS\tID" % self.NextSeq())

    def WriteAddBreakpoint(self, line, func):
        '''
            @param line: starts at 1
        '''
        breakpoint_id = self.NextBreakpointId()
        self.Write("111\t%s\t%s\t%s\t%s\t%s\t%s\tNone\tNone" % (self.NextSeq(), breakpoint_id, 'python-line', self.TEST_FILE, line, func))
        self.log.append('WriteAddBreakpoint: %s line: %s func: %s' % (breakpoint_id, line, func))
        return breakpoint_id

    def WriteRemoveBreakpoint(self, breakpoint_id):
        self.Write("112\t%s\t%s\t%s\t%s" % (self.NextSeq(), 'python-line', self.TEST_FILE, breakpoint_id))

    def WriteChangeVariable(self, thread_id, frame_id, varname, value):
        self.Write("117\t%s\t%s\t%s\t%s\t%s\t%s" % (self.NextSeq(), thread_id, frame_id, 'FRAME', varname, value))

    def WriteGetFrame(self, threadId, frameId):
        self.Write("114\t%s\t%s\t%s\tFRAME" % (self.NextSeq(), threadId, frameId))
        self.log.append('WriteGetFrame')

    def WriteGetVariable(self, threadId, frameId, var_attrs):
        self.Write("110\t%s\t%s\t%s\tFRAME\t%s" % (self.NextSeq(), threadId, frameId, var_attrs))

    def WriteStepOver(self, threadId):
        self.Write("108\t%s\t%s" % (self.NextSeq(), threadId,))

    def WriteStepIn(self, threadId):
        self.Write("107\t%s\t%s" % (self.NextSeq(), threadId,))

    def WriteStepReturn(self, threadId):
        self.Write("109\t%s\t%s" % (self.NextSeq(), threadId,))

    def WriteSuspendThread(self, threadId):
        self.Write("105\t%s\t%s" % (self.NextSeq(), threadId,))

    def WriteRunThread(self, threadId):
        self.log.append('WriteRunThread')
        self.Write("106\t%s\t%s" % (self.NextSeq(), threadId,))

    def WriteKillThread(self, threadId):
        self.Write("104\t%s\t%s" % (self.NextSeq(), threadId,))

    def WriteDebugConsoleExpression(self, locator):
        self.Write("%s\t%s\t%s" % (CMD_EVALUATE_CONSOLE_EXPRESSION, self.NextSeq(), locator))

    def WriteCustomOperation(self, locator, style, codeOrFile, operation_fn_name):
        self.Write("%s\t%s\t%s||%s\t%s\t%s" % (CMD_RUN_CUSTOM_OPERATION, self.NextSeq(), locator, style, codeOrFile, operation_fn_name))

    def WriteEvaluateExpression(self, locator, expression):
        self.Write("113\t%s\t%s\t%s\t1" % (self.NextSeq(), locator, expression))

    def WriteEnableDontTrace(self, enable):
        if enable:
            enable = 'true'
        else:
            enable = 'false'
        self.Write("%s\t%s\t%s" % (CMD_ENABLE_DONT_TRACE, self.NextSeq(), enable))

def _get_debugger_test_file(filename):
    try:
        rPath = os.path.realpath  # @UndefinedVariable
    except:
        # jython does not support os.path.realpath
        # realpath is a no-op on systems without islink support
        rPath = os.path.abspath

    return os.path.normcase(rPath(os.path.join(os.path.dirname(__file__), filename)))

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((pydev_localhost.get_localhost(), 0))
    _, port = s.getsockname()
    s.close()
    return port