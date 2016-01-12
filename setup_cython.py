'''
A simpler setup version just to compile the speedup module.

It should be used as:

python setup_cython build_ext --inplace

Note: the .c file and other generated files are regenerated from
the .pyx file by running "python build_tools/build.py"
'''

import sys
target_pydevd_name = 'pydevd_cython'
for i, arg in enumerate(sys.argv[:]):
    if arg.startswith('--target-pyd-name='):
        del sys.argv[i]
        target_pydevd_name = arg[len('--target-pyd-name='):]


from setuptools import setup

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))


c_file = os.path.join(os.path.dirname(__file__), "_pydevd_bundle", "pydevd_cython.c")

if target_pydevd_name != 'pydevd_cython':
    import shutil
    new_c_file = os.path.join(os.path.dirname(__file__), "_pydevd_bundle", "%s.c" % (target_pydevd_name,))
    shutil.copy(c_file, new_c_file)

try:
    # Always compile the .c (and not the .pyx) file (which we should keep up-to-date by running build_tools/build.py).
    from distutils.extension import Extension
    ext_modules = [Extension('_pydevd_bundle.%s' % (target_pydevd_name,), [
        "_pydevd_bundle/%s.c" % (target_pydevd_name,),
    ])]

    setup(
        name='Cythonize',
        ext_modules=ext_modules
    )
finally:
    if target_pydevd_name != 'pydevd_cython':
        try:
            os.remove(new_c_file)
        except:
            import traceback
            traceback.print_exc()
