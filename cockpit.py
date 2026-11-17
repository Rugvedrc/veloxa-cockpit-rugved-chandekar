"""Veloxa cockpit command line.

  python cockpit.py build [--data PATH] [--as-of 2026-11-16]   build the database(s) from the data room
  python cockpit.py ask "how many people?" [--as-of 2026-11-16]
  python cockpit.py top3 [--as-of DATE]                         the three things to worry about
  python cockpit.py worry [--as-of DATE]                        all findings
  python cockpit.py interview VX007 "what keeps you up?"
  python cockpit.py serve                                       web UI at http://127.0.0.1:8765
  python cockpit.py test                                        run the automated test set

PATH is the Veloxa_Hackathon_Release_Packs folder or the .zip. It is remembered after the first run.
"""
import sys
from pathlib import Path

from cockpit import agents, build as builder, db


def opt(argv, name):
    """Remove `--name value` from argv and return the value (or None)."""
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return None


def show(r):
    print(r["answer"])
    for d in r.get("disagreement", []):
        print("  SOURCES DISAGREE:", d)
    for c in r["cites"]:
        print("  source:", c)
    for c in r["caveats"]:
        print("  caveat:", c)
    print("  confidence:", r["confidence"])


def build_all(as_of=None):
    days = [builder.effective_day(as_of)] if as_of else sorted({builder.effective_day(d) for d in builder.release_dates()})
    for day in days:
        con = builder.build(day)
        print(f"built {builder.db_path(day).name}")
        for t in ("source", "person", "payroll", "gl_entry", "board_update", "message", "document", "claim", "finding"):
            print(f"  {t:13} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>4} rows")
        con.close()


def main(argv):
    data = opt(argv, "--data")
    as_of = opt(argv, "--as-of")
    if data:
        db.set_data_dir(data)
    cmd = argv[1] if len(argv) > 1 else "help"
    try:
        if cmd == "build":
            print(f"data room: {db.data_dir()}")
            return build_all(as_of)
        if cmd == "serve":
            from cockpit.server import serve
            return serve()
        if cmd == "test":
            import unittest
            suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent / "tests"))
            return sys.exit(0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1)
        if cmd == "ask":
            return show(builder.answer(" ".join(argv[2:]), as_of))
        if cmd == "top3":
            from cockpit import worry
            con = builder.get_con(as_of)
            t = worry.top_three(con)
            for x in t["themes"]:
                print(f"{x['rank']}. {x['label']} [{x['severity_label']}]  owner: {x['suggested_owner']}\n   {x['headline']}")
                for a in x["also"]:
                    print(f"   also: {a['title']}")
            return print("\n" + t["rule"])
        if cmd == "worry":
            for f in builder.table("SELECT * FROM finding ORDER BY severity DESC, id", as_of):
                print(f"[{f['severity']}] {f['title']}\n     {f['detail']}\n     evidence: {f['evidence']}\n")
            return
        if cmd == "interview":
            con = builder.get_con(as_of)
            r = agents.interview(con, argv[2], " ".join(argv[3:]))
            return print(f"{r['reply']}\n  ({r['mode']}) {', '.join(r['cites'])}")
    except FileNotFoundError as e:
        sys.exit(str(e))
    except builder.NothingReleased:
        sys.exit(f"Nothing had been released by {as_of}; the first drop was {builder.FIRST_RELEASE}.")
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
