#!/usr/bin/env python3
"""
EA Pulse Foresight Ledger.
Reads ledger/predictions.csv -> writes ledger.js (window.LEDGER).

Every forecast the Pulse makes is logged with a falsifiable resolution
criterion and a resolve-by date. When evidence lands, status becomes
correct / incorrect / partial with the evidence recorded.

Accuracy is computed on RESOLVED predictions only, and misses are shown
publicly — a track record that only shows hits is marketing, not a record.
Run: python3 build_ledger.py
"""
import os, csv, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ledger", "predictions.csv")

def main():
    rows = []
    with open(SRC, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("id"):
                continue
            # pipes are used in the CSV to escape commas inside claims
            for k in ("claim", "resolution_criteria", "evidence"):
                if r.get(k):
                    r[k] = r[k].replace("|", ",")
            rows.append(r)

    today = datetime.date.today()
    for r in rows:
        r["overdue"] = False
        if r["status"] == "open" and r.get("resolve_by"):
            try:
                r["overdue"] = datetime.date.fromisoformat(r["resolve_by"]) < today
            except ValueError:
                pass

    resolved = [r for r in rows if r["status"] in ("correct", "incorrect", "partial")]
    correct = [r for r in resolved if r["status"] == "correct"]
    partial = [r for r in resolved if r["status"] == "partial"]
    open_ = [r for r in rows if r["status"] == "open"]

    score = len(correct) + 0.5 * len(partial)
    accuracy = round(100 * score / len(resolved)) if resolved else None

    out = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stats": {
            "total": len(rows), "open": len(open_), "resolved": len(resolved),
            "correct": len(correct), "partial": len(partial),
            "incorrect": len(resolved) - len(correct) - len(partial),
            "accuracy": accuracy,
        },
        "open": sorted(open_, key=lambda r: r.get("resolve_by") or "9999"),
        "resolved": sorted(resolved, key=lambda r: r.get("resolved_date") or "", reverse=True),
    }
    with open(os.path.join(HERE, "ledger.js"), "w", encoding="utf-8") as f:
        f.write("window.LEDGER = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print(f"ledger.js built — {len(rows)} predictions ({len(open_)} open, {len(resolved)} resolved).")

if __name__ == "__main__":
    main()
