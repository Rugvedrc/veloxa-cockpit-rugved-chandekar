"""One-command setup and check:

    python bootstrap.py --data path/to/Veloxa_Hackathon_Release_Packs.zip --serve

Creates .venv, installs requirements, builds the databases from the data room (the folder or
the .zip; remembered afterwards), runs the automated test set and, with --serve, starts the
cockpit at http://127.0.0.1:8765. Without --serve it stops after the tests. Python 3.9 or newer.
Afterwards:  <venv python> cockpit.py serve     then open http://127.0.0.1:8765
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

root = Path(__file__).resolve().parent
env = root / ".venv"
args = sys.argv[1:]
data = args[args.index("--data") + 1] if "--data" in args else None

if sys.version_info < (3, 9):
    sys.exit("Python 3.9 or newer is required.")
if not env.exists():
    venv.create(env, with_pip=True)
py = str(env / ("Scripts" if os.name == "nt" else "bin") / "python")
subprocess.check_call([py, "-m", "pip", "install", "-q", "-r", str(root / "requirements.txt")])

child = dict(os.environ)
if data:
    child["VELOXA_DATA"] = str(Path(data).expanduser().resolve())
for step in (["cockpit.py", "build"], ["cockpit.py", "test"]):
    if subprocess.call([py, *step], cwd=root, env=child) != 0:
        sys.exit(f"Setup failed at: {' '.join(step)}")
if "--serve" in args:  # one command that sets up, tests and runs: open http://127.0.0.1:8765
    print("\nSetup and tests passed. Starting the cockpit at http://127.0.0.1:8765 (Ctrl+C to stop)")
    sys.exit(subprocess.call([py, "cockpit.py", "serve"], cwd=root, env=child))
print(f"\nReady. Start the cockpit with:\n  {py} cockpit.py serve\n(or run the whole thing in one go: python bootstrap.py --data <zip> --serve)")
