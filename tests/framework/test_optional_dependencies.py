import subprocess
import sys


def test_conftest_loads_without_importing_playwright():
    code = r"""
import builtins
import runpy

original_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "playwright" or name.startswith("playwright."):
        raise ImportError("playwright intentionally unavailable")
    return original_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
runpy.run_path("conftest.py")
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
