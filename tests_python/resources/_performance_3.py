import time
import sys

if '--simple-trace' in sys.argv or True:

    def trace_dispatch(frame, event, arg):
        if event == 'call':
            if frame.f_trace is not None:
                return frame.f_trace(frame, event, arg)

        return None

    sys.settrace(trace_dispatch)

start_time = time.time()

try:
    xrange  # @UndefinedVariable
except NameError:
    xrange = range

# do some busy work in parallel
print("Started main task")
x = 0
for i in xrange(1000000):
    x += 1
print("Completed main task")

if False:
    pass  # Breakpoint here

print('TotalTime>>%s<<' % (time.time() - start_time,))
print('TEST SUCEEDED')
