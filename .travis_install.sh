#!/bin/bash
set -ev

conda install --yes numpy ipython cython pytest psutil

if [ "$TRAVIS_PYTHON_VERSION" = "2.7" ]; then
    conda install --yes pyqt=4
fi
if [ "$TRAVIS_PYTHON_VERSION" = "3.5" ]; then
    conda install --yes pyqt=5
fi