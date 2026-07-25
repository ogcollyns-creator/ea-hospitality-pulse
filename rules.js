// EA Pulse regulatory tracker — levies, fees, permits and entry rules.
// Maintained by the daily Pulse task. Every entry carries a source; anything
// unverified is flagged so readers never act on a stale number unknowingly.
window.RULES = {
 updated: "25 July 2026",
 groups: [
  { country:"Kenya", flag:"🇰🇪", items:[
    {rule:"Electronic Travel Authorisation (ETA)", amount:"US$30", who:"All non-EAC visitors, including infants", effective:"In force since Jan 2024", note:"Online only; typically 24–72h. Apply before travel — there is no visa on arrival.", source:"Kenya eTA portal", verified:true},
    {rule:"Maasai Mara park fee", amount:"US$100 low / US$200 peak", who:"Non-resident adult, per person per day", effective:"Current 2026 season", note:"Peak pricing bites during migration — build it into quoted rates.", source:"Narok County / operator schedules", verified:true},
    {rule:"KWS park fees (Amboseli, Nakuru, Tsavo)", amount:"US$80–90 per day", who:"Non-resident adult", effective:"Current", note:"Paid via kwspay.ecitizen.go.ke. Nairobi NP US$80.", source:"Kenya Wildlife Service", verified:true},
    {rule:"COVID-19 entry requirements", amount:"None", who:"All", effective:"Fully lifted", note:"No testing, vaccination proof or quarantine. Remove any legacy wording from your pre-arrival comms.", source:"Ministry of Health", verified:true}
  ]},
  { country:"Uganda", flag:"🇺🇬", items:[
    {rule:"Tourist e-Visa", amount:"US$50 + US$1.50 admin", who:"Single entry, up to 90 days", effective:"Current", note:"NO visa on arrival — e-Visa is the only route. Guests must print the approval letter.", source:"Uganda e-Visa portal", verified:true},
    {rule:"Gorilla permit (Bwindi & Mgahinga)", amount:"US$800", who:"Foreign non-resident", effective:"Current", note:"US$700 foreign resident · US$500 African · UGX 300,000 EAC citizens.", source:"Uganda Wildlife Authority", verified:true},
    {rule:"Low-season gorilla permit discount", amount:"US$600 (from US$800)", who:"Foreign non-resident", effective:"April, May & November", note:"Introduced Feb 2026. A genuine packaging opportunity — sell the shoulder season on price.", source:"Uganda Wildlife Authority", verified:true},
    {rule:"Yellow fever certificate", amount:"Required", who:"All arrivals", effective:"Current", note:"Must be uploaded at visa application. A missing certificate stops the guest at immigration.", source:"Ministry of Health", verified:true}
  ]},
  { country:"Tanzania", flag:"🇹🇿", items:[
    {rule:"Tourist visa", amount:"US$50 standard · US$100 US citizens", who:"US citizens receive multiple entry", effective:"Current", note:"Apply online ahead of travel.", source:"Tanzania Immigration", verified:true}
  ]},
  { country:"Zanzibar", flag:"🇹🇿", items:[
    {rule:"Mandatory inbound travel insurance", amount:"US$44 per adult", who:"Every foreign visitor", effective:"Since Oct 2024", note:"Bought from the Zanzibar government at visitzanzibar.go.tz — private policies do not substitute. Covers medical to US$50,000. PUT THIS IN YOUR PRE-ARRIVAL EMAIL: a guest discovering it at the airport is a bad review.", source:"Zanzibar Insurance Corporation", verified:true, flag:"action"},
    {rule:"Infrastructure tax (bed-night levy)", amount:"US$2–5 per person per night", who:"All in-house guests, by hotel star rating", effective:"Current", note:"Hotels must collect on behalf of the Zanzibar Revenue Board. Usually folded into the rate — decide deliberately whether you absorb or show it.", source:"Zanzibar Revenue Board", verified:true},
    {rule:"Card payment surcharge", amount:"3–5%", who:"Card transactions", effective:"Current", note:"Widely applied. Material on a long stay — flag it at booking, not checkout.", source:"Operator practice", verified:true},
    {rule:"Visa", amount:"US$50", who:"Most nationalities", effective:"Current", note:"Zanzibar follows Tanzania visa rules.", source:"Tanzania Immigration", verified:true}
  ]},
  { country:"Rwanda", flag:"🇷🇼", items:[
    {rule:"Gorilla permit", amount:"US$1,500", who:"Foreign non-resident", effective:"Current", note:"US$500 foreign resident · US$200 Rwandan & EAC citizens. Nearly 2× Uganda's US$800 — the pricing gap is a live competitive dynamic for the whole gorilla circuit.", source:"Rwanda Development Board", verified:true},
    {rule:"Tourist visa", amount:"~US$35", who:"Most nationalities", effective:"Verify before quoting", note:"Our most recent confirmation predates 2026 — confirm on the Irembo portal before publishing to clients.", source:"Irembo / RDB", verified:false},
    {rule:"Yellow fever certificate", amount:"Required", who:"All arrivals", effective:"Current", note:"Mandatory, uploaded at application.", source:"Ministry of Health", verified:true}
  ]},
  { country:"Regional", flag:"🌍", items:[
    {rule:"East Africa Tourist Visa (EATV)", amount:"US$100", who:"Kenya + Uganda + Rwanda", effective:"Current", note:"90-day multiple entry, free movement between the three. Apply through your FIRST country of entry. Materially cheaper than three separate visas — sell multi-country itineraries on it.", source:"EAC partner states", verified:true, flag:"action"}
  ]}
 ]
};
