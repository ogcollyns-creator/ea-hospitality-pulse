#!/usr/bin/env python3
"""
Fast weekly rate entry.
  python3 add_rate.py nairobi "Sarova Stanley" 145
  python3 add_rate.py zanzibar "Zuri Zanzibar" 480 --stay 2026-09-15 --source booking
Appends to rates/observations.csv using today's date, then rebuild with build_rate_index.py.
"""
import sys, os, csv, json, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); RD=os.path.join(HERE,"rates")

def main():
    a=sys.argv[1:]
    if len(a)<3:
        print(__doc__); sys.exit(1)
    market, prop, rate = a[0].lower(), a[1], a[2]
    stay=source=note=""
    for i,t in enumerate(a):
        if t=="--stay" and i+1<len(a): stay=a[i+1]
        if t=="--source" and i+1<len(a): source=a[i+1]
        if t=="--note" and i+1<len(a): note=a[i+1]
    basket=json.load(open(os.path.join(RD,"basket.json"),encoding="utf-8"))
    if market not in basket["markets"]:
        print("Unknown market. Options:", ", ".join(basket["markets"])); sys.exit(1)
    known=basket["markets"][market]["properties"]
    if prop not in known:
        print(f"Warning: '{prop}' not in the {market} basket. Known:"); [print("  -",p) for p in known]
    conv=basket["convention"]
    if not stay:
        stay=(datetime.date.today()+datetime.timedelta(days=conv["lead_days"])).isoformat()
    with open(os.path.join(RD,"observations.csv"),"a",newline="",encoding="utf-8") as f:
        csv.writer(f).writerow([datetime.date.today().isoformat(),market,prop,rate,stay,conv["los"],source or "manual",note])
    print(f"Recorded: {market} | {prop} | US${rate} | stay {stay}")

if __name__=="__main__":
    main()
