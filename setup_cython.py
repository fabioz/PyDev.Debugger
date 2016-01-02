'''
A simpler setup version just to compile the speedup module.

It should be used as:

python setup_cython build_ext --inplace
'''

import sys
target_pydevd_name = 'pydevd_cython'
for i, arg in enumerate(sys.argv[:]):
    if arg.startswith('--target-pyd-name='):
        del sys.argv[i]
        raise AssertionError('finish this')


from setuptools import setup

try:
    from Cython.Build import cythonize
    import os
    # If we don't have the pyx nor cython, compile the .c
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "_pydevd_bundle", "pydevd_cython.pyx")):
        raise ImportError()
except ImportError:
    from distutils.extension import Extension
    ext_modules = [Extension('_pydevd_bundle.pydevd_cython', [
        "_pydevd_bundle/pydevd_cython.c",
    ])]
else:
    ext_modules = cythonize([
        "_pydevd_bundle/pydevd_cython.pyx",
    ])

setup(
    name='Cythonize',
    ext_modules=ext_modules
)
