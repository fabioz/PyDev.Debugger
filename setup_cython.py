from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Cythonize',
    ext_modules=cythonize([
        "_pydevd_bundle/pydevd_cython.pyx",
    ]),
)
