from tests_python import debugger_unittest
import sys
import re
import os
from tests_python.debugger_unittest import overrides

CHECK_BASELINE = 'baseline'
CHECK_REGULAR = 'regular'
CHECK_CYTHON = 'cython'
CHECK_FRAME_EVAL = 'frame_eval'
CHECK_SIMPLE_TRACE = 'simple_trace'
CHECK_NO_TRACE = 'no_trace'

pytest_plugins = [
    str('tests_python.debugger_fixtures'),
]

RUNS = 5


class PerformanceWriterThread(debugger_unittest.AbstractWriterThread):

    CHECK = None

    def __init__(self):
        debugger_unittest.AbstractWriterThread.__init__(self)
        if self.CHECK in (CHECK_SIMPLE_TRACE, CHECK_NO_TRACE):
            self.port = -1

    @overrides(debugger_unittest.AbstractWriterThread.get_environ)
    def get_environ(self):
        env = os.environ.copy()
        if self.CHECK == CHECK_BASELINE:
            env['PYTHONPATH'] = r'X:\PyDev.Debugger.baseline'

        elif self.CHECK == CHECK_CYTHON:
            env['PYDEVD_USE_CYTHON'] = 'YES'
            env['PYDEVD_USE_FRAME_EVAL'] = 'NO'

        elif self.CHECK == CHECK_FRAME_EVAL:
            env['PYDEVD_USE_CYTHON'] = 'YES'
            env['PYDEVD_USE_FRAME_EVAL'] = 'YES'

        elif self.CHECK == CHECK_REGULAR:
            env['PYDEVD_USE_CYTHON'] = 'NO'
            env['PYDEVD_USE_FRAME_EVAL'] = 'NO'

        elif self.CHECK in (CHECK_SIMPLE_TRACE, CHECK_NO_TRACE):
            env['PYDEVD_USE_CYTHON'] = 'NO'
            env['PYDEVD_USE_FRAME_EVAL'] = 'NO'

        else:
            raise AssertionError("Don't know what to check.")
        return env

    @overrides(debugger_unittest.AbstractWriterThread.get_pydevd_file)
    def get_pydevd_file(self):
        if self.CHECK == CHECK_BASELINE:
            return os.path.abspath(os.path.join(r'X:\PyDev.Debugger.baseline', 'pydevd.py'))
        dirname = os.path.dirname(__file__)
        dirname = os.path.dirname(dirname)
        return os.path.abspath(os.path.join(dirname, 'pydevd.py'))

    @overrides(debugger_unittest.AbstractWriterThread.update_command_line_args)
    def update_command_line_args(self, args):
        if self.CHECK == CHECK_SIMPLE_TRACE:
            # Run it with the simplest possible tracing function.
            return args[-1:] + ['--simple-trace']

        if self.CHECK == CHECK_NO_TRACE:
            # Just run it directly without any tracing.
            return args[-1:]

        return debugger_unittest.AbstractWriterThread.update_command_line_args(self, args)

    @overrides(debugger_unittest.AbstractWriterThread.run)
    def run(self):
        if self.CHECK in (CHECK_SIMPLE_TRACE, CHECK_NO_TRACE):
            return
        return debugger_unittest.AbstractWriterThread.run(self)

    @overrides(debugger_unittest.AbstractWriterThread.write_make_initial_run)
    def write_make_initial_run(self, *args, **kwargs):
        if self.CHECK in (CHECK_SIMPLE_TRACE, CHECK_NO_TRACE):
            return
        return debugger_unittest.AbstractWriterThread.write_make_initial_run(self, *args, **kwargs)


class CheckDebuggerPerformance(debugger_unittest.DebuggerRunner):

    @overrides(debugger_unittest.DebuggerRunner.get_command_line)
    def get_command_line(self):
        return [sys.executable]

    def _get_time_from_result(self, stdout):
        match = re.search(r'TotalTime>>((\d|\.)+)<<', stdout)
        time_taken = match.group(1)
        return float(time_taken)

    def obtain_results(self, benchmark_name, filename):

        class PerformanceCheck(PerformanceWriterThread):
            TEST_FILE = debugger_unittest._get_debugger_test_file(filename)
            BENCHMARK_NAME = benchmark_name

        writer_thread_class = PerformanceCheck

        runs = RUNS
        all_times = []
        for _ in range(runs):
            stdout_ref = []

            def store_stdout(stdout, stderr):
                stdout_ref.append(stdout)

            kwargs = {}
            if PerformanceCheck.CHECK in (CHECK_SIMPLE_TRACE, CHECK_NO_TRACE):
                kwargs['wait_for_port'] = False

            with self.check_case(writer_thread_class, **kwargs) as writer:
                writer.additional_output_checks = store_stdout
                yield writer

            assert len(stdout_ref) == 1
            all_times.append(self._get_time_from_result(stdout_ref[0]))
            print('partial for: %s: %.3fs' % (writer_thread_class.BENCHMARK_NAME, all_times[-1]))
        if len(all_times) > 3:
            all_times.remove(min(all_times))
            all_times.remove(max(all_times))
        time_when_debugged = sum(all_times) / float(len(all_times))

        args = self.get_command_line()
        args.append(writer_thread_class.TEST_FILE)
        # regular_time = self._get_time_from_result(self.run_process(args, writer_thread=None))
        # simple_trace_time = self._get_time_from_result(self.run_process(args+['--regular-trace'], writer_thread=None))

        if 'SPEEDTIN_AUTHORIZATION_KEY' in os.environ:

            SPEEDTIN_AUTHORIZATION_KEY = os.environ['SPEEDTIN_AUTHORIZATION_KEY']

            # sys.path.append(r'X:\speedtin\pyspeedtin')
            import pyspeedtin  # If the authorization key is there, pyspeedtin must be available
            import pydevd
            pydevd_cython_project_id, pydevd_pure_python_project_id = 6, 7
            if writer_thread_class.CHECK == CHECK_BASELINE:
                project_ids = (pydevd_cython_project_id, pydevd_pure_python_project_id)
            elif writer_thread_class.CHECK == CHECK_REGULAR:
                project_ids = (pydevd_pure_python_project_id,)
            elif writer_thread_class.CHECK == CHECK_CYTHON:
                project_ids = (pydevd_cython_project_id,)
            else:
                raise AssertionError('Wrong check: %s' % (writer_thread_class.CHECK))
            for project_id in project_ids:
                api = pyspeedtin.PySpeedTinApi(authorization_key=SPEEDTIN_AUTHORIZATION_KEY, project_id=project_id)

                benchmark_name = writer_thread_class.BENCHMARK_NAME

                if writer_thread_class.CHECK == CHECK_BASELINE:
                    version = '0.0.1_baseline'
                    return  # No longer commit the baseline (it's immutable right now).
                else:
                    version = pydevd.__version__,

                commit_id, branch, commit_date = api.git_commit_id_branch_and_date_from_path(pydevd.__file__)
                api.add_benchmark(benchmark_name)
                api.add_measurement(
                    benchmark_name,
                    value=time_when_debugged,
                    version=version,
                    released=False,
                    branch=branch,
                    commit_id=commit_id,
                    commit_date=commit_date,
                )
                api.commit()

        self.performance_msg = '%s: %.3fs ' % (writer_thread_class.BENCHMARK_NAME, time_when_debugged)

    def method_calls_with_breakpoint(self):
        for writer in self.obtain_results('method_calls_with_breakpoint', '_performance_1.py'):
            bline = writer.get_line_index_with_content('Unreachable breakpoint here')
            writer.write_add_breakpoint(bline, 'method')
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg

    def method_calls_without_breakpoint_performance1(self):
        for writer in self.obtain_results('method_calls_without_breakpoint_performance1', '_performance_1.py'):
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg

    def method_calls_without_breakpoint_performance2(self):
        for writer in self.obtain_results('method_calls_without_breakpoint_performance2', '_performance_2.py'):
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg

    def method_calls_without_breakpoint_performance3(self):
        for writer in self.obtain_results('method_calls_without_breakpoint_performance3', '_performance_3.py'):
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg

    def method_calls_with_step_over(self):
        for writer in self.obtain_results('method_calls_with_step_over', '_performance_1.py'):
            bline = writer.get_line_index_with_content('Initial breakpoint for a step-over here')
            writer.write_add_breakpoint(bline, None)

            writer.write_make_initial_run()
            hit = writer.wait_for_breakpoint_hit('111')

            writer.write_step_over(hit.thread_id)
            hit = writer.wait_for_breakpoint_hit('108')

            writer.write_run_thread(hit.thread_id)
            writer.finished_ok = True

        return self.performance_msg

    def method_calls_with_exception_breakpoint(self):
        for writer in self.obtain_results('method_calls_with_exception_breakpoint', '_performance_1.py'):
            writer.write_add_exception_breakpoint('ValueError')
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg

    def global_scope_1_with_breakpoint(self):
        for writer in self.obtain_results('global_scope_1_with_breakpoint', '_performance_2.py'):
            writer.write_add_breakpoint(writer.get_line_index_with_content('Breakpoint here'), None)
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg

    def global_scope_2_with_breakpoint(self):
        for writer in self.obtain_results('global_scope_2_with_breakpoint', '_performance_3.py'):
            bline = writer.get_line_index_with_content('Breakpoint here')
            writer.write_add_breakpoint(bline, None)
            writer.write_make_initial_run()
            writer.finished_ok = True

        return self.performance_msg


if __name__ == '__main__':
    # Local times gotten (python 3.6)
    # Checking: regular
    # method_calls_with_breakpoint: 1.124s
    # method_calls_with_step_over: 2.618s
    # method_calls_with_exception_breakpoint: 0.225s
    # global_scope_1_with_breakpoint: 0.277s
    # global_scope_2_with_breakpoint: 3.006s

    # Checking: cython
    # method_calls_with_breakpoint: 0.552s
    # method_calls_with_step_over: 1.093s
    # method_calls_with_exception_breakpoint: 0.179s
    # global_scope_1_with_breakpoint: 0.287s
    # global_scope_2_with_breakpoint: 1.398s

    # Checking: frame_eval
    # method_calls_with_breakpoint: 0.125s
    # method_calls_with_step_over: 0.131s
    # method_calls_with_exception_breakpoint: 0.130s
    # global_scope_1_with_breakpoint: 0.826s
    # global_scope_2_with_breakpoint: 0.187s

    # Checking: regular
    # method_calls_without_breakpoint_performance1: 0.222s
    # method_calls_without_breakpoint_performance2: 0.281s
    # method_calls_without_breakpoint_performance3: 0.183s

    # Checking: cython
    # method_calls_without_breakpoint_performance1: 0.157s
    # method_calls_without_breakpoint_performance2: 0.290s
    # method_calls_without_breakpoint_performance3: 0.183s

    # Checking: frame_eval
    # method_calls_without_breakpoint_performance1: 0.147s
    # method_calls_without_breakpoint_performance2: 0.844s
    # method_calls_without_breakpoint_performance3: 0.184s

    # Checking: simple_trace
    # method_calls_without_breakpoint_performance1: 0.093s
    # method_calls_without_breakpoint_performance2: 0.205s
    # method_calls_without_breakpoint_performance3: 0.186s

    # Checking: no_trace
    # method_calls_without_breakpoint_performance1: 0.016s
    # method_calls_without_breakpoint_performance2: 0.290s
    # method_calls_without_breakpoint_performance3: 0.189s
    # TotalTime for profile: 218.58s

    debugger_unittest.SHOW_WRITES_AND_READS = False
    debugger_unittest.SHOW_OTHER_DEBUG_INFO = False
    debugger_unittest.SHOW_STDOUT = False

    import time
    start_time = time.time()

    msgs = []
    for check in (
            # CHECK_BASELINE, -- Checks against the version checked out at X:\PyDev.Debugger.baseline.
            CHECK_REGULAR,
            CHECK_CYTHON,
            CHECK_FRAME_EVAL,
        ):
        PerformanceWriterThread.CHECK = check
        msgs.append('Checking: %s' % (check,))
        check_debugger_performance = CheckDebuggerPerformance()
        msgs.append(check_debugger_performance.method_calls_with_breakpoint())
        msgs.append(check_debugger_performance.method_calls_with_step_over())
        msgs.append(check_debugger_performance.method_calls_with_exception_breakpoint())
        msgs.append(check_debugger_performance.global_scope_1_with_breakpoint())
        msgs.append(check_debugger_performance.global_scope_2_with_breakpoint())

    for check in (
            # CHECK_BASELINE, -- Checks against the version checked out at X:\PyDev.Debugger.baseline.
            CHECK_REGULAR,
            CHECK_CYTHON,
            CHECK_FRAME_EVAL,
            CHECK_SIMPLE_TRACE,
            CHECK_NO_TRACE,
        ):
        PerformanceWriterThread.CHECK = check
        msgs.append('Checking: %s' % (check,))
        check_debugger_performance = CheckDebuggerPerformance()
        msgs.append(check_debugger_performance.method_calls_without_breakpoint_performance1())
        msgs.append(check_debugger_performance.method_calls_without_breakpoint_performance2())
        msgs.append(check_debugger_performance.method_calls_without_breakpoint_performance3())

    for msg in msgs:
        print(msg)

    print('TotalTime for profile: %.2fs' % (time.time() - start_time,))
