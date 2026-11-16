"""Veloxa cockpit command line.

  python cockpit.py build [--as-of 2026-11-18]   rebuild the database from the data room
  python cockpit.py ask "how many people?"
  python cockpit.py worry
  python cockpit.py interview VX007 "what keeps you up?"
  python cockpit.py serve                 web UI at http://127.0.0.1:8765
"""
import sys
from datetime import date

from cockpit import agents, checks, loaders, resolve
from cockpit.ask import ask
from cockpit.db import DATA_DIR, connect, rebuild
from cockpit.loaders import load_all


def build(as_of=None):
    """as_of defaults to today (never earlier than the Day 1 drop), so files from drops that
    have not been released yet are ignored even if they are already sitting in the folder."""
    if not DATA_DIR.exists():
        sys.exit(f"Data room not found at {DATA_DIR}. Set VELOXA_DATA to the Veloxa_Hackathon_Release_Packs folder.")
    loaders.AS_OF = as_of or max(date.today().isoformat(), "2026-11-16")
    print(f"Building as of {loaders.AS_OF}")
    con = rebuild()
    load_all(con)
    resolve.load_entities(con)
    resolve.load_claims(con)
    checks.run_all(con)
    con.commit()
    for t in ("source", "person", "payroll", "gl_entry", "board_update", "message", "document", "claim", "finding"):
        print(f"  {t:13} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>4} rows")


def show(r):
    print(r["answer"])
    for c in r["cites"]:
        print("  source:", c)
    for c in r["caveats"]:
        print("  caveat:", c)
    print("  confidence:", r["confidence"])


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "build":
        return build(argv[argv.index("--as-of") + 1] if "--as-of" in argv else None)
    if cmd == "serve":
        from cockpit.server import serve
        return serve()
    con = connect()
    if cmd == "ask":
        return show(ask(con, " ".join(argv[2:])))
    if cmd == "worry":
        for f in con.execute("SELECT * FROM finding ORDER BY severity DESC, id"):
            print(f"[{f['severity']}] {f['title']}\n     {f['detail']}\n     evidence: {f['evidence']}\n")
        return
    if cmd == "interview":
        r = agents.interview(con, argv[2], " ".join(argv[3:]))
        return print(f"{r['reply']}\n  ({r['mode']}) {', '.join(r['cites'])}")
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
