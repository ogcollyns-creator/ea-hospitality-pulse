#!/usr/bin/env python3
"""
What have we already covered?

Reads editions-src/*.md and prints every story headline published in the last N days,
newest first, flagging TODAY's separately. The Telegram channel preview is cached and
unreliable for this, so the repo is the source of truth.

Run before drafting any edition:
    python3 recent_topics.py          # last 7 days
    python3 recent_topics.py 3        # last 3 days
"""
import os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "editions-src")
KEYCAP = re.compile(r"^([0-9]️?⃣)\s*")

def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=days)

    editions = []
    for fn in os.listdir(SRC):
        if not fn.lower().endswith(".md"):
            continue
        m = re.search(r"(\d{4}-\d{2}-\d{2})", fn)
        if not m:
            continue
        try:
            d = datetime.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if d < cutoff:
            continue
        md = open(os.path.join(SRC, fn), encoding="utf-8").read()
        # take the TELEGRAM section
        body = md
        for part in re.split(r"\n##+\s*", "\n" + md):
            if part.strip().split("\n", 1)[0].strip().upper().startswith("TELEGRAM"):
                body = part.split("\n", 1)[1] if "\n" in part else ""
                break
        heads = [KEYCAP.sub("", l.strip()) for l in body.split("\n") if KEYCAP.match(l.strip())]
        editions.append((d, fn, heads))

    editions.sort(key=lambda x: (x[0], x[1]), reverse=True)

    todays = [e for e in editions if e[0] == today]
    older = [e for e in editions if e[0] != today]

    print("=" * 66)
    print(f"ALREADY COVERED TODAY ({today}) — DO NOT REPEAT without a new development")
    print("=" * 66)
    if not todays:
        print("(nothing published yet today)")
    for d, fn, heads in todays:
        print(f"\n[{fn}]")
        for h in heads:
            print(f"  • {h}")

    print("\n" + "=" * 66)
    print(f"COVERED IN THE PREVIOUS {days} DAYS — treat as stale unless genuinely advanced")
    print("=" * 66)
    for d, fn, heads in older:
        print(f"\n[{d} · {fn}]")
        for h in heads:
            print(f"  • {h}")

    total = sum(len(h) for _, _, h in editions)
    print(f"\n{len(editions)} editions, {total} stories in window.")

if __name__ == "__main__":
    main()
