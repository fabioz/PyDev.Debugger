import sys
import os 
if __name__ == '__main__':
    print('pid:%s' % (os.getpid()))
    i = 0
    while True:
        i += 1
        import time
        time.sleep(.5)
        sys.stdout.write('.')
        sys.stdout.flush()
        if i % 40 == 0:
            sys.stdout.write('\n')
            sys.stdout.flush()
