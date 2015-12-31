'''
Creating the needed environments for creating the pre-compiled distribution on Windods:

1. Download:

* conda32 at C:\tools\Miniconda32

* conda64 at C:\tools\Miniconda

Create the environments:

C:\tools\Miniconda32\Scripts\conda create -y -f -n py27_32 python=2.7 cython numpy nose ipython pip
C:\tools\Miniconda32\Scripts\activate py27_32
pip install "django>=1.7,<1.8"
deactivate

C:\tools\Miniconda32\Scripts\conda create -y -f -n py34_32 python=3.4 cython numpy nose ipython pip
C:\tools\Miniconda32\Scripts\activate py34_32
pip install "django>=1.9"
deactivate

C:\tools\Miniconda32\Scripts\conda create -y -f -n py35_32 python=3.5 cython numpy nose ipython pip
C:\tools\Miniconda32\Scripts\activate py35_32
pip install "django>=1.9"
deactivate

C:\tools\Miniconda\Scripts\conda create -y -f -n py27_64 python=2.7 cython numpy nose ipython pip
C:\tools\Miniconda\Scripts\activate py27_64
pip install "django>=1.7,<1.8"
deactivate

C:\tools\Miniconda\Scripts\conda create -y -f -n py34_64 python=3.4 cython numpy nose ipython pip
C:\tools\Miniconda\Scripts\activate py34_64
pip install "django>=1.9"
deactivate

C:\tools\Miniconda\Scripts\conda create -y -f -n py35_64 python=3.5 cython numpy nose ipython pip
C:\tools\Miniconda\Scripts\activate py35_64
pip install "django>=1.9"
deactivate


'''

from __future__ import unicode_literals
import os



python_installations = [
    r'C:\tools\Miniconda32\envs\py27_32\python.exe',
    r'C:\tools\Miniconda32\envs\py34_32\python.exe',
    r'C:\tools\Miniconda32\envs\py35_32\python.exe',

    r'C:\tools\Miniconda\envs\py27_64\python.exe',
    r'C:\tools\Miniconda\envs\py34_64\python.exe',
    r'C:\tools\Miniconda\envs\py35_64\python.exe',
]

def main():
    from generate_code import generate_dont_trace_files
    from generate_code import generate_cython_module

    # First, make sure that our code is up to date.
    generate_dont_trace_files()
    generate_cython_module()

    for python_install in python_installations:
        assert os.path.exists(python_install)


if __name__ == '__main__':
    main()

