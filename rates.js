window.RATE_INDEX = {
 "updated": "2026-08-02 14:45",
 "convention": {
  "los": 2,
  "lead_days": 30,
  "occupancy": "2 adults",
  "currency": "USD"
 },
 "minN": 3,
 "lookbackWeeks": 6,
 "method": "chain-linked matched-sample",
 "methodNote": "Each property is compared only with itself, so the index measures rate MOVEMENT validly even though the basket mixes meal bases and rate types. Raw medians are context only and are not comparable across markets — check levelComparable before quoting a level.",
 "spreadNote": "Commission-leakage spread = median of (OTA rate / direct rate - 1) for the same property in the same week. Computed only where the direct rate is room-only or B&B, since an OTA lowest rate is not comparable with a fully-inclusive safari rate. Markets where no property qualifies report null.",
 "totalObservations": 12,
 "distinctProperties": 12,
 "basketSize": 40,
 "markets": {
  "nairobi": {
   "label": "Nairobi",
   "segment": "city",
   "country": "KE",
   "basketSize": 8,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 206.0,
     "n": 1,
     "observations": 1,
     "coverage": 12,
     "confident": false,
     "basisMix": {
      "BB": 1
     },
     "rateTypeMix": {
      "international": 1
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": null
    }
   ],
   "baseline": null,
   "latest": {
    "week": "2026-W31",
    "weekStart": "2026-07-27",
    "median": 206.0,
    "n": 1,
    "observations": 1,
    "coverage": 12,
    "confident": false,
    "basisMix": {
     "BB": 1
    },
    "rateTypeMix": {
     "international": 1
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": null
   },
   "wow": null,
   "basisMix": {
    "BB": 1
   },
   "rateTypeMix": {
    "international": 1
   },
   "levelComparable": true,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "coast": {
   "label": "Mombasa & Diani",
   "segment": "beach",
   "country": "KE",
   "basketSize": 7,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 278.0,
     "n": 5,
     "observations": 5,
     "coverage": 71,
     "confident": true,
     "basisMix": {
      "HB": 3,
      "AI": 2
     },
     "rateTypeMix": {
      "resident": 5
     },
     "levelComparable": false,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 278.0,
   "latest": {
    "week": "2026-W31",
    "weekStart": "2026-07-27",
    "median": 278.0,
    "n": 5,
    "observations": 5,
    "coverage": 71,
    "confident": true,
    "basisMix": {
     "HB": 3,
     "AI": 2
    },
    "rateTypeMix": {
     "resident": 5
    },
    "levelComparable": false,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "HB": 3,
    "AI": 2
   },
   "rateTypeMix": {
    "resident": 5
   },
   "levelComparable": false,
   "residentOnly": true,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "zanzibar": {
   "label": "Zanzibar",
   "segment": "beach",
   "country": "ZNZ",
   "basketSize": 8,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 1160.0,
     "n": 1,
     "observations": 1,
     "coverage": 12,
     "confident": false,
     "basisMix": {
      "HB": 1
     },
     "rateTypeMix": {
      "international": 1
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": null
    }
   ],
   "baseline": null,
   "latest": {
    "week": "2026-W31",
    "weekStart": "2026-07-27",
    "median": 1160.0,
    "n": 1,
    "observations": 1,
    "coverage": 12,
    "confident": false,
    "basisMix": {
     "HB": 1
    },
    "rateTypeMix": {
     "international": 1
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": null
   },
   "wow": null,
   "basisMix": {
    "HB": 1
   },
   "rateTypeMix": {
    "international": 1
   },
   "levelComparable": true,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "kigali": {
   "label": "Kigali",
   "segment": "city",
   "country": "RW",
   "basketSize": 5,
   "series": [],
   "baseline": null,
   "latest": null,
   "wow": null,
   "basisMix": {},
   "rateTypeMix": {},
   "levelComparable": false,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "kampala": {
   "label": "Kampala & Entebbe",
   "segment": "city",
   "country": "UG",
   "basketSize": 5,
   "series": [],
   "baseline": null,
   "latest": null,
   "wow": null,
   "basisMix": {},
   "rateTypeMix": {},
   "levelComparable": false,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "safari": {
   "label": "Mara & Serengeti",
   "segment": "bush",
   "country": "KE/TZ",
   "basketSize": 7,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 1996.0,
     "n": 5,
     "observations": 5,
     "coverage": 71,
     "confident": true,
     "basisMix": {
      "FB+": 1,
      "FI": 2,
      "FB": 2
     },
     "rateTypeMix": {
      "international": 5
     },
     "levelComparable": false,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 1996.0,
   "latest": {
    "week": "2026-W31",
    "weekStart": "2026-07-27",
    "median": 1996.0,
    "n": 5,
    "observations": 5,
    "coverage": 71,
    "confident": true,
    "basisMix": {
     "FB+": 1,
     "FI": 2,
     "FB": 2
    },
    "rateTypeMix": {
     "international": 5
    },
    "levelComparable": false,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "FB+": 1,
    "FI": 2,
    "FB": 2
   },
   "rateTypeMix": {
    "international": 5
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  }
 },
 "benchmarks": {
  "updated": "2026-07-24",
  "items": [
   {
    "market": "Nairobi",
    "metric": "Short-let ADR",
    "value": "US$47",
    "period": "2026",
    "source": "AirDNA",
    "url": "https://www.airdna.co/vacation-rental-data/app/ke/default/nairobi/overview",
    "note": "Short-term rental market, not branded hotels — a demand-side proxy."
   },
   {
    "market": "Nairobi",
    "metric": "Short-let occupancy",
    "value": "41%",
    "period": "2026",
    "source": "AirDNA",
    "url": "https://www.airdna.co/vacation-rental-data/app/ke/default/nairobi/overview",
    "note": "Across ~13,110 active listings."
   },
   {
    "market": "Nairobi",
    "metric": "Short-let RevPAR",
    "value": "US$19",
    "period": "2026",
    "source": "AirDNA",
    "url": "https://www.airdna.co/vacation-rental-data/app/ke/default/nairobi/overview",
    "note": "Rate weighted by occupancy."
   },
   {
    "market": "Nairobi",
    "metric": "Branded room pipeline",
    "value": "~3,650 rooms",
    "period": "Q1 2026",
    "source": "W Hospitality Group via Tourism Update",
    "url": "https://www.tourismupdate.com/article/is-nairobi-building-too-many-hotels",
    "note": "~1,500 rooms opening in 2026; occupancy already off ~10pts since 2023."
   },
   {
    "market": "Zanzibar",
    "metric": "Annual arrivals",
    "value": "917,167",
    "period": "2025",
    "source": "Zanzibar tourism data via Travel And Tour World",
    "url": "https://www.travelandtourworld.com/",
    "note": "Up roughly 24% on 2024."
   },
   {
    "market": "Tanzania",
    "metric": "Tourism earnings",
    "value": "US$4.41bn",
    "period": "2025",
    "source": "Tanzania national statistics",
    "url": "https://www.tanzaniatourism.go.tz/",
    "note": "Record high; 2,294,495 international arrivals."
   }
  ]
 }
};
