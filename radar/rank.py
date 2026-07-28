#!/usr/bin/env python3
"""Rank and dedupe radar observations into an edition candidate feed.

  python3 radar/rank.py --slot midday
  python3 radar/rank.py --since-hours 18 --top 40

The scanner answers "what moved". This answers "what is worth an editor's
attention", which is a different and harder question. Two rules shape it:

  * first_seen_ts, not the page's claimed date, decides the recency window. The
    claimed date is used only to *disqualify* (an item first seen today that
    says it was published in May is a stale trap, and those are the single most
    common way bad items enter a brief).
  * Anything already covered in the last 7 days is demoted, not hidden. The
    editor still needs to see it, because a covered story with a genuinely new
    development is a legitimate lead — it just has to earn it.

Every score is emitted with its component breakdown. A ranking you cannot argue
with is a ranking an editor will quietly stop trusting.
"""
import os, sys, re, json, time, argparse, sqlite3, datetime, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import store

EAT = datetime.timezone(datetime.timedelta(hours=3))

TIER_W = {1: 40, 2: 20, 3: 5}
CAT_W = {
    "advisory": 32, "health": 24, "gazette": 20, "entry-rules": 20, "parks": 18,
    "regulator": 17, "statistics": 16, "fiscal": 15, "central-bank": 12,
    "aviation": 13, "airline": 12, "ministry": 12, "aviation-tracker": 14,
    "hotel-group": 9, "dmo": 8, "capital": 9, "tender": 7, "legislature": 10,
    "weather": 11, "research": 8, "body": 7, "source-market": 9,
    "trade": 5, "press": 4, "aviation-body": 8,
}

# Words that mean an item touches demand, supply, cost, risk or reputation.
RELEVANT = {
    3: ("advisory", "outbreak", "ebola", "marburg", "cholera", "quarantine", "curfew",
        "evacuat", "terror", "kidnap", "grounded", "insolven", "collapse", "suspend",
        "cancel", "state of emergency", "travel ban", "level 4", "level 3"),
    2: ("levy", "tax", "vat", "fee", "tariff", "permit", "visa", "eta", "gazette",
        "occupancy", "adr", "revpar", "arrivals", "bed-night", "fuel", "diesel",
        "electricity", "route", "frequency", "capacity", "seat", "charter", "airport",
        "strike", "flood", "cyclone", "protest", "election", "conservanc", "park fee",
        "gorilla", "concession", "wildlife"),
    1: ("hotel", "lodge", "camp", "resort", "tourism", "tourist", "safari", "beach",
        "airline", "flight", "booking", "conference", "mice", "exhibition", "summit",
        "investment", "opening", "signing", "pipeline", "rooms", "guest", "operator",
        "inflation", "shilling", "franc", "exchange rate", "traffic", "passenger"),
}
SHOCK = ("level 4", "level 3", "do not travel", "reconsider travel", "outbreak",
         "confirmed case", "attack", "explosion", "grounded", "suspends all",
         "airspace closed", "state of emergency", "curfew", "evacuat", "cyclone",
         "insolven", "ceases operations", "strike")

STOP = set("""the a an and or of to in on for with by from at as is are was were be been
this that these those it its their his her our your not no all any new news more most
after before over under between into out up down than then when what which who how why
will would can could should may might must has have had do does did about across
said says say per amid ahead following report reports reported year years month months
week weeks day days today yesterday tomorrow first second third last next""".split())


def toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if len(w) >= 4 and w not in STOP} | \
           {w for w in re.findall(r"\b\d{2,}\b", s or "")}


# ---------------------------------------------------------------- coverage

KEYCAP = re.compile(r"^([0-9]️?⃣)\s*")


def covered_headlines(days=7, today=None):
    """Headlines already published, newest first. Same extraction as
    recent_topics.py so the radar and the coverage check never disagree."""
    today = today or datetime.date.today()
    cutoff = today - datetime.timedelta(days=days)
    out = []
    for path in sorted(glob.glob(os.path.join(REPO, "editions-src", "*.md"))):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
        if not m:
            continue
        try:
            d = datetime.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if d < cutoff:
            continue
        md = open(path, encoding="utf-8").read()
        body = md
        for part in re.split(r"\n##+\s*", "\n" + md):
            if part.strip().split("\n", 1)[0].strip().upper().startswith("TELEGRAM"):
                body = part.split("\n", 1)[1] if "\n" in part else ""
                break
        for line in body.split("\n"):
            line = line.strip()
            if KEYCAP.match(line):
                out.append((d, KEYCAP.sub("", line)))
    return out


def coverage_penalty(title, summary, covered, today):
    """Containment, not Jaccard: a three-word radar headline against a ten-word
    edition headline scores near zero on Jaccard even when it is plainly the same
    story. Containment asks the right question — how much of this candidate is
    already accounted for?"""
    t = toks(title) | toks(summary[:300])
    if not t:
        return 0, None, 0.0
    best, best_h, best_d = 0.0, None, None
    for d, head in covered:
        h = toks(head)
        if not h:
            continue
        score = len(t & h) / min(len(t), max(len(h), 1))
        if score > best:
            best, best_h, best_d = score, head, d
    if best < 0.45:
        return 0, None, best
    pen = -70 if best_d == today else -40
    return pen, best_h, best


# ---------------------------------------------------------------- scoring

def relevance(text):
    t = (text or "").lower()
    score, hits = 0, []
    for weight, words in RELEVANT.items():
        for w in words:
            if w in t:
                score += weight * 4
                hits.append(w)
    return min(score, 60), hits[:8]


def window_for(slot, now=None):
    now = now or datetime.datetime.now(EAT)
    if slot == "morning":
        start = (now - datetime.timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
    elif slot == "midday":
        start = now.replace(hour=7, minute=0, second=0, microsecond=0)
    elif slot == "evening":
        start = now.replace(hour=13, minute=0, second=0, microsecond=0)
    else:
        start = now - datetime.timedelta(hours=18)
    if start > now:
        start -= datetime.timedelta(days=1)
    return int(start.timestamp())


def auto_slot(now=None):
    h = (now or datetime.datetime.now(EAT)).hour
    return "morning" if h < 10 else ("midday" if h < 16 else "evening")


def score_item(row, covered, today, now_ts):
    tier = row["tier"]
    parts = {}
    parts["tier"] = TIER_W.get(tier, 5)
    parts["category"] = CAT_W.get(row["category"], 5)
    parts["lead"] = round(min(row["lead_days"], 14) * 1.2, 1)
    text = f"{row['title']} {row['summary'][:600]}"
    rel, hits = relevance(text)
    parts["relevance"] = rel

    age_h = (now_ts - row["first_seen_ts"]) / 3600.0
    parts["freshness"] = round(max(0, 18 - age_h) * 1.1, 1)

    pub = row["published_ts"]
    if pub:
        age_d = (now_ts - pub) / 86400.0
        # Calibrated against a real miss: on 28 July a search engine surfaced a
        # WTTC release as same-day news; the page itself was dated 15 June, 43
        # days earlier. A 45-day threshold would have waved it through. An
        # edition window is measured in hours, so anything over three weeks old
        # cannot be the hook, however recently we first saw it.
        if age_d > 21:
            parts["stale_trap"] = -60
        elif age_d > 7:
            parts["stale_trap"] = -25
        elif age_d > 3:
            parts["stale_trap"] = -10
        elif age_d <= 2:
            parts["corroborated"] = 10          # source states a date and it agrees
    else:
        parts["undated"] = -6                   # publishable only if a date can be found

    shock = [w for w in SHOCK if w in text.lower()]
    if shock:
        parts["shock"] = 18

    pen, match, sim = coverage_penalty(row["title"], row["summary"], covered, today)
    if pen:
        parts["already_covered"] = pen

    if row["kind"] == "page-change":
        parts["page_change"] = -4               # real, but needs a human to read it

    total = round(sum(parts.values()), 1)
    return total, parts, hits, shock, match, round(sim, 2)


# ---------------------------------------------------------------- main

def build(db, slot, since_ts, top, days):
    now_ts = int(time.time())
    today = datetime.date.today()
    covered = covered_headlines(days, today)
    rows = db.execute("""
        SELECT i.*, s.name AS source_name, s.tier, s.country, s.category,
               s.lead_days, s.segments, s.slots, s.url AS source_url
        FROM items i JOIN sources s ON s.id = i.source_id
        WHERE i.first_seen_ts >= ? AND s.enabled = 1
        ORDER BY i.first_seen_ts DESC""", (since_ts,)).fetchall()

    cands = []
    for r in rows:
        total, parts, hits, shock, match, sim = score_item(r, covered, today, now_ts)
        cands.append({
            "score": total, "components": parts, "keywords": hits, "shock_terms": shock,
            "dedupe_match": match, "dedupe_similarity": sim,
            "id": r["key"][:12], "title": r["title"], "url": r["url"],
            "summary": r["summary"][:400], "kind": r["kind"],
            "source": r["source_name"], "source_id": r["source_id"],
            "tier": r["tier"], "country": r["country"], "category": r["category"],
            "segments": json.loads(r["segments"]),
            "first_seen": datetime.datetime.fromtimestamp(r["first_seen_ts"], EAT).isoformat(timespec="minutes"),
            "published": (datetime.datetime.fromtimestamp(r["published_ts"], EAT).date().isoformat()
                          if r["published_ts"] else None),
            "verdict": None,
        })
    for c in cands:
        if c["components"].get("already_covered", 0) <= -70:
            c["verdict"] = "DROP — covered today"
        elif c["components"].get("already_covered", 0) < 0:
            c["verdict"] = "DEMOTE — covered in last 7d; needs a new development"
        elif c["components"].get("stale_trap", 0) <= -60:
            c["verdict"] = "DROP — stale trap: source date far outside window"
        elif c["components"].get("stale_trap", 0) < 0:
            c["verdict"] = "CHECK — source date older than the window"
        elif c["shock_terms"] and c["tier"] == 1:
            c["verdict"] = "LEAD CANDIDATE — tier-1 shock language"
        elif c["tier"] == 1 and c["score"] >= 90:
            c["verdict"] = "STRONG — tier-1, upstream"
        elif c["score"] >= 70:
            c["verdict"] = "CONSIDER"
        else:
            c["verdict"] = "weak"
    cands.sort(key=lambda c: -c["score"])
    return cands[:top], len(rows), covered


def to_markdown(cands, slot, since_ts, total_seen, n_covered):
    since = datetime.datetime.fromtimestamp(since_ts, EAT)
    L = [f"# Radar candidates — {slot} slot",
         f"_Window opens {since.strftime('%a %d %b %H:%M')} EAT · "
         f"{total_seen} observations in window · {n_covered} headlines deduped against_",
         "",
         "Ranked by first-seen recency, source tier and hospitality relevance. "
         "`first seen` is when the radar observed the item, which is the date the recency "
         "gate runs on. `published` is what the source claims — where the two disagree, "
         "the disagreement is the story.",
         ""]
    if not cands:
        L += ["**Nothing in window.** Under the skip rule that is a finding, not a failure — "
              "report it and do not stretch the window.", ""]
    live = [c for c in cands if not c["verdict"].startswith(("DROP", "weak"))]
    dropped = [c for c in cands if c["verdict"].startswith("DROP")]
    for c in live:
        flag = "🔴" if "LEAD" in c["verdict"] else ("🟠" if "STRONG" in c["verdict"] else "🟡")
        L.append(f"### {flag} [{c['score']}] {c['title'][:120]}")
        L.append(f"- **Verdict:** {c['verdict']}")
        L.append(f"- **Source:** {c['source']} · tier {c['tier']} · {c['country']} · {c['category']}")
        L.append(f"- **First seen:** {c['first_seen']} EAT · **Source date:** {c['published'] or '— none stated'}")
        L.append(f"- **URL:** {c['url']}")
        if c["shock_terms"]:
            L.append(f"- **Shock language:** {', '.join(c['shock_terms'][:5])}")
        if c["dedupe_match"]:
            L.append(f"- **Overlaps prior coverage ({c['dedupe_similarity']}):** {c['dedupe_match'][:90]}")
        if c["summary"]:
            L.append(f"- **Extract:** {c['summary'][:260]}")
        L.append(f"- **Score parts:** " + ", ".join(f"{k} {v:+g}" for k, v in c["components"].items()))
        L.append("")
    if dropped:
        L += ["---", "", "## Dropped (shown so the reasoning is auditable)", ""]
        for c in dropped:
            L.append(f"- [{c['score']}] {c['title'][:90]} — _{c['verdict']}_ ({c['source']})")
        L.append("")
    return "\n".join(L)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.path.join(HERE, "radar.db"))
    p.add_argument("--slot", choices=["morning", "midday", "evening"])
    p.add_argument("--since-hours", type=float)
    p.add_argument("--top", type=int, default=40)
    p.add_argument("--dedupe-days", type=int, default=7)
    p.add_argument("--out-dir", default=os.path.join(HERE, "out"))
    a = p.parse_args()

    slot = a.slot or auto_slot()
    since = (int(time.time() - a.since_hours * 3600) if a.since_hours else window_for(slot))
    db = store.connect(a.db)
    cands, total, covered = build(db, slot, since, a.top, a.dedupe_days)

    os.makedirs(a.out_dir, exist_ok=True)
    payload = {"generated": datetime.datetime.now(EAT).isoformat(timespec="seconds"),
               "slot": slot, "window_start": since, "observations_in_window": total,
               "deduped_against": len(covered), "candidates": cands}
    with open(os.path.join(a.out_dir, "candidates.json"), "w") as f:
        json.dump(payload, f, indent=1)
    md = to_markdown(cands, slot, since, total, len(covered))
    with open(os.path.join(a.out_dir, "candidates.md"), "w") as f:
        f.write(md)
    live = [c for c in cands if not c["verdict"].startswith(("DROP", "weak"))]
    print(f"slot={slot} window_start={datetime.datetime.fromtimestamp(since, EAT):%d %b %H:%M} "
          f"observations={total} candidates={len(cands)} publishable-looking={len(live)}")
    for c in live[:12]:
        print(f"  [{c['score']:>6}] {c['verdict'][:34]:34} {c['title'][:60]}")
    if len(live) < 2:
        print("\n  ⚠ Fewer than 2 live candidates — the skip rule is in play.")


if __name__ == "__main__":
    main()
