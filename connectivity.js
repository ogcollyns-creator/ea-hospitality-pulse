// EA Pulse Connectivity Tracker.
// HONEST SCOPE: true seats-per-week data sits behind OAG/Cirium paywalls, so we do NOT
// publish a seat count we cannot verify. Instead we track (a) official airport traffic
// — lagging but authoritative — and (b) confirmed route events, which are forward-looking
// and are what operators can actually act on.
window.CONNECT = {
 updated: "25 July 2026",
 traffic: [
  { airport:"JKIA Nairobi", code:"NBO", flag:"🇰🇪", metric:"Passenger arrivals",
    value:"227,974", period:"March 2026", change:"−0.4% vs February (228,826)", dir:"down",
    note:"Broadly flat month-on-month. Major expansion planned under the National Infrastructure Fund — new facilities and a runway.",
    source:"KNBS", verified:true },
  { airport:"Entebbe", code:"EBB", flag:"🇺🇬", metric:"International arrivals",
    value:"239,850", period:"Q1 2026", change:"−7.9% vs Q1 2025 (260,434)", dir:"down",
    note:"A material decline, consistent with the Ebola outbreak and advisory environment. This is the clearest hard evidence that the Uganda shock is showing up in actual traffic — not just sentiment. Watch Q2 for whether it deepens.",
    source:"UCAA via Aviation Week", verified:true },
  { airport:"Entebbe", code:"EBB", flag:"🇺🇬", metric:"Terminal capacity",
    value:"3.5m/yr", period:"From Jan 2026", change:"up from 2m", dir:"up",
    note:"New passenger terminal opened January 2026, lifting capacity from 2m to at least 3.5m annually. Capacity is no longer Uganda's constraint — demand is.",
    source:"UCAA", verified:true }
 ],
 routes: [
  { carrier:"Safarilink", route:"Nairobi ⇄ Entebbe (non-stop)", status:"Operating", effective:"1 May 2026",
    impact:"Cuts a regional connection that previously routed via Kisumu. Easier multi-country itineraries; good for Kampala city hotels chasing transit corporate traffic.",
    segment:"City", source:"Safarilink / KATA", dir:"up" },
  { carrier:"Safarilink", route:"Nairobi ⇄ Kisumu ⇄ Entebbe", status:"Continues", effective:"Since Jan 2026",
    impact:"Twice-daily service retained alongside the non-stop.", segment:"City", source:"KATA", dir:"flat" },
  { carrier:"Uganda Airlines", route:"14 destinations ex-Entebbe", status:"Operating", effective:"July 2026 schedule",
    impact:"Daily Nairobi rotations and three weekly to Zanzibar. Build UG-origin weekend packages around the Zanzibar frequency.",
    segment:"City, Beach", source:"KATA", dir:"up" },
  { carrier:"RwandAir", route:"Kigali ⇄ Zanzibar", status:"Driving 2026 growth", effective:"2026",
    impact:"Opens Rwanda–Zanzibar safari-and-beach combinations without routing through Nairobi or Dar.",
    segment:"Beach, Bush", source:"Aviation trade press", dir:"up" },
  { carrier:"Flightlink (TZ)", route:"Entebbe & Kigali", status:"Announced — acquiring ATR 72-600s", effective:"2026",
    impact:"Forward signal, not yet flying. If it lands, it adds regional lift into two capitals.",
    segment:"City", source:"Aviation Week", dir:"up" },
  { carrier:"Airlink (SA)", route:"Johannesburg ⇄ Zanzibar / Nairobi", status:"Launching", effective:"2026",
    impact:"Southern African feed into both a beach and a city market — a source market EA operators under-work.",
    segment:"Beach, City", source:"Travel And Tour World", dir:"up" }
 ]
};
