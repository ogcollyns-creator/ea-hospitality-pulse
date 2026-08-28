// EA Hospitality Pulse — advisory status board data.
// Levels reflect MAIN TOURIST AREAS; regional exceptions are in the notes.
// Maintained by the scheduled Pulse task; verify against the official source before travel.
window.ADVISORIES = {
  updated: "28 August 2026 (CORRECTION: UK Uganda is Level 1 — the FCDO advises against travel to no part of Uganda, and lifted the Queen Elizabeth/Semuliki restriction on 2 Dec 2025. We carried it wrong for nine months. Verified vs gov.uk 28 Aug 2026. Also standing: Nairobi's Eastleigh & Kibera are US Level 4, verified vs travel.state.gov 12 Aug 2026.)",
  rows: [
    { code:"KE", name:"Kenya", flag:"🇰🇪",
      us:{ level:2, note:"Terrorism, crime, kidnapping, unrest, health and 'Other'. Country level unchanged at 2. Re-issued 28 July 2026 (rendered page carries 'Date issued: July 28, 2026', verified 12 Aug 2026) — the 'Other (O)' indicator was added and the Nairobi neighbourhoods of EASTLEIGH and KIBERA are now LEVEL 4 DO NOT TRAVEL (crime, kidnapping), corrected from our earlier Level 3 reading. Also Level 4: Garissa, Wajir, Mandera, Lamu, Tana River (except Tsavo NP), Kilifi north of the C103 and coastal areas north of Malindi; West Pokot and western Turkana; Marsabit and Turkana within 50km of Ethiopia. Nairobi hotel corridors (Westlands, Upper Hill, Gigiri, CBD, Karen), Diani and Watamu are not in any Level 4 area." },
      uk:{ level:2, note:"Against travel to the Kenya–Somalia border and parts of Lamu/north coast; core safari & coast areas unaffected." } },
    { code:"UG", name:"Uganda", flag:"🇺🇬",
      us:{ level:4, note:"Do not travel — Ebola (Bundibugyo) outbreak in the region." },
      uk:{ level:1, note:"CORRECTED 28 Aug 2026 — the UK advises against travel to NO part of Uganda. We carried 'against all-but-essential travel to Queen Elizabeth & Semuliki NP' for nine months after the FCDO lifted it on 2 December 2025. Verified against gov.uk/foreign-travel-advice/uganda and its Regional risks page, 28 Aug 2026: still current at 25 Aug 2026, updated 27 Jul 2026, and the Warnings page carries no advice-against-travel block at all. Every 'advises against all travel' line on the Regional risks page refers to the DRC and South Sudan, NOT Uganda. Western Uganda carries caution language only (ADF, Kasese/Bundibugyo attacks Nov 2025). Bwindi and Mgahinga are open; armed escort on gorilla tracking is described as routine practice, not a warning. NOTE: mandatory National Cleaning Day, final Saturday monthly 07:00-10:00, nationwide movement restriction — tourists exempt (Uganda Police, 24 Aug 2026)." } },
    { code:"TZ", name:"Tanzania", flag:"🇹🇿",
      us:{ level:3, note:"Reconsider travel — RAISED from Level 2 to 3 on 31 Oct 2025 ('unrest' indicator added). Grounds: unrest, crime, terrorism (highest risk in the Mtwara Region near the Mozambique border), and targeting of gay & lesbian individuals. Verified vs travel.state.gov 4 Aug 2026." },
      uk:{ level:1, note:"No advisory against travel except within 20km of the Mozambique (Cabo Delgado) border." } },
    { code:"ZNZ", name:"Zanzibar", flag:"🇹🇿",
      us:{ level:3, note:"As mainland Tanzania (Level 3 since 31 Oct 2025); no Zanzibar-specific carve-out. Verified 4 Aug 2026." },
      uk:{ level:1, note:"No advisory against travel." } },
    { code:"RW", name:"Rwanda", flag:"🇷🇼",
      us:{ level:3, note:"Reconsider travel — regional Ebola risk and DRC border security." },
      uk:{ level:2, note:"Against all-but-essential travel to areas near the DRC and Burundi borders (Rubavu, Rusizi)." } }
  ],
  links: {
    us: {
      KE:"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/kenya-travel-advisory.html",
      UG:"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/uganda-travel-advisory.html",
      TZ:"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/tanzania-travel-advisory.html",
      ZNZ:"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/tanzania-travel-advisory.html",
      RW:"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/rwanda-travel-advisory.html"
    },
    uk: {
      KE:"https://www.gov.uk/foreign-travel-advice/kenya",
      UG:"https://www.gov.uk/foreign-travel-advice/uganda",
      TZ:"https://www.gov.uk/foreign-travel-advice/tanzania",
      ZNZ:"https://www.gov.uk/foreign-travel-advice/tanzania",
      RW:"https://www.gov.uk/foreign-travel-advice/rwanda"
    }
  }
};
