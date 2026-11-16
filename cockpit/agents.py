"""The 14 people as interviewable agents.

Work facts come from the database at call time (so they stay true after each data drop);
private life and voice come from data/curated/personas.json and are all logged as assumptions.
With ANTHROPIC_API_KEY set the persona is played by an LLM; without it a grounded offline
mode answers from the same facts, so the demo never depends on a network.
Pay is never put into an agent's context, so no agent can leak it.
"""
import json
import os
import re
import urllib.request

from .db import ROOT

PERSONAS = json.loads((ROOT / "data" / "curated" / "personas.json").read_text(encoding="utf8"))
PERSONAS.pop("_note", None)
MEMORY_DIR = ROOT / "data" / "memory"
MODEL = os.environ.get("VELOXA_MODEL", "claude-sonnet-5-5")


def roster(con):
    rows = con.execute("SELECT * FROM person WHERE emp_id IN (%s) ORDER BY dept, join_date" %
                       ",".join("?" * len(PERSONAS)), list(PERSONAS)).fetchall()
    return [dict(r) for r in rows]


def grounded_facts(con, emp):
    """Everything the data room says about this person, as plain sentences with sources."""
    p = con.execute("SELECT * FROM person WHERE emp_id=?", (emp,)).fetchone()
    facts = []
    mgr = con.execute("SELECT full_name FROM person WHERE emp_id=?", (p["manager_id"],)).fetchone()
    facts.append((f"{p['full_name']} is {p['title']} in {p['dept']} ({p['location']}), joined {p['join_date']}"
                  + (f", reports to {mgr['full_name']}" if mgr else "") + f". Status: {p['status']}"
                  + (f", last day {p['exit_date']}" if p["exit_date"] else "") + ".", p["src_ref"]))
    reports = [r["full_name"] for r in con.execute("SELECT full_name FROM person WHERE manager_id=?", (emp,))]
    if reports:
        facts.append((f"Direct reports: {', '.join(reports)}.", "Employee_Master.xlsx"))
    for m in con.execute("SELECT * FROM message WHERE sender LIKE ? OR recipient LIKE ? ORDER BY sent_at",
                         (f"%{p['email']}%", f"%{p['email']}%")):
        body = re.sub(r"\s+", " ", m["body"])[:300]
        if p["email"] in m["sender"]:
            facts.append((f"On {m['sent_at'][:10]} I emailed {m['recipient'].split('<')[0].strip()} "
                          f"('{m['subject']}'): {body}", m["src_ref"]))
        else:
            facts.append((f"On {m['sent_at'][:10]} {m['sender'].split('<')[0].strip()} emailed me "
                          f"('{m['subject']}'): {body}", m["src_ref"]))
    for c in con.execute("SELECT * FROM claim WHERE resolved LIKE ? OR as_heard LIKE ?",
                         (f"%{p['full_name']}%", f"%{p['full_name'].split()[0]}%")):
        facts.append((f"Mentioned on a leadership call ({c['doc_id']}): '{c['as_heard']}'.", f"claim {c['id']}"))
    for f in con.execute("SELECT * FROM finding WHERE evidence LIKE ? OR title LIKE ?",
                         (f"%{p['full_name']}%", f"%{p['full_name']}%")):
        facts.append((f"Issue on file: {f['title']}. {f['detail']}", f["id"]))
    ini = "".join(w[0] for w in p["full_name"].split()[:2]).upper()
    n = con.execute("SELECT COUNT(*) FROM gl_entry WHERE entered_by=?", (ini,)).fetchone()[0]
    if n and p["dept"] == "Finance":
        facts.append((f"Entered {n} GL lines (initials {ini}).", "GL_Export_Apr-Sep_2026.xlsx"))
    return facts


def company_facts(con):
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on DESC LIMIT 1").fetchone()
    return (f"Company: Veloxa, B2B SaaS, Bengaluru, {b['team']} people. Latest board update ({b['period']}): "
            f"ARR Rs {b['arr_cr']} Cr, {b['customers']} customers, burn Rs {b['burn_lakh']:.0f} L/month, "
            f"runway {b['runway_months']} months. Atlas (routing engine v3) GA has slipped from 15 Sep.")


def system_prompt(con, emp):
    pers = PERSONAS[emp]
    facts = "\n".join(f"- {t} [{s}]" for t, s in grounded_facts(con, emp))
    return f"""You are role-playing a real colleague at Veloxa for the CEO's test environment. Stay in character.

VOICE: {pers['voice']}
PRIVATE LIFE (invented, may reveal naturally): {pers['life']}
WANTS: {pers['wants']}
WORRIES: {pers['worries']}
TELL: {pers['tells']}

{company_facts(con)}

WHAT THE RECORDS SAY ABOUT YOU (true; do not contradict):
{facts}

RULES: Speak in first person, 2-5 sentences. Only state work facts that appear above or in the company line;
if you do not know, say so in character. Never reveal anyone's salary or pay, including your own: say it is
confidential. Do not invent figures, dates or events. Private life details may be shared if natural."""


def _memory_path(emp):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{emp}.jsonl"


def load_memory(emp):
    p = _memory_path(emp)
    return [json.loads(l) for l in p.read_text(encoding="utf8").splitlines()] if p.exists() else []


def _remember(emp, q, a):
    with _memory_path(emp).open("a", encoding="utf8") as f:
        f.write(json.dumps({"role": "user", "content": q}) + "\n")
        f.write(json.dumps({"role": "assistant", "content": a}) + "\n")


def _llm(system, history, question, key):
    body = json.dumps({"model": MODEL, "max_tokens": 400, "system": system,
                       "messages": history[-10:] + [{"role": "user", "content": question}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["content"][0]["text"]


PAY = re.compile(r"salary|\bpay\b|\bpaid\b|ctc|earn|compensation|how much do you make", re.I)


def _offline(con, emp, question):
    pers, facts = PERSONAS[emp], grounded_facts(con, emp)
    if PAY.search(question):
        return "That's confidential - pay isn't something I'll discuss, and it's not in what I've been given.", []
    words = {w for w in re.findall(r"[a-z]{4,}", question.lower())}
    scored = sorted(facts[1:], key=lambda f: -len(words & set(re.findall(r"[a-z]{4,}", f[0].lower()))))
    hit = [f for f in scored if words & set(re.findall(r"[a-z]{4,}", f[0].lower()))][:2]
    if re.search(r"weekend|family|life|hobby|outside|home|live", question.lower()):
        return pers["life"], []
    if re.search(r"worr|concern|afraid|stress|keep you", question.lower()):
        return pers["worries"], []
    if hit:
        return " ".join(h[0] for h in hit), [h[1] for h in hit]
    return f"I'd rather not guess on that. What I can tell you: {pers['wants']}", []


def interview(con, emp, question, use_memory=True):
    if emp not in PERSONAS:
        raise KeyError(f"{emp} is not one of the 14 agents")
    key = os.environ.get("ANTHROPIC_API_KEY")
    hist = load_memory(emp) if use_memory else []
    if key:
        try:
            text, cites, mode = _llm(system_prompt(con, emp), hist, question, key), [], "llm"
        except Exception as e:  # network/API failure must not break the demo
            text, cites = _offline(con, emp, question)
            mode = f"offline (LLM call failed: {type(e).__name__})"
    else:
        text, cites = _offline(con, emp, question)
        mode = "offline (set ANTHROPIC_API_KEY for full persona mode)"
    if use_memory:
        _remember(emp, question, text)
    return {"emp_id": emp, "reply": text, "mode": mode, "cites": cites}
