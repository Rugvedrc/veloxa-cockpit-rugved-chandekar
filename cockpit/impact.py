"""Continuity exposure: what the work records say would be at stake if a person left.

This measures DEPENDENCY (who holds the work), never likelihood (who might leave): nothing in the data
supports predicting departures, and a ranking by "likely to quit" would be guesswork about real people.
Everything here is computed from Jira, git and the on-call rota, so it exists only once those are released.
"""
from datetime import date

EXPORT = date(2026, 10, 31)       # the engineering exports are as of 31 Oct (data_room/README.txt)
RECENT_FROM = "2026-08-02"        # 90 days before the export
PACE_FROM = "2026-07-01"          # same window as the Atlas pace finding


def _share(a, b):
    return a / b if b else 0.0


def exit_impact(con, emp):
    """Metrics for one person, or None if there is no engineering data (before Day 3)."""
    issues = con.execute("SELECT * FROM jira_issue").fetchall()
    if not issues:
        return None
    mine = [i for i in issues if i["emp_id"] == emp]
    open_all = sum(i["points"] for i in issues if i["status"] != "Done")
    open_me = sum(i["points"] for i in mine if i["status"] != "Done")
    done_recent = sum(i["points"] for i in issues if i["status"] == "Done" and i["resolved"] >= PACE_FROM)
    done_me = sum(i["points"] for i in mine if i["status"] == "Done" and i["resolved"] >= PACE_FROM)
    epics = []
    for e in con.execute("SELECT * FROM jira_epic ORDER BY key"):
        pts = sum(i["points"] for i in mine if i["epic_key"] == e["key"] and i["status"] != "Done")
        if pts:
            epics.append({"key": e["key"], "name": e["name"], "open_points": pts})
    eng = con.execute("SELECT emp_id, COUNT(*) c FROM git_commit WHERE repo='atlas-engine' GROUP BY emp_id ORDER BY c DESC").fetchall()
    eng_all = sum(r["c"] for r in eng)
    eng_me = next((r["c"] for r in eng if r["emp_id"] == emp), 0)
    rec = con.execute("SELECT emp_id, COUNT(*) c FROM git_commit WHERE repo='atlas-engine' AND substr(committed_ist,1,10) >= ? GROUP BY emp_id",
                      (RECENT_FROM,)).fetchall()
    rec_all = sum(r["c"] for r in rec)
    rec_me = next((r["c"] for r in rec if r["emp_id"] == emp), 0)
    names = {r["emp_id"]: r["full_name"] for r in con.execute("SELECT emp_id, full_name FROM person")}
    others = [(names.get(r["emp_id"], r["emp_id"]), r["c"]) for r in eng if r["emp_id"] != emp]
    weeks = con.execute("SELECT COUNT(*) FROM oncall").fetchone()[0]
    on = con.execute("SELECT COUNT(*) FROM oncall WHERE primary_id=? OR secondary_id=?", (emp, emp)).fetchone()[0]
    weeks_span = (EXPORT - date.fromisoformat(PACE_FROM)).days / 7
    return {
        "emp_id": emp, "name": names.get(emp, emp), "tickets": len(mine), "points": sum(i["points"] for i in mine),
        "open_points": open_me, "open_total": open_all, "open_share": _share(open_me, open_all), "epics": epics,
        "done_recent": done_me, "done_recent_all": done_recent, "done_share": _share(done_me, done_recent),
        "pace_all": _share(done_recent, weeks_span), "pace_others": _share(done_recent - done_me, weeks_span),
        "engine_commits": eng_me, "engine_total": eng_all, "engine_share": _share(eng_me, eng_all),
        "engine_recent_share": _share(rec_me, rec_all), "other_engine_committers": others,
        "oncall_weeks": on, "rota_weeks": weeks,
        "kit_assets": [r["asset"] for r in con.execute("SELECT asset FROM launch_kit WHERE owner_id=?", (emp,))],
    }


def dependency_ranking(con):
    """Everyone who owns Atlas work, ordered by how much of the open work they hold. Not a likelihood ranking."""
    ids = [r[0] for r in con.execute("SELECT DISTINCT emp_id FROM jira_issue WHERE emp_id IS NOT NULL")]
    rows = [exit_impact(con, i) for i in ids]
    return sorted([r for r in rows if r], key=lambda r: (-r["open_points"], -r["engine_share"], r["name"]))
