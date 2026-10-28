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
import tabular

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ledger", "predictions.csv")

def main():
    # pipes are the CSV's escape for a comma inside a claim; tabular restores them
    rows = [r for r in tabular.rows(
        SRC, pipes_as_commas=("claim", "resolution_criteria", "evidence"))
        if r.get("id")]

    today = datetime.date.today()
    for r in rows:
        r["overdue"] = False
        if r["status"] == "open" and r.get("resolve_by"):
            try:
                r["overdue"] = datetime.date.fromisoformat(r["resolve_by"]) < today
            except ValueError:
                pass

    # A call can also be VOIDED — the test turned out to be unresolvable, or the
    # call should never have been logged. Those are shown with the resolved ones
    # and kept out of the accuracy denominator: scoring them either way would be
    # dishonest, but dropping them silently (as happened until 28 Oct 2026, when
    # they matched no bucket and vanished from the page) is worse.
    resolved = [r for r in rows if r["status"] in ("correct", "incorrect", "partial")]
    void = [r for r in rows if r["status"] == "void"]
    correct = [r for r in resolved if r["status"] == "correct"]
    partial = [r for r in resolved if r["status"] == "partial"]
    open_ = [r for r in rows if r["status"] == "open"]
    counted = len(resolved) + len(void) + len(open_)
    if counted != len(rows):
        unknown = sorted({r["status"] for r in rows} - {"correct","incorrect","partial","open","void"})
        print(f"  WARNING: {len(rows)-counted} row(s) have an unrecognised status "
              f"and will not appear on the site: {unknown}")

    score = len(correct) + 0.5 * len(partial)
    accuracy = round(100 * score / len(resolved)) if resolved else None

    out = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stats": {
            "total": len(rows), "open": len(open_), "resolved": len(resolved),
            "correct": len(correct), "partial": len(partial),
            "incorrect": len(resolved) - len(correct) - len(partial),
            "void": len(void),
            "accuracy": accuracy,
        },
        "open": sorted(open_, key=lambda r: r.get("resolve_by") or "9999"),
        "resolved": sorted(resolved + void, key=lambda r: r.get("resolved_date") or "", reverse=True),
    }
    with open(os.path.join(HERE, "ledger.js"), "w", encoding="utf-8") as f:
        f.write("window.LEDGER = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print(f"ledger.js built — {len(rows)} predictions "
          f"({len(open_)} open, {len(resolved)} resolved, {len(void)} void).")

if __name__ == "__main__":
    main()
