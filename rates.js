window.RATE_INDEX = {
 "updated": "2026-08-05 10:09",
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
 "totalObservations": 127,
 "distinctProperties": 108,
 "basketSize": 136,
 "markets": {
  "nairobi": {
   "label": "Nairobi",
   "segment": "city",
   "country": "KE",
   "basketSize": 16,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 206.0,
     "n": 1,
     "observations": 1,
     "coverage": 6,
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
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 381.77,
     "n": 10,
     "observations": 10,
     "coverage": 62,
     "confident": true,
     "basisMix": {
      "BB": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 381.77,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 381.77,
    "n": 10,
    "observations": 10,
    "coverage": 62,
    "confident": true,
    "basisMix": {
     "BB": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "BB": 11
   },
   "rateTypeMix": {
    "international": 11
   },
   "levelComparable": true,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W31",
      "weekStart": "2026-07-27",
      "median": 1054.0,
      "n": 1,
      "observations": 1,
      "coverage": 6,
      "confident": false,
      "basisMix": {
       "UNK": 1
      },
      "rateTypeMix": {
       "international": 1
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": null
     },
     {
      "week": "2026-W32",
      "weekStart": "2026-08-03",
      "median": 236.0,
      "n": 5,
      "observations": 5,
      "coverage": 31,
      "confident": true,
      "basisMix": {
       "UNK": 5
      },
      "rateTypeMix": {
       "international": 5
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": 100.0
     }
    ],
    "latest": {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 236.0,
     "n": 5,
     "observations": 5,
     "coverage": 31,
     "confident": true,
     "basisMix": {
      "UNK": 5
     },
     "rateTypeMix": {
      "international": 5
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    },
    "wow": null
   },
   "spread": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "spreadPct": -51.2,
     "n": 3,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "spreadPct": -51.2,
    "n": 3,
    "skippedNonComparableBasis": 0
   }
  },
  "coast": {
   "label": "Mombasa & Diani",
   "segment": "beach",
   "country": "KE",
   "basketSize": 13,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 278.0,
     "n": 5,
     "observations": 5,
     "coverage": 38,
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
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 304.33,
     "n": 10,
     "observations": 10,
     "coverage": 77,
     "confident": true,
     "basisMix": {
      "FB": 1,
      "BB": 8,
      "UNK": 1
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": false,
     "matched": 4,
     "link": 1.10506,
     "index": 110.5
    }
   ],
   "baseline": 278.0,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 304.33,
    "n": 10,
    "observations": 10,
    "coverage": 77,
    "confident": true,
    "basisMix": {
     "FB": 1,
     "BB": 8,
     "UNK": 1
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": false,
    "matched": 4,
    "link": 1.10506,
    "index": 110.5
   },
   "wow": 10.5,
   "basisMix": {
    "HB": 3,
    "AI": 2,
    "FB": 1,
    "BB": 8,
    "UNK": 1
   },
   "rateTypeMix": {
    "resident": 5,
    "international": 10
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W31",
      "weekStart": "2026-07-27",
      "median": 209.0,
      "n": 1,
      "observations": 1,
      "coverage": 8,
      "confident": false,
      "basisMix": {
       "UNK": 1
      },
      "rateTypeMix": {
       "international": 1
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": null
     },
     {
      "week": "2026-W32",
      "weekStart": "2026-08-03",
      "median": 218.0,
      "n": 5,
      "observations": 5,
      "coverage": 38,
      "confident": true,
      "basisMix": {
       "BB": 5
      },
      "rateTypeMix": {
       "international": 5
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": 100.0
     }
    ],
    "latest": {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 218.0,
     "n": 5,
     "observations": 5,
     "coverage": 38,
     "confident": true,
     "basisMix": {
      "BB": 5
     },
     "rateTypeMix": {
      "international": 5
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    },
    "wow": null
   },
   "spread": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "spreadPct": 22.0,
     "n": 5,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "spreadPct": 22.0,
    "n": 5,
    "skippedNonComparableBasis": 0
   }
  },
  "zanzibar": {
   "label": "Zanzibar",
   "segment": "beach",
   "country": "ZNZ",
   "basketSize": 13,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 1160.0,
     "n": 1,
     "observations": 1,
     "coverage": 8,
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
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 818.5,
     "n": 9,
     "observations": 10,
     "coverage": 69,
     "confident": true,
     "basisMix": {
      "HB": 4,
      "AI": 4,
      "UNK": 2
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": false,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 818.5,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 818.5,
    "n": 9,
    "observations": 10,
    "coverage": 69,
    "confident": true,
    "basisMix": {
     "HB": 4,
     "AI": 4,
     "UNK": 2
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": false,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "HB": 5,
    "AI": 4,
    "UNK": 2
   },
   "rateTypeMix": {
    "international": 11
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "kigali": {
   "label": "Kigali",
   "segment": "city",
   "country": "RW",
   "basketSize": 11,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 266.63,
     "n": 8,
     "observations": 8,
     "coverage": 73,
     "confident": true,
     "basisMix": {
      "UNK": 6,
      "BB": 2
     },
     "rateTypeMix": {
      "international": 8
     },
     "levelComparable": false,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 266.63,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 266.63,
    "n": 8,
    "observations": 8,
    "coverage": 73,
    "confident": true,
    "basisMix": {
     "UNK": 6,
     "BB": 2
    },
    "rateTypeMix": {
     "international": 8
    },
    "levelComparable": false,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "UNK": 6,
    "BB": 2
   },
   "rateTypeMix": {
    "international": 8
   },
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
   "basketSize": 12,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 176.0,
     "n": 9,
     "observations": 9,
     "coverage": 75,
     "confident": true,
     "basisMix": {
      "UNK": 1,
      "BB": 8
     },
     "rateTypeMix": {
      "international": 9
     },
     "levelComparable": false,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 176.0,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 176.0,
    "n": 9,
    "observations": 9,
    "coverage": 75,
    "confident": true,
    "basisMix": {
     "UNK": 1,
     "BB": 8
    },
    "rateTypeMix": {
     "international": 9
    },
    "levelComparable": false,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "UNK": 1,
    "BB": 8
   },
   "rateTypeMix": {
    "international": 9
   },
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
   "basketSize": 22,
   "series": [
    {
     "week": "2026-W31",
     "weekStart": "2026-07-27",
     "median": 1996.0,
     "n": 5,
     "observations": 5,
     "coverage": 23,
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
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 4293.0,
     "n": 18,
     "observations": 18,
     "coverage": 82,
     "confident": true,
     "basisMix": {
      "FB": 4,
      "AI": 6,
      "UNK": 8
     },
     "rateTypeMix": {
      "international": 18
     },
     "levelComparable": false,
     "matched": 3,
     "link": 1.0,
     "index": 100.0
    }
   ],
   "baseline": 1996.0,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 4293.0,
    "n": 18,
    "observations": 18,
    "coverage": 82,
    "confident": true,
    "basisMix": {
     "FB": 4,
     "AI": 6,
     "UNK": 8
    },
    "rateTypeMix": {
     "international": 18
    },
    "levelComparable": false,
    "matched": 3,
    "link": 1.0,
    "index": 100.0
   },
   "wow": 0.0,
   "basisMix": {
    "FB+": 1,
    "FI": 2,
    "FB": 6,
    "AI": 6,
    "UNK": 8
   },
   "rateTypeMix": {
    "international": 23
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "dar_arusha": {
   "label": "Dar es Salaam & Arusha",
   "segment": "city",
   "country": "TZ",
   "basketSize": 10,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 292.89,
     "n": 6,
     "observations": 6,
     "coverage": 60,
     "confident": true,
     "basisMix": {
      "UNK": 6
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 292.89,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 292.89,
    "n": 6,
    "observations": 6,
    "coverage": 60,
    "confident": true,
    "basisMix": {
     "UNK": 6
    },
    "rateTypeMix": {
     "international": 6
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "UNK": 6
   },
   "rateTypeMix": {
    "international": 6
   },
   "levelComparable": true,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "lakevictoria": {
   "label": "Lake Victoria & Entebbe",
   "segment": "beach",
   "country": "UG",
   "basketSize": 9,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 300.4,
     "n": 6,
     "observations": 6,
     "coverage": 67,
     "confident": true,
     "basisMix": {
      "UNK": 6
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 300.4,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 300.4,
    "n": 6,
    "observations": 6,
    "coverage": 67,
    "confident": true,
    "basisMix": {
     "UNK": 6
    },
    "rateTypeMix": {
     "international": 6
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "UNK": 6
   },
   "rateTypeMix": {
    "international": 6
   },
   "levelComparable": true,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "bwindi": {
   "label": "Bwindi, Kibale & QENP",
   "segment": "bush",
   "country": "UG",
   "basketSize": 10,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 1770.0,
     "n": 10,
     "observations": 10,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "UNK": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 1770.0,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 1770.0,
    "n": 10,
    "observations": 10,
    "coverage": 100,
    "confident": true,
    "basisMix": {
     "UNK": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "UNK": 10
   },
   "rateTypeMix": {
    "international": 10
   },
   "levelComparable": true,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "lakekivu": {
   "label": "Lake Kivu",
   "segment": "beach",
   "country": "RW",
   "basketSize": 10,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 151.25,
     "n": 6,
     "observations": 6,
     "coverage": 60,
     "confident": true,
     "basisMix": {
      "BB": 2,
      "UNK": 4
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": false,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 151.25,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 151.25,
    "n": 6,
    "observations": 6,
    "coverage": 60,
    "confident": true,
    "basisMix": {
     "BB": 2,
     "UNK": 4
    },
    "rateTypeMix": {
     "international": 6
    },
    "levelComparable": false,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "BB": 2,
    "UNK": 4
   },
   "rateTypeMix": {
    "international": 6
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": null,
   "spread": null,
   "spreadLatest": null
  },
  "volcanoes": {
   "label": "Volcanoes & Akagera",
   "segment": "bush",
   "country": "RW",
   "basketSize": 10,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 4095.0,
     "n": 10,
     "observations": 10,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "UNK": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 0,
     "link": null,
     "index": 100.0
    }
   ],
   "baseline": 4095.0,
   "latest": {
    "week": "2026-W32",
    "weekStart": "2026-08-03",
    "median": 4095.0,
    "n": 10,
    "observations": 10,
    "coverage": 100,
    "confident": true,
    "basisMix": {
     "UNK": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 0,
    "link": null,
    "index": 100.0
   },
   "wow": null,
   "basisMix": {
    "UNK": 10
   },
   "rateTypeMix": {
    "international": 10
   },
   "levelComparable": true,
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
