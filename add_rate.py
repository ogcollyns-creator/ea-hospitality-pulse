#!/usr/bin/env python3
"""
Fast rate entry for the EA Pulse Rate Index.

  python3 add_rate.py nairobi "Sarova Stanley" 206 --basis BB --type international \
      --source "sarovahotels.com published rate, 2 Aug 2026"

BASIS IS MANDATORY. The basket mixes room-only, B&B, half board, full board and
fully-inclusive rates, and a rate without its basis is not usable: the index needs to
know that a property has not silently changed what the price includes.

  --basis   RO  room only
            BB  bed & breakfast
            HB  half board
            FB  full board
            FB+ full board plus (meals + some activities)
            AI  all inclusive
            FI  fully inclusive (meals, drinks and activities — typical safari basis)
  --channel direct (default) | ota
            'direct' = the property's own published rate. 'ota' = the rate displayed on
            Google Hotels metasearch. The two chain as SEPARATE series and their
            difference is the commission-leakage spread.
  --type    international (default) | resident | trade
            'resident' = East African resident rate. These sit materially below rack
            and are tracked separately; never mix them into an international level.

Appends to rates/observations.csv using today's date, then rebuild with build_rate_index.py.
"""
import sys, os, csv, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, "rates")
BASES = {"RO", "BB", "HB", "FB", "FB+", "AI", "FI", "UNK"}
CHANNELS = {"direct", "ota"}
TYPES = {"international", "resident", "trade"}
HEADER = ["observed_date", "market", "property", "rate_usd", "stay_date",
          "los", "source", "note", "basis", "rate_type", "channel"]


def flag(a, name, default=""):
    for i, t in enumerate(a):
        if t == name and i + 1 < len(a):
            return a[i + 1]
    return default


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        sys.exit(1)
    market, prop, rate = a[0].lower(), a[1], a[2]

    try:
        float(rate)
    except ValueError:
        print(f"Rate must be a number, got '{rate}'")
        sys.exit(1)

    basis = flag(a, "--basis").upper()
    rtype = (flag(a, "--type") or "international").lower()
    channel = (flag(a, "--channel") or "direct").lower()
    stay = flag(a, "--stay")
    source = flag(a, "--source")
    note = flag(a, "--note")

    if basis not in BASES:
        print(f"--basis is required and must be one of: {', '.join(sorted(BASES))}")
        print("A rate without its meal basis cannot go into the index. See --help text above.")
        sys.exit(1)
    if rtype not in TYPES:
        print(f"--type must be one of: {', '.join(sorted(TYPES))}")
        sys.exit(1)
    if channel not in CHANNELS:
        print(f"--channel must be one of: {', '.join(sorted(CHANNELS))}")
        sys.exit(1)
    if basis == "UNK" and channel != "ota":
        print("basis UNK is only permitted on --channel ota (OTA rates display no meal basis).")
        print("A direct rate must state what it includes.")
        sys.exit(1)
    if not source:
        print("--source is required: name where you saw the rate, with a date.")
        sys.exit(1)

    basket = json.load(open(os.path.join(RD, "basket.json"), encoding="utf-8"))
    if market not in basket["markets"]:
        print("Unknown market. Options:", ", ".join(basket["markets"]))
        sys.exit(1)
    known = basket["markets"][market]["properties"]
    if prop not in known:
        print(f"Warning: '{prop}' is not in the {market} basket. Known properties:")
        for p in known:
            print("  -", p)
        print("The basket is fixed by design — add off-basket names only deliberately.")

    conv = basket["convention"]
    if not stay:
        stay = (datetime.date.today() + datetime.timedelta(days=conv["lead_days"])).isoformat()

    path = os.path.join(RD, "observations.csv")
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(HEADER)
        w.writerow([datetime.date.today().isoformat(), market, prop, rate, stay,
                    conv["los"], source, note, basis, rtype, channel])
    print(f"Recorded: {market} | {prop} | US${rate} | {basis} | {rtype} | {channel} | stay {stay}")


if __name__ == "__main__":
    main()
