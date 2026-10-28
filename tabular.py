#!/usr/bin/env python3
"""Delimiter-tolerant reader for the repo's small CSV datasets.

Why this exists
---------------
Two data files silently changed delimiter under the scripts that read them:

* ledger/predictions.csv flipped from comma to tab on 6 Oct 2026. Every reader
  used csv.DictReader's default comma, so each row came back as one unnamed
  field, r.get("id") was None, and the row was skipped. ledger.js went to zero
  predictions and the public Foresight record was empty from 6 to 28 Oct.
* rates/observations.csv is TAB for hand-collected rows but the automated OTA
  fetcher appends with csv.writer's default comma, so the file is genuinely
  mixed: 806 tab rows and 74 comma rows at the time of writing.

A reader that assumes one delimiter loses data silently, which is the worst
failure mode a dataset can have: the build still succeeds and the page still
renders, just empty. So detect the delimiter from the header, and fall back
per record for a file that mixes both.

Quoted fields spanning several lines (rate-season tables pasted into `note`)
are handled, because parsing streams through csv rather than splitting lines.
"""
import csv

ALT = {",": "\t", "\t": ","}


def sniff(path, encoding="utf-8"):
    """Delimiter of the header row — tab if present, else comma."""
    with open(path, encoding=encoding, newline="") as fh:
        head = fh.readline()
    return "\t" if "\t" in head else ","


def records(path, encoding="utf-8"):
    """Yield each record as a list of cells, whichever delimiter wrote it."""
    delim = sniff(path, encoding)
    alt = ALT[delim]
    with open(path, encoding=encoding, newline="") as fh:
        for row in csv.reader(fh, delimiter=delim):
            # A record written with the other delimiter arrives as one cell.
            # Re-parse it rather than drop it.
            if len(row) == 1 and alt in row[0]:
                row = next(csv.reader([row[0]], delimiter=alt), row)
            yield row


def rows(path, encoding="utf-8", pipes_as_commas=()):
    """Rows as dicts keyed by the header.

    pipes_as_commas: field names where "|" is the escape the ledger uses for a
    comma inside a value. Restored here so callers never see the escape.
    """
    it = records(path, encoding)
    try:
        header = [h.strip() for h in next(it)]
    except StopIteration:
        return []
    out = []
    for cells in it:
        if not cells or not any(c.strip() for c in cells):
            continue
        r = {header[i]: (cells[i] if i < len(cells) else "") for i in range(len(header))}
        for k in pipes_as_commas:
            if r.get(k):
                r[k] = r[k].replace("|", ",")
        out.append(r)
    return out


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        rs = rows(p)
        print(f"{p}: delimiter={sniff(p)!r} rows={len(rs)} fields={len(rs[0]) if rs else 0}")
