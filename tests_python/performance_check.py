import debugger_unittest
import sys
import re


class WriterThreadPerformance1(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_performance_1.py')
    BENCHMARK_NAME = 'method_calls_with_breakpoint'

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(17, 'method')
        self.WriteMakeInitialRun()
        self.finished_ok = True

class WriterThreadPerformance2(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_performance_1.py')
    BENCHMARK_NAME = 'method_calls_without_breakpoint'

    def run(self):
        self.StartSocket()
        self.WriteMakeInitialRun()
        self.finished_ok = True

class WriterThreadPerformance3(debugger_unittest.AbstractWriterThread):

    TEST_FILE = debugger_unittest._get_debugger_test_file('_performance_1.py')
    BENCHMARK_NAME = 'method_calls_with_step_over'

    def run(self):
        self.StartSocket()
        self.WriteAddBreakpoint(26, None)

        self.WriteMakeInitialRun()
        thread_id, frame_id, line = self.WaitForBreakpointHit('111', True)

        self.WriteStepOver(thread_id)
        thread_id, frame_id, line = self.WaitForBreakpointHit('108', True)

        self.WriteRunThread(thread_id)
        self.finished_ok = True


class CheckDebuggerPerformance(debugger_unittest.DebuggerRunner):

    def get_command_line(self):
        return [sys.executable]

    def _get_time_from_result(self, result):
        stdout = ''.join(result['stdout'])
        match = re.search('TotalTime>>((\d|\.)+)<<', stdout)
        time_taken = match.group(1)
        return float(time_taken)

    def obtain_results(self, writer_thread_class):
        time_when_debugged = self._get_time_from_result(self.check_case(writer_thread_class))

        args = self.get_command_line()
        args.append(writer_thread_class.TEST_FILE)
        regular_time = self._get_time_from_result(self.run_process(args, writer_thread=None))
        print writer_thread_class.BENCHMARK_NAME, time_when_debugged, regular_time


    def check_performance1(self):
        self.obtain_results(WriterThreadPerformance1)

    def check_performance2(self):
        self.obtain_results(WriterThreadPerformance2)

    def check_performance3(self):
        self.obtain_results(WriterThreadPerformance3)

if __name__ == '__main__':
    check_debugger_performance = CheckDebuggerPerformance()
    check_debugger_performance.check_performance1()
    check_debugger_performance.check_performance2()
    check_debugger_performance.check_performance3()
