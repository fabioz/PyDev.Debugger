import os

import pydevd_file_utils


def test_normalize_case_does_not_split_dot_zipx_directory(tmpdir):
    zipx_dir = tmpdir.mkdir(".zipx")
    filename = str(zipx_dir.join("main.py"))
    zipx_dir.join("main.py").write("print('ok')\n")

    expected = os.path.abspath(filename)
    assert pydevd_file_utils._apply_func_and_normalize_case(filename, os.path.abspath, True, False) == expected
