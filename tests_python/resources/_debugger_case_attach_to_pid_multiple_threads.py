
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
            while wait:  # break thread here
                time.sleep(1 / 100.)

    _thread.start_new_thread(new_thread_function, ())

    wait = True

    while not initialized[0]:
        time.sleep(1)

    with lock:  # It'll be here until the secondary thread finishes (i.e.: releases the lock).
        pass

    import threading  # Note: only import after the attach.
    if hasattr(threading, 'main_thread'):
        assert threading.current_thread().ident == threading.main_thread().ident
    else:
        # Python 2 does not have main_thread, but we can still get the reference.
        assert threading.current_thread().ident == threading._shutdown.im_self.ident

    print('TEST SUCEEDED')
