import time

# See: https://github.com/microsoft/ptvsd/issues/1542 (If threading is not imported in main thread,
# attach to pid does not work properly).
import threading

if __name__ == '__main__':
    wait = True

    while wait:
        time.sleep(1)  # break here

    print('TEST SUCEEDED')
