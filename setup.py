# Reference on wheels:
# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
# http://lucumr.pocoo.org/2014/1/27/python-on-wheels/
from setuptools import setup
from setuptools.dist import Distribution

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False

args = dict(
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

        #'pydev_sitecustomize', -- Not actually a package

        # 'pydevd_attach_to_process', -- Not actually a package

        'pydevd_concurrency_analyser',
        'pydevd_plugins',
    ],
    py_modules=[
        'interpreterInfo',
        'pycompletionserver',
        'pydev_app_engine_debug_startup',
        'pydev_coverage',
        'pydev_pysrc',
        'pydev_run_in_console',
        'pydevconsole',
        'pydevd_file_utils',
        'pydevd',
        'runfiles',
        'setup_cython',
        'setup',
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
    keywords=['pydev', 'pydevd', 'pydev.debugger'],
    include_package_data=True,
    zip_safe=False,
    distclass=BinaryDistribution,
)

try:
    from Cython.Build import cythonize
except ImportError:
    pass
else:
    args['ext_modules'] = cythonize([
        "_pydevd_bundle/pydevd_cython.pyx",
    ])

setup(**args)

# Note: nice reference: https://jamie.curle.io/blog/my-first-experience-adding-package-pypi/
# New version: change version and then:
# python setup.py sdist
# python setup.py sdist register upload

