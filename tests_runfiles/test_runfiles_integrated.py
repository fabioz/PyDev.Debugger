import os
from subprocess import CompletedProcess
import subprocess
import sys
from typing import Union, Literal, Optional, Dict
import json


def python_run(
    cmdline,
    returncode: Union[Literal["error"], Literal["any"], int],
    cwd=None,
    additional_env: Optional[Dict[str, str]] = None,
    timeout=None,
) -> CompletedProcess:
    cp = os.environ.copy()
    cp["PYTHONPATH"] = os.pathsep.join([x for x in sys.path if x])
    if additional_env:
        cp.update(additional_env)
    args = [sys.executable] + cmdline
    result = subprocess.run(args, capture_output=True, env=cp, cwd=cwd, timeout=timeout)

    if returncode == "any":
        return result

    if returncode == "error" and result.returncode:
        return result

    if result.returncode == returncode:
        return result

    # This is a bit too verbose, so, commented out for now.
    # env_str = "\n".join(str(x) for x in sorted(cp.items()))

    raise AssertionError(
        f"""Expected returncode: {returncode}. Found: {result.returncode}.
=== stdout:
{result.stdout.decode('utf-8')}

=== stderr:
{result.stderr.decode('utf-8')}

=== Args:
{args}

"""
    )


project_rootdir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cwd = os.path.join(project_rootdir, "tests_runfiles", "samples_integrated")
runfiles = os.path.join(project_rootdir, "runfiles.py")
test_in_root = os.path.join(cwd, "root", "test_in_root.py")

assert os.path.exists(cwd), f"{cwd} does not exist."
assert os.path.exists(runfiles), f"{runfiles} does not exist."
assert os.path.exists(test_in_root), f"{test_in_root} does not exist."
assert os.path.exists(project_rootdir), f"{project_rootdir} does not exist."


env_filter_1 = {
    "PYDEV_RUNFILES_FILTER_TESTS": json.dumps(
        {
            "include": [
                [
                    test_in_root,
                    "*",
                ]
            ],
            "exclude": [
                [
                    test_in_root,
                    "test1",
                ]
            ],
        }
    )
}

env_filter_2 = {
    "PYDEV_RUNFILES_FILTER_TESTS": json.dumps(
        {
            "include": [
                [
                    test_in_root,
                    "MyTest",
                ],
                [
                    test_in_root,
                    "test1",
                ],
            ],
            "exclude": [
                [
                    test_in_root,
                    "test2",
                ]
            ],
        }
    )
}


def test_runfiles_integrated():
    completed = python_run(["-Xfrozen_modules=off", runfiles, cwd], returncode=0, cwd=cwd, additional_env=env_filter_2)
    print(completed.stdout.decode("utf-8"))
    print(completed.stderr.decode("utf-8"))
