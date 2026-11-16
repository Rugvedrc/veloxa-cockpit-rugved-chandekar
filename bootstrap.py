"""One-command setup:  python bootstrap.py
Creates .venv, installs requirements, builds the database and runs the tests.
Then start the cockpit with:  .venv/Scripts/python cockpit.py serve   (Windows)
                              .venv/bin/python cockpit.py serve       (macOS/Linux)
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

root = Path(__file__).resolve().parent
env = root / ".venv"
if not env.exists():
    venv.create(env, with_pip=True)
py = str(env / ("Scripts" if os.name == "nt" else "bin") / "python")
subprocess.check_call([py, "-m", "pip", "install", "-q", "-r", str(root / "requirements.txt")])
subprocess.check_call([py, str(root / "cockpit.py"), "build"], cwd=root)
subprocess.check_call([py, "-m", "unittest", "discover", "tests"], cwd=root)
print("\nReady. Run:", py, "cockpit.py serve")
