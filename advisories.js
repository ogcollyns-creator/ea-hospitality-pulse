// EA Hospitality Pulse — advisory status board data.
// Levels reflect MAIN TOURIST AREAS; regional exceptions are in the notes.
// Maintained by the scheduled Pulse task; verify against the official source before travel.
window.ADVISORIES = {
  updated: "2 August 2026 (evening)",
  rows: [
    { code:"KE", name:"Kenya", flag:"🇰🇪",
      us:{ level:2, note:"Terrorism & crime. Higher risk on the Somalia border and parts of the north coast (Lamu). Eastleigh & Kibera are Reconsider Travel (Level 3), NOT Do Not Travel. Rendered page still dated 17 March 2025 when checked 2 Aug 2026 — the late-July re-issue did not change the page text." },
      uk:{ level:2, note:"Against travel to the Kenya–Somalia border and parts of Lamu/north coast; core safari & coast areas unaffected." } },
    { code:"UG", name:"Uganda", flag:"🇺🇬",
      us:{ level:4, note:"Do not travel — Ebola (Bundibugyo) outbreak in the region." },
      uk:{ level:3, note:"Against all-but-essential travel to parts of western Uganda (Queen Elizabeth & Semuliki NP). Elections aftermath — avoid crowds." } },
    { code:"TZ", name:"Tanzania", flag:"🇹🇿",
      us:{ level:2, note:"Exercise increased caution." },
      uk:{ level:1, note:"No advisory against travel except within 20km of the Mozambique (Cabo Delgado) border." } },
    { code:"ZNZ", name:"Zanzibar", flag:"🇹🇿",
      us:{ level:2, note:"As mainland Tanzania; no Zanzibar-specific warning." },
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
