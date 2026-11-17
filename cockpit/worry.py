"""The 'what should I worry about' home screen: the top three themes, with the rule that ranked them.

The CEO's voice note T6a asked for 'the top three'. Three raw findings would mix a payroll slip
with a missed launch, so findings are grouped into themes (checks.py assigns each one) and the
three themes are ranked. Everything else stays one click away.

Ranking rule (shown to the user, DECISIONS D-15):
  1. highest severity in the theme (3 = act now, 2 = look soon, 1 = FYI)
  2. tie -> the theme the CEO named as her main concern on the kickoff call (engineering speed, Atlas)
  3. tie -> more findings at severity 2 or above
"""
import re

CEO_MAIN_CONCERN = "delivery"  # T1: "Main concern is engineering speed; the routing engine ... not sure it will make it"

THEMES = {
    "delivery": ("Atlas delivery is at risk", "VP Engineering"),
    "money": ("Money, books and numbers", "CFO"),
    "people": ("People: leavers, hiring and morale", "Head of People%"),
}
SEV = {3: "Act now", 2: "Look soon", 1: "FYI"}

RULE = ("Ranked by the highest severity in each theme; ties go to the CEO's stated main concern "
        "(engineering speed / Atlas), then to the theme with more findings at 'look soon' or above. "
        "Severity is my judgement, not the data's.")


def _owner(con, title_like):
    r = con.execute("SELECT full_name, title FROM person WHERE title LIKE ? AND status='Active' LIMIT 1", (title_like,)).fetchone()
    return f"{r['full_name']} ({r['title']})" if r else None


def top_three(con, n=3):
    rows = [dict(r) for r in con.execute("SELECT * FROM finding ORDER BY severity DESC, id")]
    by = {}
    for f in rows:
        by.setdefault(f["theme"], []).append(f)

    def key(theme):
        fs = by[theme]
        return (-max(f["severity"] for f in fs), 0 if theme == CEO_MAIN_CONCERN else 1,
                -sum(1 for f in fs if f["severity"] >= 2))

    ranked = sorted(by, key=key)[:n]
    out = []
    for i, theme in enumerate(ranked, 1):
        fs = by[theme]
        head = fs[0]  # rows are already ordered by severity, then id
        more = [f for f in fs[1:] if f["severity"] >= 2][:3]
        fyi = sum(1 for f in fs[1:] if f["severity"] < 2)
        ev = []
        for f in [head, *more]:
            for e in re.split(r";\s*", f["evidence"]):
                if e and e not in ev:
                    ev.append(e)
        label, owner_title = THEMES.get(theme, (theme.title(), None))
        out.append({
            "rank": i, "theme": theme, "label": label, "headline": head["title"], "detail": head["detail"],
            "severity": head["severity"], "severity_label": SEV[head["severity"]],
            "also": [{"id": f["id"], "title": f["title"], "severity": f["severity"]} for f in more],
            "fyi_count": fyi, "evidence": ev[:8],
            "suggested_owner": _owner(con, owner_title) if owner_title else None,
            "finding_ids": [f["id"] for f in fs],
        })
    return {"rule": RULE, "themes": out, "total_findings": len(rows)}
