'''
Experiments:

// gdb -p 4957
// call dlopen("/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so", 2)
// call dlsym($1, "hello")
// call hello()


// call open("/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so", 2)
// call mmap(0, 6672, 1 | 2 | 4, 1, 3 , 0)
// add-symbol-file
// cat /proc/pid/maps

// call dlopen("/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so", 1|8)
// call dlsym($1, "hello")
// call hello()
'''

import subprocess
import sys
import os
import time


def run_python_code_linux(pid, python_code, connect_debugger_tracing=False):
    assert '\'' not in python_code, 'Having a single quote messes with our command.'
    # Note that the space in the beginning of each line in the multi-line is important!
    cmds = """-eval-command='call PyGILState_Ensure()'
 -eval-command='call PyRun_SimpleString("%s")'
 -eval-command='call PyGILState_Release($1)'""" % python_code
    cmds = cmds.replace('\r\n', '').replace('\r', '').replace('\n', '')

    cmd = 'gdb -p ' + str(pid) + ' -batch ' + cmds
    print cmd

    env = os.environ.copy()
    env.pop('PYTHONIOENCODING', None)
    env.pop('PYTHONPATH', None)

    p = subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print out, err
    return out, err

if __name__ == '__main__':

    linux_dir = os.path.join(os.path.dirname(__file__), 'linux')
    os.chdir(linux_dir)
    so_location = os.path.join(linux_dir, 'attach_linux.so')
    try:
        os.remove(so_location)
    except:
        pass
    subprocess.call('g++ -shared -o attach_linux.so -fPIC -nostartfiles attach_linux.c'.split())
    print('Finished compiling')
    assert os.path.exists('/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so')
    os.chdir(os.path.dirname(linux_dir))
#     import attach_pydevd
#     attach_pydevd.main(attach_pydevd.process_command_line(['--pid', str(p.pid)]))
    p = subprocess.Popen([sys.executable, '-u', '_always_live_program.py'])
    print('Size of file: %s' % (os.stat(so_location).st_size))

    cmd = [
        'gdb',
        '-p',
        str(p.pid),
        '-batch',
        "-eval-command='call dlopen(\"/home/fabioz/Desktop/dev/PyDev.Debugger/pydevd_attach_to_process/linux/attach_linux.so\", 2)'",
#         "-eval-command='call hello()'",
        "-eval-command='call SetSysTraceFunc(1, 0)'",
    ]

    print ' '.join(cmd)
    time.sleep(.5)
#     run_python_code_linux(p.pid, 'print(10)')
    env = os.environ.copy()
    env.pop('PYTHONIOENCODING', None)
    env.pop('PYTHONPATH', None)
    p2 = subprocess.call(' '.join(cmd), env=env, shell=True)

    p.wait()
