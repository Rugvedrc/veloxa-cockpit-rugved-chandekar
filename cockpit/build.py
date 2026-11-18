"""Build and open one database per release date ("what did we know on date X?").

A database for date D contains only files from drops released on or before D, so later
material cannot leak into earlier answers. Databases are cached in data/ and rebuilt when
the code or curated inputs are newer.
"""
from datetime import date

from . import checks, db, loaders, org, resolve
from .ask import ask, reply

FIRST_RELEASE = "2026-11-16"
# The newest drop whose contents are actually modelled and analysed. Bump this as each day's
# data is added; until then a later "as of" date is answered from this snapshot and says so.
ANALYSED_THROUGH = "2026-11-18"


class NothingReleased(Exception):
    pass


def release_dates():
    return sorted(loaders.DAY_DATES.values())


def effective_day(as_of=None):
    """Map any calendar date to the newest release date we can honestly answer from."""
    d = as_of or max(date.today().isoformat(), FIRST_RELEASE)
    if d < FIRST_RELEASE:
        raise NothingReleased(d)
    cap = min(d, ANALYSED_THROUGH)
    return max(r for r in release_dates() if r <= cap)


def db_path(day):
    return db.ROOT / "data" / f"veloxa_{day}.db"


def build(day, path=None):
    loaders.AS_OF = day
    con = db.rebuild(path or db_path(day))
    loaders.load_all(con)
    resolve.load_entities(con)
    resolve.load_claims(con)
    org.load_org(con)
    checks.run_all(con)
    con.commit()
    return con


def _stale(p):
    code = [*(db.ROOT / "cockpit").glob("*.py"), *(db.ROOT / "data" / "curated").glob("*.json")]
    return p.stat().st_mtime < max(f.stat().st_mtime for f in code)


def get_con(as_of=None, rebuild=False):
    day = effective_day(as_of)
    p = db_path(day)
    if rebuild or not p.exists() or _stale(p):
        build(day, p).close()
    return db.connect(p)


def answer(question, as_of=None):
    """The one entry point for the UI, CLI and tests: question + optional date -> answer dict."""
    try:
        con = get_con(as_of)
    except NothingReleased:
        return reply(f"Nothing had been released by {as_of}; the first drop was {FIRST_RELEASE}.", [], "None")
    try:
        r = ask(con, question)
    finally:
        con.close()
    if as_of and as_of > ANALYSED_THROUGH:
        r["caveats"].append(f"Analysis currently covers drops through {ANALYSED_THROUGH}; later material is not modelled yet.")
    return r


def table(sql, as_of=None, args=()):
    """Run a read-only query against the database for `as_of` and return plain dicts."""
    con = get_con(as_of)
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()
