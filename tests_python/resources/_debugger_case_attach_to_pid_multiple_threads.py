# Note: multiple threads but no threading import!

import time
try:
    import _thread
except:
    import thread as _thread

if __name__ == '__main__':

    def new_thread_function():
        wait = True

        while wait:
            time.sleep(1 / 100.)

    _thread.start_new_thread(new_thread_function, ())

    wait = True

    while wait:
        time.sleep(22)  # break here

    print('TEST SUCEEDED')
