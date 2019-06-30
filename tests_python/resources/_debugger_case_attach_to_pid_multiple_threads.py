
import time
try:
    import _thread
except:
    import thread as _thread

if __name__ == '__main__':

    lock = _thread.allocate_lock()
    initialized = [False]

    def new_thread_function():
        wait = True

        with lock:
            initialized[0] = True
            while wait:  # break 2 here
                time.sleep(1 / 100.)

    _thread.start_new_thread(new_thread_function, ())

    wait = True

    while not initialized[0]:
        time.sleep(1)

    with lock:  # It'll be here until the secondary thread finishes (i.e.: releases the lock).
        pass

    import threading  # Only import threading at the end!
    assert isinstance(threading.current_thread(), threading._MainThread)

    print('TEST SUCEEDED')  # break 1 here
