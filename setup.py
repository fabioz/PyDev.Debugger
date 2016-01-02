'''
Full setup, used to distribute the debugger backend to PyPi.

Note that this is mostly so that users can do:

pip install pydevd

in a machine for doing remote-debugging, as a local installation with the IDE should have
everything already distributed.

Reference on wheels:
https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
http://lucumr.pocoo.org/2014/1/27/python-on-wheels/

Another (no wheels): https://jamie.curle.io/blog/my-first-experience-adding-package-pypi/

New version: change version and then:
python setup.py bdist_wheel sdist
python setup.py register
twine upload -s dist/pydevd-4.1.0*
'''


from setuptools import setup
from setuptools.dist import Distribution
from distutils.extension import Extension
import os

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False

data_files = []

def accept_file(f):
    f = f.lower()
    for ext in '.py .dll .so .dylib .txt .cpp .h .bat .c .sh'.split():
        if f.endswith(ext):
            return True

    return f in ['reamde', 'makefile']

data_files.append(('pydevd_attach_to_process', [os.path.join('pydevd_attach_to_process', f) for f in os.listdir('pydevd_attach_to_process') if accept_file(f)]))
for root, dirs, files in os.walk("pydevd_attach_to_process"):
    for d in dirs:
        data_files.append((os.path.join(root, d), [os.path.join(root, d, f) for f in os.listdir(os.path.join(root, d)) if accept_file(f)]))

setup(
    name='pydevd',
    version='0.0.1',
    description = 'PyDev.Debugger (used in PyDev and PyCharm)',
    author='Fabio Zadrozny and others',
    url='https://github.com/fabioz/PyDev.Debugger/',
    license='EPL (Eclipse Public License)',
    packages=[
        '_pydev_bundle',
        '_pydev_imps',
        '_pydev_runfiles',
        '_pydevd_bundle',
        'pydev_ipython',

        # 'pydev_sitecustomize', -- Not actually a package (not added)

        # 'pydevd_attach_to_process', -- Not actually a package (included in MANIFEST.in)

        'pydevd_concurrency_analyser',
        'pydevd_plugins',
    ],
    py_modules=[
        # 'interpreterInfo', -- Not needed for debugger
        # 'pycompletionserver', -- Not needed for debugger
        'pydev_app_engine_debug_startup',
        # 'pydev_coverage', -- Not needed for debugger
        # 'pydev_pysrc', -- Not needed for debugger
        'pydev_run_in_console',
        'pydevconsole',
        'pydevd_file_utils',
        'pydevd',
        # 'runfiles', -- Not needed for debugger
        # 'setup_cython', -- Should not be included as a module
        # 'setup', -- Should not be included as a module
    ],
    classifiers=[
        'Development Status :: 6 - Mature',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Eclipse Public License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Debuggers',
    ],
    data_files=data_files,
    keywords=['pydev', 'pydevd', 'pydev.debugger'],
    include_package_data=True,
    zip_safe=False,
    distclass=BinaryDistribution,
    ext_modules=[
        # In this setup, don't even m
        Extension('_pydevd_bundle.pydevd_cython', ["_pydevd_bundle/pydevd_cython.c",])
    ]
)




