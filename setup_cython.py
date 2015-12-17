from distutils.core import setup
from Cython.Build import cythonize
import shutil
import os

# rem Configure the environment for 64-bit builds.
# rem Use "vcvars32.bat" for a 32-bit build.
# "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\vcvars64.bat"
#
# rem Convince setup.py to use the SDK tools.
# set MSSdk=1
# set DISTUTILS_USE_SDK=1

# c:\bin\Anaconda\Scripts\activate.bat graph
# python setup_cython.py build_ext --inplace


# Note: C:\bin\Anaconda\Lib\distutils\distutils.cfg has
# [build]
# compiler=mingw32
# But it may make the compilation with visual fail!

# TODO: Work in progress
setup(
    name='Cythonize',
    ext_modules=cythonize([
        "_pydevd_bundle/pydevd_trace_dispatch_cython.pyx",
        "_pydevd_bundle/pydevd_additional_thread_info_cython.pyx",
    ]),
)
