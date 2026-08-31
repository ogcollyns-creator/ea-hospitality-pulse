window.RATE_INDEX = {
 "updated": "2026-08-31 11:19",
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
 "wowNote": "wow is the matched-sample link for the latest week. wowClean is the same link computed only on pairs whose meal basis was KNOWN and UNCHANGED between the two weeks; basisChangedPairs counts the pairs excluded from it. Where basisChangedPairs is large relative to matched, the headline wow is partly a re-basing artefact — quote wowClean, or quote no move at all.",
 "spreadNote": "Commission-leakage spread = median of (OTA rate / direct rate - 1) for the same property in the same week. Computed only where the direct rate is room-only or B&B, since an OTA lowest rate is not comparable with a fully-inclusive safari rate. Markets where no property qualifies report null.",
 "totalObservations": 419,
 "distinctProperties": 123,
 "basketSize": 133,
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
     "median": 190.88,
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
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 187.43,
     "n": 9,
     "observations": 9,
     "coverage": 56,
     "confident": true,
     "basisMix": {
      "BB": 9
     },
     "rateTypeMix": {
      "international": 9
     },
     "levelComparable": true,
     "matched": 9,
     "link": 0.99385,
     "index": 99.4,
     "basisChangedPairs": 0,
     "cleanMatched": 9,
     "linkClean": 0.99385
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 212.72,
     "n": 8,
     "observations": 8,
     "coverage": 50,
     "confident": true,
     "basisMix": {
      "BB": 8
     },
     "rateTypeMix": {
      "international": 8
     },
     "levelComparable": true,
     "matched": 8,
     "link": 1.07215,
     "index": 106.6,
     "basisChangedPairs": 0,
     "cleanMatched": 8,
     "linkClean": 1.07215
    }
   ],
   "baseline": 190.88,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 212.72,
    "n": 8,
    "observations": 8,
    "coverage": 50,
    "confident": true,
    "basisMix": {
     "BB": 8
    },
    "rateTypeMix": {
     "international": 8
    },
    "levelComparable": true,
    "matched": 8,
    "link": 1.07215,
    "index": 106.6,
    "basisChangedPairs": 0,
    "cleanMatched": 8,
    "linkClean": 1.07215
   },
   "wow": 7.2,
   "wowClean": 7.2,
   "basisChangedPairs": 0,
   "basisMix": {
    "BB": 28
   },
   "rateTypeMix": {
    "international": 28
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
      "median": 221.0,
      "n": 8,
      "observations": 8,
      "coverage": 50,
      "confident": true,
      "basisMix": {
       "UNK": 8
      },
      "rateTypeMix": {
       "international": 8
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": 100.0
     },
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 239.75,
      "n": 10,
      "observations": 10,
      "coverage": 62,
      "confident": true,
      "basisMix": {
       "UNK": 10
      },
      "rateTypeMix": {
       "international": 10
      },
      "levelComparable": true,
      "matched": 7,
      "link": 1.11298,
      "index": 111.3,
      "basisChangedPairs": 7,
      "cleanMatched": 0,
      "linkClean": null
     },
     {
      "week": "2026-W34",
      "weekStart": "2026-08-17",
      "median": 213.0,
      "n": 7,
      "observations": 7,
      "coverage": 44,
      "confident": true,
      "basisMix": {
       "UNK": 7
      },
      "rateTypeMix": {
       "international": 7
      },
      "levelComparable": true,
      "matched": 7,
      "link": 0.74298,
      "index": 82.7,
      "basisChangedPairs": 7,
      "cleanMatched": 0,
      "linkClean": null
     },
     {
      "week": "2026-W35",
      "weekStart": "2026-08-24",
      "median": 195.5,
      "n": 6,
      "observations": 6,
      "coverage": 38,
      "confident": true,
      "basisMix": {
       "UNK": 6
      },
      "rateTypeMix": {
       "international": 6
      },
      "levelComparable": true,
      "matched": 6,
      "link": 0.96825,
      "index": 80.1,
      "basisChangedPairs": 6,
      "cleanMatched": 0,
      "linkClean": null
     }
    ],
    "latest": {
     "week": "2026-W35",
     "weekStart": "2026-08-24",
     "median": 195.5,
     "n": 6,
     "observations": 6,
     "coverage": 38,
     "confident": true,
     "basisMix": {
      "UNK": 6
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": true,
     "matched": 6,
     "link": 0.96825,
     "index": 80.1,
     "basisChangedPairs": 6,
     "cleanMatched": 0,
     "linkClean": null
    },
    "wow": -3.2
   },
   "spread": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "spreadPct": -7.1,
     "n": 6,
     "skippedNonComparableBasis": 0
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": 3.3,
     "n": 8,
     "skippedNonComparableBasis": 0
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "spreadPct": -9.1,
     "n": 5,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "spreadPct": -9.1,
    "n": 5,
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
      "BB": 9,
      "UNK": 1
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": false,
     "matched": 4,
     "link": 1.10506,
     "index": 110.5,
     "basisChangedPairs": 4,
     "cleanMatched": 0,
     "linkClean": null
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 265.92,
     "n": 10,
     "observations": 10,
     "coverage": 77,
     "confident": true,
     "basisMix": {
      "FB": 1,
      "BB": 9
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": false,
     "matched": 9,
     "link": 1.0,
     "index": 110.5,
     "basisChangedPairs": 1,
     "cleanMatched": 8,
     "linkClean": 0.99844
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 315.0,
     "n": 7,
     "observations": 7,
     "coverage": 54,
     "confident": true,
     "basisMix": {
      "BB": 7
     },
     "rateTypeMix": {
      "international": 7
     },
     "levelComparable": true,
     "matched": 7,
     "link": 1.0,
     "index": 110.5,
     "basisChangedPairs": 0,
     "cleanMatched": 7,
     "linkClean": 1.0
    }
   ],
   "baseline": 278.0,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 315.0,
    "n": 7,
    "observations": 7,
    "coverage": 54,
    "confident": true,
    "basisMix": {
     "BB": 7
    },
    "rateTypeMix": {
     "international": 7
    },
    "levelComparable": true,
    "matched": 7,
    "link": 1.0,
    "index": 110.5,
    "basisChangedPairs": 0,
    "cleanMatched": 7,
    "linkClean": 1.0
   },
   "wow": 0.0,
   "wowClean": 0.0,
   "basisChangedPairs": 0,
   "basisMix": {
    "HB": 3,
    "AI": 2,
    "BB": 25,
    "UNK": 1,
    "FB": 1
   },
   "rateTypeMix": {
    "resident": 5,
    "international": 27
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
      "median": 216.5,
      "n": 6,
      "observations": 6,
      "coverage": 46,
      "confident": true,
      "basisMix": {
       "BB": 5,
       "UNK": 1
      },
      "rateTypeMix": {
       "international": 6
      },
      "levelComparable": false,
      "matched": 0,
      "link": null,
      "index": 100.0
     },
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 209.0,
      "n": 9,
      "observations": 9,
      "coverage": 69,
      "confident": true,
      "basisMix": {
       "UNK": 9
      },
      "rateTypeMix": {
       "international": 9
      },
      "levelComparable": true,
      "matched": 6,
      "link": 0.93686,
      "index": 93.7,
      "basisChangedPairs": 6,
      "cleanMatched": 0,
      "linkClean": null
     },
     {
      "week": "2026-W34",
      "weekStart": "2026-08-17",
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
      "matched": 1,
      "link": 1.0,
      "index": 93.7,
      "basisChangedPairs": 1,
      "cleanMatched": 0,
      "linkClean": null
     }
    ],
    "latest": {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
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
     "matched": 1,
     "link": 1.0,
     "index": 93.7,
     "basisChangedPairs": 1,
     "cleanMatched": 0,
     "linkClean": null
    },
    "wow": 0.0
   },
   "spread": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "spreadPct": 22.0,
     "n": 5,
     "skippedNonComparableBasis": 0
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": 1.4,
     "n": 7,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": 1.4,
    "n": 7,
    "skippedNonComparableBasis": 0
   }
  },
  "zanzibar": {
   "label": "Zanzibar",
   "segment": "beach",
   "country": "ZNZ",
   "basketSize": 12,
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
     "coverage": 75,
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
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 1160.0,
     "n": 9,
     "observations": 9,
     "coverage": 75,
     "confident": true,
     "basisMix": {
      "AI": 4,
      "HB": 4,
      "BB": 1
     },
     "rateTypeMix": {
      "international": 9
     },
     "levelComparable": false,
     "matched": 9,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 2,
     "cleanMatched": 7,
     "linkClean": 1.0
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 917.5,
     "n": 8,
     "observations": 8,
     "coverage": 67,
     "confident": true,
     "basisMix": {
      "AI": 3,
      "HB": 4,
      "BB": 1
     },
     "rateTypeMix": {
      "international": 8
     },
     "levelComparable": false,
     "matched": 8,
     "link": 1.01759,
     "index": 101.8,
     "basisChangedPairs": 0,
     "cleanMatched": 8,
     "linkClean": 1.01759
    }
   ],
   "baseline": 818.5,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 917.5,
    "n": 8,
    "observations": 8,
    "coverage": 67,
    "confident": true,
    "basisMix": {
     "AI": 3,
     "HB": 4,
     "BB": 1
    },
    "rateTypeMix": {
     "international": 8
    },
    "levelComparable": false,
    "matched": 8,
    "link": 1.01759,
    "index": 101.8,
    "basisChangedPairs": 0,
    "cleanMatched": 8,
    "linkClean": 1.01759
   },
   "wow": 1.8,
   "wowClean": 1.8,
   "basisChangedPairs": 0,
   "basisMix": {
    "HB": 13,
    "AI": 11,
    "UNK": 2,
    "BB": 2
   },
   "rateTypeMix": {
    "international": 28
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 867.0,
      "n": 8,
      "observations": 8,
      "coverage": 67,
      "confident": true,
      "basisMix": {
       "UNK": 8
      },
      "rateTypeMix": {
       "international": 8
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": 100.0
     }
    ],
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 867.0,
     "n": 8,
     "observations": 8,
     "coverage": 67,
     "confident": true,
     "basisMix": {
      "UNK": 8
     },
     "rateTypeMix": {
      "international": 8
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
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": -33.0,
     "n": 1,
     "skippedNonComparableBasis": 7
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": -33.0,
    "n": 1,
    "skippedNonComparableBasis": 7
   }
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
     "median": 200.69,
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
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 193.5,
     "n": 6,
     "observations": 6,
     "coverage": 55,
     "confident": true,
     "basisMix": {
      "BB": 6
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": true,
     "matched": 6,
     "link": 0.92374,
     "index": 92.4,
     "basisChangedPairs": 5,
     "cleanMatched": 1,
     "linkClean": 1.00252
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 188.75,
     "n": 10,
     "observations": 10,
     "coverage": 91,
     "confident": true,
     "basisMix": {
      "BB": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 8,
     "link": 1.01026,
     "index": 93.3,
     "basisChangedPairs": 1,
     "cleanMatched": 7,
     "linkClean": 1.0
    }
   ],
   "baseline": 200.69,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 188.75,
    "n": 10,
    "observations": 10,
    "coverage": 91,
    "confident": true,
    "basisMix": {
     "BB": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 8,
    "link": 1.01026,
    "index": 93.3,
    "basisChangedPairs": 1,
    "cleanMatched": 7,
    "linkClean": 1.0
   },
   "wow": 1.0,
   "wowClean": 0.0,
   "basisChangedPairs": 1,
   "basisMix": {
    "UNK": 6,
    "BB": 18
   },
   "rateTypeMix": {
    "international": 24
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 163.5,
      "n": 10,
      "observations": 10,
      "coverage": 91,
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
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 163.5,
     "n": 10,
     "observations": 10,
     "coverage": 91,
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
    "wow": null
   },
   "spread": [
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": 27.6,
     "n": 6,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": 27.6,
    "n": 6,
    "skippedNonComparableBasis": 0
   }
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
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 158.51,
     "n": 10,
     "observations": 10,
     "coverage": 83,
     "confident": true,
     "basisMix": {
      "BB": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 8,
     "link": 1.0082,
     "index": 100.8,
     "basisChangedPairs": 0,
     "cleanMatched": 8,
     "linkClean": 1.0082
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 182.0,
     "n": 11,
     "observations": 11,
     "coverage": 92,
     "confident": true,
     "basisMix": {
      "BB": 11
     },
     "rateTypeMix": {
      "international": 11
     },
     "levelComparable": true,
     "matched": 11,
     "link": 1.0,
     "index": 100.8,
     "basisChangedPairs": 1,
     "cleanMatched": 10,
     "linkClean": 1.057
    }
   ],
   "baseline": 176.0,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 182.0,
    "n": 11,
    "observations": 11,
    "coverage": 92,
    "confident": true,
    "basisMix": {
     "BB": 11
    },
    "rateTypeMix": {
     "international": 11
    },
    "levelComparable": true,
    "matched": 11,
    "link": 1.0,
    "index": 100.8,
    "basisChangedPairs": 1,
    "cleanMatched": 10,
    "linkClean": 1.057
   },
   "wow": 0.0,
   "wowClean": 5.7,
   "basisChangedPairs": 1,
   "basisMix": {
    "UNK": 1,
    "BB": 29
   },
   "rateTypeMix": {
    "international": 30
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 187.0,
      "n": 10,
      "observations": 10,
      "coverage": 83,
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
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 187.0,
     "n": 10,
     "observations": 10,
     "coverage": 83,
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
    "wow": null
   },
   "spread": [
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": 6.5,
     "n": 9,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": 6.5,
    "n": 9,
    "skippedNonComparableBasis": 0
   }
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
     "index": 100.0,
     "basisChangedPairs": 2,
     "cleanMatched": 1,
     "linkClean": 0.8999
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 4299.5,
     "n": 22,
     "observations": 22,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "FB": 5,
      "AI": 6,
      "FI": 10,
      "FB+": 1
     },
     "rateTypeMix": {
      "international": 22
     },
     "levelComparable": false,
     "matched": 20,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 8,
     "cleanMatched": 12,
     "linkClean": 1.0
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 4900.0,
     "n": 19,
     "observations": 19,
     "coverage": 86,
     "confident": true,
     "basisMix": {
      "FB": 4,
      "AI": 6,
      "FI": 9
     },
     "rateTypeMix": {
      "international": 19
     },
     "levelComparable": false,
     "matched": 19,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 0,
     "cleanMatched": 19,
     "linkClean": 1.0
    }
   ],
   "baseline": 1996.0,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 4900.0,
    "n": 19,
    "observations": 19,
    "coverage": 86,
    "confident": true,
    "basisMix": {
     "FB": 4,
     "AI": 6,
     "FI": 9
    },
    "rateTypeMix": {
     "international": 19
    },
    "levelComparable": false,
    "matched": 19,
    "link": 1.0,
    "index": 100.0,
    "basisChangedPairs": 0,
    "cleanMatched": 19,
    "linkClean": 1.0
   },
   "wow": 0.0,
   "wowClean": 0.0,
   "basisChangedPairs": 0,
   "basisMix": {
    "FB+": 2,
    "FI": 21,
    "FB": 15,
    "AI": 18,
    "UNK": 8
   },
   "rateTypeMix": {
    "international": 64
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
   "basketSize": 8,
   "series": [
    {
     "week": "2026-W32",
     "weekStart": "2026-08-03",
     "median": 214.15,
     "n": 6,
     "observations": 6,
     "coverage": 75,
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
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 193.93,
     "n": 4,
     "observations": 4,
     "coverage": 50,
     "confident": true,
     "basisMix": {
      "BB": 4
     },
     "rateTypeMix": {
      "international": 4
     },
     "levelComparable": true,
     "matched": 3,
     "link": 0.80125,
     "index": 80.1,
     "basisChangedPairs": 3,
     "cleanMatched": 0,
     "linkClean": null
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 213.0,
     "n": 6,
     "observations": 6,
     "coverage": 75,
     "confident": true,
     "basisMix": {
      "BB": 6
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": true,
     "matched": 5,
     "link": 1.04373,
     "index": 83.6,
     "basisChangedPairs": 2,
     "cleanMatched": 3,
     "linkClean": 1.23995
    }
   ],
   "baseline": 214.15,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 213.0,
    "n": 6,
    "observations": 6,
    "coverage": 75,
    "confident": true,
    "basisMix": {
     "BB": 6
    },
    "rateTypeMix": {
     "international": 6
    },
    "levelComparable": true,
    "matched": 5,
    "link": 1.04373,
    "index": 83.6,
    "basisChangedPairs": 2,
    "cleanMatched": 3,
    "linkClean": 1.23995
   },
   "wow": 4.4,
   "wowClean": 24.0,
   "basisChangedPairs": 2,
   "basisMix": {
    "UNK": 6,
    "BB": 10
   },
   "rateTypeMix": {
    "international": 16
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 201.75,
      "n": 6,
      "observations": 6,
      "coverage": 75,
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
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 201.75,
     "n": 6,
     "observations": 6,
     "coverage": 75,
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
    "wow": null
   },
   "spread": [
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": 7.8,
     "n": 3,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": 7.8,
    "n": 3,
    "skippedNonComparableBasis": 0
   }
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
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 300.5,
     "n": 4,
     "observations": 4,
     "coverage": 44,
     "confident": true,
     "basisMix": {
      "BB": 4
     },
     "rateTypeMix": {
      "international": 4
     },
     "levelComparable": true,
     "matched": 3,
     "link": 0.99901,
     "index": 99.9,
     "basisChangedPairs": 3,
     "cleanMatched": 0,
     "linkClean": null
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 300.0,
     "n": 7,
     "observations": 7,
     "coverage": 78,
     "confident": true,
     "basisMix": {
      "BB": 6,
      "FB": 1
     },
     "rateTypeMix": {
      "international": 7
     },
     "levelComparable": false,
     "matched": 6,
     "link": 1.0,
     "index": 99.9,
     "basisChangedPairs": 2,
     "cleanMatched": 4,
     "linkClean": 1.0
    }
   ],
   "baseline": 300.4,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 300.0,
    "n": 7,
    "observations": 7,
    "coverage": 78,
    "confident": true,
    "basisMix": {
     "BB": 6,
     "FB": 1
    },
    "rateTypeMix": {
     "international": 7
    },
    "levelComparable": false,
    "matched": 6,
    "link": 1.0,
    "index": 99.9,
    "basisChangedPairs": 2,
    "cleanMatched": 4,
    "linkClean": 1.0
   },
   "wow": 0.0,
   "wowClean": 0.0,
   "basisChangedPairs": 2,
   "basisMix": {
    "UNK": 6,
    "BB": 10,
    "FB": 1
   },
   "rateTypeMix": {
    "international": 17
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 217.0,
      "n": 7,
      "observations": 7,
      "coverage": 78,
      "confident": true,
      "basisMix": {
       "UNK": 7
      },
      "rateTypeMix": {
       "international": 7
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": 100.0
     }
    ],
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 217.0,
     "n": 7,
     "observations": 7,
     "coverage": 78,
     "confident": true,
     "basisMix": {
      "UNK": 7
     },
     "rateTypeMix": {
      "international": 7
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
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": 2.0,
     "n": 3,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": 2.0,
    "n": 3,
    "skippedNonComparableBasis": 0
   }
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
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 3010.0,
     "n": 9,
     "observations": 9,
     "coverage": 90,
     "confident": true,
     "basisMix": {
      "FI": 9
     },
     "rateTypeMix": {
      "international": 9
     },
     "levelComparable": true,
     "matched": 9,
     "link": 1.11724,
     "index": 111.7,
     "basisChangedPairs": 9,
     "cleanMatched": 0,
     "linkClean": null
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 2137.0,
     "n": 10,
     "observations": 10,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "FI": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 10,
     "link": 1.0,
     "index": 111.7,
     "basisChangedPairs": 1,
     "cleanMatched": 9,
     "linkClean": 1.0
    }
   ],
   "baseline": 1770.0,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 2137.0,
    "n": 10,
    "observations": 10,
    "coverage": 100,
    "confident": true,
    "basisMix": {
     "FI": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 10,
    "link": 1.0,
    "index": 111.7,
    "basisChangedPairs": 1,
    "cleanMatched": 9,
    "linkClean": 1.0
   },
   "wow": 0.0,
   "wowClean": 0.0,
   "basisChangedPairs": 1,
   "basisMix": {
    "UNK": 10,
    "FI": 19
   },
   "rateTypeMix": {
    "international": 29
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 1070.0,
      "n": 1,
      "observations": 1,
      "coverage": 10,
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
     }
    ],
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 1070.0,
     "n": 1,
     "observations": 1,
     "coverage": 10,
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
    "wow": null
   },
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
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 142.5,
     "n": 6,
     "observations": 6,
     "coverage": 60,
     "confident": true,
     "basisMix": {
      "BB": 6
     },
     "rateTypeMix": {
      "international": 6
     },
     "levelComparable": true,
     "matched": 6,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 4,
     "cleanMatched": 2,
     "linkClean": 0.9227
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 113.75,
     "n": 10,
     "observations": 10,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "BB": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 6,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 0,
     "cleanMatched": 6,
     "linkClean": 1.0
    }
   ],
   "baseline": 151.25,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 113.75,
    "n": 10,
    "observations": 10,
    "coverage": 100,
    "confident": true,
    "basisMix": {
     "BB": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 6,
    "link": 1.0,
    "index": 100.0,
    "basisChangedPairs": 0,
    "cleanMatched": 6,
    "linkClean": 1.0
   },
   "wow": 0.0,
   "wowClean": 0.0,
   "basisChangedPairs": 0,
   "basisMix": {
    "BB": 18,
    "UNK": 4
   },
   "rateTypeMix": {
    "international": 22
   },
   "levelComparable": false,
   "residentOnly": false,
   "ota": {
    "series": [
     {
      "week": "2026-W33",
      "weekStart": "2026-08-10",
      "median": 100.5,
      "n": 8,
      "observations": 8,
      "coverage": 80,
      "confident": true,
      "basisMix": {
       "UNK": 8
      },
      "rateTypeMix": {
       "international": 8
      },
      "levelComparable": true,
      "matched": 0,
      "link": null,
      "index": 100.0
     }
    ],
    "latest": {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 100.5,
     "n": 8,
     "observations": 8,
     "coverage": 80,
     "confident": true,
     "basisMix": {
      "UNK": 8
     },
     "rateTypeMix": {
      "international": 8
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
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "spreadPct": -7.5,
     "n": 4,
     "skippedNonComparableBasis": 0
    }
   ],
   "spreadLatest": {
    "week": "2026-W33",
    "weekStart": "2026-08-10",
    "spreadPct": -7.5,
    "n": 4,
    "skippedNonComparableBasis": 0
   }
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
    },
    {
     "week": "2026-W33",
     "weekStart": "2026-08-10",
     "median": 4090.0,
     "n": 10,
     "observations": 10,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "FI": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 10,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 10,
     "cleanMatched": 0,
     "linkClean": null
    },
    {
     "week": "2026-W34",
     "weekStart": "2026-08-17",
     "median": 4090.0,
     "n": 10,
     "observations": 10,
     "coverage": 100,
     "confident": true,
     "basisMix": {
      "FI": 10
     },
     "rateTypeMix": {
      "international": 10
     },
     "levelComparable": true,
     "matched": 10,
     "link": 1.0,
     "index": 100.0,
     "basisChangedPairs": 0,
     "cleanMatched": 10,
     "linkClean": 1.0
    }
   ],
   "baseline": 4095.0,
   "latest": {
    "week": "2026-W34",
    "weekStart": "2026-08-17",
    "median": 4090.0,
    "n": 10,
    "observations": 10,
    "coverage": 100,
    "confident": true,
    "basisMix": {
     "FI": 10
    },
    "rateTypeMix": {
     "international": 10
    },
    "levelComparable": true,
    "matched": 10,
    "link": 1.0,
    "index": 100.0,
    "basisChangedPairs": 0,
    "cleanMatched": 10,
    "linkClean": 1.0
   },
   "wow": 0.0,
   "wowClean": 0.0,
   "basisChangedPairs": 0,
   "basisMix": {
    "UNK": 10,
    "FI": 20
   },
   "rateTypeMix": {
    "international": 30
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
