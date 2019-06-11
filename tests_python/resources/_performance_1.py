import time

try:
    xrange
except:
    xrange = range


def method2():
    i = 1


def method():

    for i in xrange(200000):
        method2()

        if False:
            # Unreachable breakpoint here
            pass


def caller():
    start_time = time.time()
    method()
    print('TotalTime>>%s<<' % (time.time() - start_time,))


if __name__ == '__main__':
    import sys
    if '--simple-trace' in sys.argv:

        def trace_dispatch(frame, event, arg):
            if event == 'call':
                if frame.f_trace is not None:
                    return frame.f_trace(frame, event, arg)

            return None

        sys.settrace(trace_dispatch)

    caller()  # Initial breakpoint for a step-over here
    print('TEST SUCEEDED')
