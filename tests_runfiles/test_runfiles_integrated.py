import os
from subprocess import CompletedProcess
import subprocess
import sys
from typing import Union, Literal, Optional, Dict


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


def test_runfiles_integrated():
    project_rootdir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cwd = os.path.join(project_rootdir, "tests_runfiles", "samples_integrated")
    runfiles = os.path.join(project_rootdir, "runfiles.py")
    assert os.path.exists(cwd), f"{cwd} does not exist."
    completed = python_run(["-Xfrozen_modules=off", runfiles, cwd], returncode=0, cwd=cwd)
    print(completed.stdout.decode("utf-8"))
    print(completed.stderr.decode("utf-8"))
