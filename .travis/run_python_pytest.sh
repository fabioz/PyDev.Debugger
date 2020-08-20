if [[ "$PYDEVD_USE_CONDA" != "NO" ]]; then
    source activate build_env
fi

if [[ ("$PYDEVD_PYTHON_VERSION" == "2.6" || "$PYDEVD_PYTHON_VERSION" == "2.7") ]]; then
  # pytest-xdist not available for python == 2.6 and timing out without output with 2.7
    python -m pytest -k test_case_referrers

else
    python -m pytest -n auto -k test_case_referrers

fi