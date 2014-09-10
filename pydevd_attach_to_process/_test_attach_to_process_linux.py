import subprocess
import sys
import os
import time

if __name__ == '__main__':

    linux_dir = os.path.join(os.path.dirname(__file__), 'linux')
    os.chdir(linux_dir)
    so_location = os.path.join(linux_dir, 'attach_linux.so')
    try:
        os.remove(so_location)
    except:
        pass
    subprocess.call('g++ -shared -o attach_linux.so -fPIC -nostartfiles attach_linux.c'.split())
    os.chdir(os.path.dirname(linux_dir))
#     import attach_pydevd
#     attach_pydevd.main(attach_pydevd.process_command_line(['--pid', str(p.pid)]))
    p = subprocess.Popen([sys.executable, '-u', '_always_live_program.py'])
    print('Size of file: %s' % (os.stat(so_location).st_size))
    time.sleep(2)
    p.wait()
