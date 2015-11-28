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
    print('TotalTime>>%s<<' % (time.time()-start_time,))

if __name__ == '__main__':
    caller() # Initial breakpoint for a step-over here
    print('TEST SUCEEDED')
