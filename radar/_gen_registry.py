#!/usr/bin/env python3
"""One-off generator for radar/registry.json. Kept in-tree so the registry stays
auditable and regenerable. Hand-edits to registry.json are fine; re-running this
overwrites them, so port them back here."""
import json, collections

S = []
def add(sid, name, url, tier, country, cat, method, cadence, lead, why,
        segments=("city","bush","beach"), slots=("morning","midday","evening"), frag=""):
    S.append(dict(id=sid, name=name, url=url, tier=tier, country=country,
                  category=cat, method=method, cadence_min=cadence, lead_days=lead,
                  segments=list(segments), slots=list(slots), why=why, frag=frag))

A = ("morning",); M = ("midday",); E = ("evening",); ALL = ("morning","midday","evening")

# ---------------------------------------------------------------- KENYA
add("ke-gazette","Kenya Gazette (Kenya Law)","https://new.kenyalaw.org/gazettes/",1,"KE","gazette","html",180,10,
    "Fee changes, licensing and policy legally originate here, with effective dates the press omits.",slots=A)
add("ke-gazettes-africa","Kenya Gazette mirror (gazettes.africa)","https://gazettes.africa/gazettes/ke",1,"KE","gazette","html",240,10,
    "Second read on the gazette; often indexed faster than the official portal.",slots=A)
add("ke-epra-press","EPRA press releases","https://www.epra.go.ke/media-center/press-releases/",1,"KE","regulator","html",180,2,
    "Monthly fuel price review lands here ~14th, effective 15th. Moves transfer, generator and laundry costs.",slots=A)
add("ke-epra-fuel","EPRA maximum retail petroleum prices","https://www.epra.go.ke/services/economic-regulation/petroleum/maximum-retail-petroleum-prices/",1,"KE","regulator","html",180,2,
    "The actual price table. Diarised, knowable date — be first to price the impact.",slots=A)
add("ke-knbs-releases","KNBS statistical releases","https://www.knbs.or.ke/statistical-releases/",1,"KE","statistics","html",120,2,
    "CPI, Leading Economic Indicators incl. arrivals and hotel bed-nights.",slots=A)
add("ke-knbs-calendar","KNBS advance release calendar","https://www.knbs.or.ke/release-calendar/",1,"KE","statistics","html",1440,30,
    "Tells you what lands when. Feed for calendar.js.",slots=A)
add("ke-cbk-press","Central Bank of Kenya press releases","https://www.centralbank.go.ke/press/",1,"KE","central-bank","html",180,2,
    "Rate decisions and FX. The cost-side input for anyone carrying refurbishment debt.",slots=A)
add("ke-cbk-bulletin","CBK weekly bulletin","https://www.centralbank.go.ke/weekly-bulletin/",1,"KE","central-bank","html",1440,3,
    "Fridays. FX cross-rates and reserves.",slots=A)
add("ke-tri","Tourism Research Institute","https://tri.go.ke/",1,"KE","statistics","html",360,5,
    "Authoritative Kenyan arrivals by source market — the number to quote.",slots=A)
add("ke-tourism-ministry","Ministry of Tourism & Wildlife","https://www.tourism.go.ke/",1,"KE","ministry","html",240,3,
    "Policy, levies and ministerial directives.",slots=ALL)
add("ke-ktb-news","Kenya Tourism Board news","https://ktb.go.ke/news",1,"KE","dmo","html",240,3,
    "Destination marketing pushes and source-market campaigns.",slots=ALL)
add("ke-kws","Kenya Wildlife Service","https://www.kws.go.ke/",1,"KE","parks","html",240,7,
    "Park fees, closures and conservancy rules — direct lodge cost and access impact.",segments=("bush",),slots=E)
add("ke-tra","Tourism Regulatory Authority","https://www.tourismauthority.go.ke/",1,"KE","regulator","html",360,7,
    "Licensing and classification of accommodation.",slots=E)
add("ke-tourism-fund","Tourism Fund","https://www.tourismfund.co.ke/",1,"KE","regulator","html",720,7,
    "Tourism levy administration — a direct line item on every guest bill.",slots=E)
add("ke-kcaa","KCAA — aeronautical information & circulars","https://kcaa.or.ke/",1,"KE","aviation","html",180,5,
    "AICs create passenger document requirements before any airline tells an agent.",slots=M)
add("ke-kaa","Kenya Airports Authority","https://www.kaa.go.ke/",1,"KE","aviation","html",240,4,
    "Terminal capacity, disruption notices and traffic statistics.",slots=M)
add("ke-kaa-tenders","KAA tenders","https://www.kaa.go.ke/corporate/tenders/",1,"KE","tender","html",720,30,
    "Airport works signal capacity and disruption years ahead.",slots=E)
add("ke-moh","Kenya Ministry of Health","https://www.health.go.ke/",1,"KE","health","html",120,2,
    "Screening measures and outbreak statements that precede advisory changes.",slots=ALL)
add("ke-eta","Kenya eTA portal","https://www.etakenya.go.ke/",1,"KE","entry-rules","html",360,7,
    "Entry requirement and fee changes appear on the portal before they are reported.",slots=A)
add("ke-treasury","National Treasury Kenya","https://www.treasury.go.ke/",1,"KE","fiscal","html",720,21,
    "Budget documents carry tourism levies and aviation taxes months before they bite.",slots=E)
add("ke-parliament","Parliament of Kenya — bills & papers","http://www.parliament.go.ke/",1,"KE","legislature","html",720,30,
    "Finance Bills and committee reports — the earliest sight of a tax change.",slots=E)
add("ke-tenders","Kenya PPIP tender portal","https://tenders.go.ke/",1,"KE","tender","html",720,30,
    "Tourism and access infrastructure awards.",slots=E)
add("ke-nse","Nairobi Securities Exchange announcements","https://www.nse.co.ke/listed-company-announcements/",1,"KE","capital","html",360,3,
    "Results and disclosures from listed hospitality and aviation names.",slots=ALL)
add("ke-met","Kenya Meteorological Department","https://meteo.go.ke/",1,"KE","weather","html",240,2,
    "Flood and severe-weather warnings that close roads and airstrips.",slots=ALL)

# ---------------------------------------------------------------- UGANDA
add("ug-gazette","Uganda Gazette (gazettes.africa)","https://gazettes.africa/gazettes/ug",1,"UG","gazette","html",240,10,
    "Statutory instruments incl. park and licensing fees.",slots=A)
add("ug-ubos","UBOS statistical releases","https://www.ubos.org/",1,"UG","statistics","html",180,2,
    "CPI and the shilling-strength story that squeezes USD-earning operators.",slots=A)
add("ug-bou","Bank of Uganda","https://www.bou.or.ug/",1,"UG","central-bank","html",360,3,
    "MPC and FX. UGX strength is a live margin issue.",slots=A)
add("ug-utb","Uganda Tourism Board","https://utb.go.ug/",1,"UG","dmo","html",240,3,
    "POATE, campaigns and destination policy.",slots=ALL)
add("ug-uwa","Uganda Wildlife Authority updates","https://ugandawildlife.org/new_categories/updates/",1,"UG","parks","html",180,7,
    "Gorilla permit pricing, allocation rules and park entry waivers.",segments=("bush",),slots=E)
add("ug-ucaa","Uganda Civil Aviation Authority","https://www.caa.co.ug/",1,"UG","aviation","html",240,5,
    "Entebbe terminal capacity and aeronautical notices.",slots=M)
add("ug-moh","Uganda Ministry of Health","https://www.health.go.ug/",1,"UG","health","html",120,1,
    "Ebola situation reports and the 42-day countdown status, direct from source.",slots=ALL)
add("ug-tourism-ministry","Ministry of Tourism, Wildlife & Antiquities","https://www.tourism.go.ug/",1,"UG","ministry","html",360,5,
    "Policy and the ten-year tourism growth strategy.",slots=ALL)
add("ug-ura","Uganda Revenue Authority","https://www.ura.go.ug/",1,"UG","fiscal","html",720,14,
    "VAT and tourism tax changes.",slots=E)
add("ug-parliament","Parliament of Uganda","https://www.parliament.go.ug/",1,"UG","legislature","html",720,30,
    "Budget and tax proposals affecting accommodation.",slots=E)
add("ug-tenders","Uganda EGP portal","https://egpuganda.go.ug/",1,"UG","tender","html",1440,30,
    "Airport, road and park infrastructure awards.",slots=E)

# ---------------------------------------------------------------- TANZANIA
add("tz-gazette","Tanzania Government Gazette (gazettes.africa)","https://gazettes.africa/gazettes/tz",1,"TZ","gazette","html",240,10,
    "Fee schedules and statutory instruments.",slots=A)
add("tz-nbs","NBS Tanzania statistics","https://www.nbs.go.tz/",1,"TZ","statistics","html",180,2,
    "CPI plus arrivals and tourism earnings. Tanzania's benign cost base is a competitive asset.",slots=A)
add("tz-bot","Bank of Tanzania","https://www.bot.go.tz/",1,"TZ","central-bank","html",360,3,
    "Monthly economic review carries travel receipts.",slots=A)
add("tz-mnrt","Ministry of Natural Resources & Tourism","https://www.maliasili.go.tz/",1,"TZ","ministry","html",240,5,
    "Park fee orders, concession rules and tourism policy.",segments=("bush",),slots=ALL)
add("tz-tanapa","TANAPA","https://www.tanzaniaparks.go.tz/",1,"TZ","parks","html",240,7,
    "Park entry fees and access rules — the biggest single line in a northern-circuit quote.",segments=("bush",),slots=E)
add("tz-ncaa","Ngorongoro Conservation Area Authority","https://www.ncaa.go.tz/",1,"TZ","parks","html",360,7,
    "Crater fees and vehicle rules.",segments=("bush",),slots=E)
add("tz-ttb","Tanzania Tourist Board","https://www.tanzaniatourism.go.tz/",1,"TZ","dmo","html",360,4,
    "Campaigns and arrivals commentary.",slots=ALL)
add("tz-tcaa","Tanzania Civil Aviation Authority","https://www.tcaa.go.tz/",1,"TZ","aviation","html",240,5,
    "Route approvals and aeronautical notices.",slots=M)
add("tz-taa","Tanzania Airports Authority","https://www.taa.go.tz/",1,"TZ","aviation","html",360,5,
    "Kilimanjaro and Dar terminal capacity, traffic data.",slots=M)
add("tz-moh","Tanzania Ministry of Health","https://www.moh.go.tz/",1,"TZ","health","pdf",120,2,
    "Publishes numbered travel advisories as PDFs — pure upstream, rarely reported.",slots=ALL)
add("tz-immigration","Tanzania Immigration Services","https://www.immigration.go.tz/",1,"TZ","entry-rules","html",360,7,
    "Visa and entry rule changes.",slots=A)
add("tz-tra","Tanzania Revenue Authority","https://www.tra.go.tz/",1,"TZ","fiscal","html",720,14,
    "Tourism VAT and levy administration.",slots=E)
add("tz-tenders","Tanzania NeST procurement portal","https://nest.go.tz/",1,"TZ","tender","html",1440,30,
    "Park, airport and road works.",slots=E)

# ---------------------------------------------------------------- ZANZIBAR
add("zn-ocgs","OCGS Zanzibar statistics","https://www.ocgs.go.tz/",1,"ZNZ","statistics","html",180,3,
    "Monthly arrivals with source-market split — the granular number nobody else quotes on time.",segments=("beach",),slots=A)
add("zn-tourism","Zanzibar Commission for Tourism","https://www.zanzibartourism.go.tz/",1,"ZNZ","dmo","html",240,4,
    "Arrivals releases, licensing and levy notices.",segments=("beach",),slots=ALL)
add("zn-zrb","Zanzibar Revenue Board","https://www.zrb.go.tz/",1,"ZNZ","fiscal","html",360,10,
    "Infrastructure levy and hotel tax changes — a direct per-guest cost.",segments=("beach",),slots=E)
add("zn-zaa","Zanzibar Airports Authority","https://www.zaa.go.tz/",1,"ZNZ","aviation","html",360,5,
    "AAKIA terminal capacity and charter handling.",segments=("beach",),slots=M)
add("zn-moh","Zanzibar Ministry of Health","https://www.mohz.go.tz/",1,"ZNZ","health","html",180,2,
    "Island health notices; cholera and outbreak statements move European charters.",segments=("beach",),slots=ALL)

# ---------------------------------------------------------------- RWANDA
add("rw-gazette","Rwanda Official Gazette (gazettes.africa)","https://gazettes.africa/gazettes/rw",1,"RW","gazette","html",240,10,
    "Ministerial orders incl. permit and park pricing.",slots=A)
add("rw-nisr","NISR publications","https://statistics.gov.rw/statistical-publications",1,"RW","statistics","html",180,2,
    "CPI and tourism statistics; Rwanda's source-market mix is shifting fast.",slots=A)
add("rw-bnr","National Bank of Rwanda","https://www.bnr.rw/",1,"RW","central-bank","html",360,3,
    "FX and rate decisions.",slots=A)
add("rw-rdb","Rwanda Development Board media","https://rdb.rw/media/",1,"RW","regulator","html",180,5,
    "Primary source for gorilla permit policy, arrivals and MICE wins.",slots=ALL)
add("rw-visitrwanda","Visit Rwanda news","https://www.visitrwanda.com/",1,"RW","dmo","html",360,4,
    "Destination campaigns and product launches.",slots=ALL)
add("rw-rca","Rwanda Civil Aviation Authority","https://www.rca.gov.rw/",1,"RW","aviation","html",360,5,
    "Route approvals and aeronautical notices.",slots=M)
add("rw-moh","Rwanda Ministry of Health","https://www.moh.gov.rw/",1,"RW","health","html",120,2,
    "Entry screening and DRC-border health measures — Rwanda moves first and hardest.",slots=ALL)
add("rw-rra","Rwanda Revenue Authority","https://www.rra.gov.rw/",1,"RW","fiscal","html",720,14,
    "Tourism VAT and levy changes.",slots=E)
add("rw-rppa","Rwanda public procurement (RPPA)","https://www.rppa.gov.rw/",1,"RW","tender","html",1440,30,
    "Conference, airport and park infrastructure awards.",slots=E)

# ---------------------------------------------------------------- HEALTH / MULTILATERAL
add("who-afro-outbreaks","WHO AFRO outbreaks & emergencies","https://www.afro.who.int/health-topics/disease-outbreaks/outbreaks-and-other-emergencies-updates",1,"REG","health","html",120,4,
    "Weekly bulletins carry case counts, districts and countdown status days before the press.",slots=ALL)
add("who-don","WHO Disease Outbreak News","https://www.who.int/emergencies/disease-outbreak-news",1,"GLOBAL","health","html",120,3,
    "Formal event notifications — the trigger for advisory changes.",slots=ALL)
add("africacdc-outbreaks","Africa CDC outbreak briefs","https://africacdc.org/disease-outbreak/",1,"REG","health","html",120,4,
    "Situation reports numbered by issue; continental view catches spillover early.",slots=ALL)
add("africacdc-downloads","Africa CDC downloads (sit reps & EIW)","https://africacdc.org/download-category/situation-report/",1,"REG","health","html",180,4,
    "Where the numbered Bundibugyo situation reports actually land as PDFs.",slots=ALL)
add("reliefweb-ea","ReliefWeb — East Africa updates","https://reliefweb.int/updates/rss.xml?view=headlines",2,"REG","health","rss",120,1,
    "Aggregates ministry and WHO reporting, often hours ahead of anyone else.",slots=ALL)
add("cdc-travel-notices","US CDC travel health notices","https://wwwnc.cdc.gov/travel/notices",1,"GLOBAL","health","html",180,2,
    "A CDC notice reshapes US booking behaviour independently of State Department levels.",slots=ALL)
add("ecdc-cdtr","ECDC weekly communicable disease threats report","https://www.ecdc.europa.eu/en/threats-and-outbreaks",1,"GLOBAL","health","html",360,3,
    "European view — drives German, Italian and Polish charter sentiment to Zanzibar.",slots=ALL)
add("promed","ProMED-mail","https://promedmail.org/",2,"GLOBAL","health","html",180,2,
    "Earliest informal signal on outbreaks, ahead of official confirmation.",slots=ALL)

# ---------------------------------------------------------------- TRAVEL ADVISORIES
for cc, slug, nm in [("KE","kenya","Kenya"),("UG","uganda","Uganda"),("TZ","tanzania","Tanzania"),("RW","rwanda","Rwanda")]:
    add(f"adv-us-{slug}", f"US State Dept advisory — {nm}",
        f"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/{slug}-travel-advisory.html",
        1,cc,"advisory","html",60,1,
        "Read the page, not news about it: level, exact geography, stated grounds.",slots=ALL)
    add(f"adv-uk-{slug}", f"UK FCDO advice — {nm}",
        f"https://www.gov.uk/foreign-travel-advice/{slug}",1,cc,"advisory","html",60,1,
        "FCDO wording drives UK operator insurance and tour-operator policy.",slots=ALL)
for cc, slug, nm in [("KE","kenya","Kenya"),("TZ","tanzania","Tanzania")]:
    add(f"adv-ca-{slug}", f"Canada travel advice — {nm}",
        f"https://travel.gc.ca/destinations/{slug}",1,cc,"advisory","html",180,1,
        "Divergence between governments is a commercial asset, not an inconsistency.",slots=ALL)
    add(f"adv-au-{slug}", f"Smartraveller — {nm}",
        f"https://www.smartraveller.gov.au/destinations/africa/{slug}",1,cc,"advisory","html",180,1,
        "Australian long-haul safari demand tracks this closely.",slots=ALL)
    add(f"adv-de-{slug}", f"Auswärtiges Amt — {nm}",
        f"https://www.auswaertiges-amt.de/de/service/laender/{slug}-node/{slug}sicherheit",1,cc,"advisory","html",180,1,
        "Germany is a top-three source market for Zanzibar and the northern circuit.",slots=ALL)
    add(f"adv-fr-{slug}", f"France Conseils aux voyageurs — {nm}",
        f"https://www.diplomatie.gouv.fr/fr/conseils-aux-voyageurs/conseils-par-pays-destination/{slug}/",1,cc,"advisory","html",180,1,
        "French advisories move Indian Ocean beach demand.",slots=ALL)

# ---------------------------------------------------------------- AVIATION
add("air-kq","Kenya Airways newsroom","https://corporate.kenya-airways.com/en/news-press-release/",1,"KE","airline","html",180,3,
    "Route, fleet and capacity announcements from the regional hub carrier.",slots=M)
add("air-ug","Uganda Airlines news","https://www.ugandairlines.com/news",1,"UG","airline","html",240,3,
    "Entebbe network build-out; capacity is a leading indicator of arrivals.",slots=M)
add("air-wb","RwandAir media centre","https://www.rwandair.com/media-center/",1,"RW","airline","html",240,3,
    "Kigali hub strategy and schedule shifts.",slots=M)
add("air-tc","Air Tanzania","https://www.airtanzania.co.tz/",1,"TZ","airline","html",240,3,
    "Long-haul experiments and domestic capacity to the northern circuit.",slots=M)
add("air-jambojet","Jambojet media","https://www.jambojet.com/en/press-release",1,"KE","airline","html",360,3,
    "Low-cost capacity into coastal and regional leisure markets.",slots=M)
add("air-precision","Precision Air","https://www.precisionairtz.com/",1,"TZ","airline","html",360,3,
    "Northern circuit and Zanzibar feeder capacity.",slots=M)
add("air-et","Ethiopian Airlines press room","https://www.ethiopianairlines.com/aa/media/press-room",1,"REG","airline","html",360,3,
    "The dominant African feeder; its schedule sets regional connectivity.",slots=M)
add("air-ek","Emirates media centre","https://www.emirates.com/media-centre/",1,"GLOBAL","airline","html",360,3,
    "Gulf capacity into Nairobi and Zanzibar drives long-haul leisure volume.",slots=M)
add("air-qr","Qatar Airways press releases","https://www.qatarairways.com/en/press-releases.html",1,"GLOBAL","airline","html",360,3,
    "Doha capacity into Kilimanjaro, Zanzibar, Entebbe and Kigali.",slots=M)
add("air-tk","Turkish Airlines press room","https://www.turkishairlines.com/en-int/press-room/",1,"GLOBAL","airline","html",360,3,
    "Istanbul feeds European and Asian secondary markets into EA.",slots=M)
add("air-klm","KLM/Air France newsroom","https://news.klm.com/",1,"GLOBAL","airline","html",360,3,
    "Amsterdam and Paris capacity — core to Dutch, French and Scandinavian safari demand.",slots=M)
add("air-lh","Lufthansa Group newsroom","https://newsroom.lufthansagroup.com/en/",1,"GLOBAL","airline","html",720,3,
    "Discover Airlines charter-style capacity into Zanzibar and Mombasa.",segments=("beach",),slots=M)
add("air-airlink","Airlink news","https://www.flyairlink.com/",1,"REG","airline","html",720,3,
    "Southern Africa linkage for combined safari itineraries.",slots=M)
add("aeroroutes","AeroRoutes schedule filings","https://www.aeroroutes.com/",2,"GLOBAL","aviation-tracker","html",180,7,
    "Schedule filings appear here days to months before airlines publicise them.",slots=M)
add("chaviation","ch-aviation news","https://www.ch-aviation.com/news",2,"GLOBAL","aviation-tracker","html",240,5,
    "Fleet, AOC and route filings — the earliest sight of a new entrant or a collapse.",slots=M)
add("iata-pressroom","IATA pressroom","https://www.iata.org/en/pressroom/",1,"GLOBAL","aviation-body","html",720,2,
    "Monthly air passenger analysis incl. Africa — leading indicator for arrivals.",slots=M)

# ---------------------------------------------------------------- CAPITAL / DEVELOPMENT
add("dev-marriott","Marriott news centre","https://news.marriott.com/",1,"GLOBAL","hotel-group","html",720,14,
    "Signings and openings reshape competitive supply years ahead.",slots=M)
add("dev-accor","Accor press","https://press.accor.com/",1,"GLOBAL","hotel-group","html",720,14,
    "Strong African pipeline; watch conversions and soft brands.",slots=M)
add("dev-hilton","Hilton stories/newsroom","https://stories.hilton.com/releases",1,"GLOBAL","hotel-group","html",720,14,
    "Nairobi, Kampala and Kigali pipeline activity.",slots=M)
add("dev-radisson","Radisson Hotel Group media","https://www.radissonhotels.com/en-us/corporate/media",1,"GLOBAL","hotel-group","html",720,14,
    "The most aggressive African signer of recent years.",slots=M)
add("dev-ihg","IHG news","https://www.ihgplc.com/en/news-and-media",1,"GLOBAL","hotel-group","html",1440,14,
    "Pipeline and brand entries into EA cities.",slots=M)
add("dev-minor","Minor Hotels newsroom","https://www.minorhotels.com/en/newsroom",1,"GLOBAL","hotel-group","html",1440,14,
    "Anantara and NH expansion into Indian Ocean beach markets.",segments=("beach",),slots=M)
add("dev-kempinski","Kempinski press","https://www.kempinski.com/en/press-releases",1,"GLOBAL","hotel-group","html",1440,14,
    "Luxury city and resort positioning in Nairobi and Zanzibar.",slots=M)
add("dev-whospitality","W Hospitality Group pipeline reports","https://w-hospitalitygroup.com/blog/",2,"REG","research","html",1440,21,
    "The annual Africa pipeline report is the supply-side reference everyone quotes.",slots=E)
add("dev-hospitalitynet-africa","Hospitality Net — Africa announcements","https://www.hospitalitynet.org/africa/announcements",2,"REG","trade","html",360,3,
    "Openings and appointments across the continent.",slots=M)
add("dev-costar","CoStar / STR hospitality news","https://www.costar.com/news",2,"GLOBAL","research","html",720,5,
    "Occupancy and ADR benchmarking commentary for African markets.",slots=E)
add("dev-jll-hotels","JLL Hotels & Hospitality research","https://www.jll.com/en-us/insights",2,"GLOBAL","research","html",1440,21,
    "Transaction and investment flow into African hospitality.",slots=E)
add("dev-aleph","Aleph Hospitality news","https://alephhospitality.com/news/",2,"REG","hotel-group","html",1440,14,
    "Africa-focused third-party operator; signs the mid-market and Kigali/Nairobi deals the global chains skip.",slots=M)
add("dev-tophotel","TOPHOTELNEWS development pipeline","https://tophotel.news/category/construction-and-development/",2,"GLOBAL","trade","html",720,7,
    "Development-desk trade press; often carries a signing before the operator's own newsroom does.",slots=M)
add("dev-choice","Choice Hotels newsroom","https://media.choicehotels.com/",2,"GLOBAL","hotel-group","html",1440,14,
    "Entered Africa in 2026 with three Kenyan franchises including a soft-brand inside the Mara.",slots=M)
add("dev-luxcollective","The Lux Collective press","https://theluxcollective.com/press/",3,"REG","hotel-group","html",2880,21,
    "Running Rwanda's five-property ultra-luxury circuit; a bellwether for premium bush supply.",slots=E)

# ---------------------------------------------------------------- TRADE & REGIONAL PRESS
add("np-businessdaily","Business Daily Africa","https://www.businessdailyafrica.com/",2,"KE","press","html",60,0,
    "Kenya's business paper of record for hospitality and aviation.",slots=ALL)
add("np-eastafrican","The EastAfrican","https://www.theeastafrican.co.ke/",2,"REG","press","html",60,0,
    "Regional view across all five markets.",slots=ALL)
add("np-citizen-tz","The Citizen (Tanzania)","https://www.thecitizen.co.tz/",2,"TZ","press","html",60,0,
    "Tanzanian policy and tourism reporting.",slots=ALL)
add("np-dailynews-tz","Daily News (Tanzania)","https://dailynews.co.tz/",2,"TZ","press","html",120,0,
    "Carries government statistics releases early, incl. Zanzibar arrivals.",slots=ALL)
add("np-monitor-ug","Daily Monitor (Uganda)","https://www.monitor.co.ug/",2,"UG","press","html",60,0,
    "Ugandan tourism, health and aviation reporting.",slots=ALL)
add("np-newvision-ug","New Vision (Uganda)","https://www.newvision.co.ug/",2,"UG","press","html",120,0,
    "State-adjacent paper; often first with ministry announcements.",slots=ALL)
add("np-newtimes-rw","The New Times (Rwanda)","https://www.newtimes.co.rw/",2,"RW","press","html",60,0,
    "Rwandan policy, MICE and permit news.",slots=ALL)
add("np-ktpress-rw","KT Press (Rwanda)","https://www.ktpress.rw/",2,"RW","press","html",180,0,
    "Second Rwandan read; useful for cross-checking.",slots=ALL)
add("np-theexchange","The Exchange Africa — hospitality","https://theexchange.africa/hospitality/",2,"REG","trade","html",240,1,
    "Regional business coverage of hospitality investment.",slots=ALL)
add("tp-voyagesafriq","VoyagesAfriq","https://voyagesafriq.com/",2,"REG","trade","html",180,1,
    "African travel trade publication of record.",slots=ALL)
add("tp-tourismupdate","Tourism Update (Southern & East Africa)","https://www.tourismupdate.com/",2,"REG","trade","html",180,1,
    "Trade-facing distribution and operator news.",slots=ALL)
add("tp-hotelonline","HotelOnline Africa","https://www.hotelonline.co/",2,"REG","trade","html",360,1,
    "African hotel distribution and technology economics.",slots=ALL)
add("tp-skift","Skift","https://skift.com/feed/",2,"GLOBAL","trade","rss",120,1,
    "Distribution economics and global demand structure.",slots=ALL)
add("tp-travelnews-africa","travelnews.africa","https://travelnews.africa/",2,"REG","trade","html",240,1,
    "Route and trade news across African aviation.",slots=M)
add("tp-atqnews","ATQ News","https://atqnews.com/",3,"REG","trade","html",360,0,
    "Aggregator — use only as a lead to chase to a primary source.",slots=ALL)
add("tp-tanzaniainvest","TanzaniaInvest — tourism","https://www.tanzaniainvest.com/tourism",2,"TZ","trade","html",240,1,
    "Reliably fast with NBS and OCGS statistics releases.",slots=ALL)
add("tp-kata","Kenya Association of Travel Agents news","https://katakenya.org/news/",2,"KE","trade","html",180,2,
    "Trade-side signals; occasionally genuinely exclusive on route plans.",slots=ALL)
add("tp-eturbonews","eTurboNews Africa","https://eturbonews.com/category/africa/",3,"GLOBAL","trade","html",720,0,
    "Republisher — chase to primary before use.",slots=ALL)

# ---------------------------------------------------------------- SOURCE MARKETS / DEMAND
add("sm-unwto","UN Tourism news & barometer","https://www.unwto.org/newsroom",1,"GLOBAL","body","html",720,3,
    "Global context and long-haul source-market outlook.",slots=E)
add("sm-wttc","WTTC news","https://wttc.org/news",1,"GLOBAL","body","html",720,3,
    "Economic Impact Research releases — verify the page date, aggregators misreport it.",slots=E)
add("sm-abta","ABTA (UK) news","https://www.abta.com/news",2,"GLOBAL","source-market","html",1440,3,
    "UK outbound operator sentiment and insolvency notices.",slots=E)
add("sm-tui","TUI Group press","https://www.tuigroup.com/en-en/media",1,"GLOBAL","source-market","html",1440,7,
    "Charter programme decisions move Zanzibar and Mombasa beach volume wholesale.",segments=("beach",),slots=E)
add("sm-derreise","FVW / German travel trade","https://www.fvw.de/",2,"GLOBAL","source-market","html",1440,3,
    "German market — top-three for Zanzibar and the northern circuit.",segments=("beach","bush"),slots=E)
add("sm-forwardkeys","ForwardKeys insights","https://forwardkeys.com/newsroom/",2,"GLOBAL","source-market","html",1440,7,
    "Forward booking data — the closest public proxy for pace.",slots=E)

reg = {"version": 1, "updated": "2026-07-28",
       "note": "Upstream-weighted source registry for the EA Hospitality Pulse radar. "
               "tier 1 = primary/official, 2 = reputable secondary, 3 = weak (lead only, never publishable alone). "
               "lead_days = typical head start over mainstream coverage. "
               "Sources that fail repeatedly are surfaced by monitor.py rather than silently dropped.",
       "sources": S}

ids = [s["id"] for s in S]
dupes = [k for k,v in collections.Counter(ids).items() if v > 1]
assert not dupes, f"duplicate ids: {dupes}"
print(json.dumps(reg, indent=1)[:1] and "")

# ---------------------------------------------------------------- RESTORED HAND-ADDS
# Added directly to registry.json during live coverage (Ebola / US advisory work) and
# ported back here so a regeneration never silently drops them again.
add("adv-us-ea","US State Dept travel advisories (EA feed)","https://travel.state.gov/_res/rss/TAsTWs.xml",1,"REG","advisory","rss",120,1,
    "Official RSS of all US advisories — read Kenya/Uganda/Tanzania/Rwanda levels and divergence straight from the feed.",slots=ALL)
add("us-cdc-evdorder","CDC port health — s.362 Ebola entry orders","https://www.cdc.gov/port-health/legal-authorities/evdorder.html",1,"REG","advisory","html",180,14,
    "The signed 30-day entry-suspension orders land here before trade press notices. Each carries a hard expiry date and a comment deadline.",segments=('city', 'bush'),slots=E)
add("us-fedreg-cdc","Federal Register — CDC notices","https://www.federalregister.gov/agencies/centers-for-disease-control-and-prevention",1,"REG","advisory","html",180,10,
    "Docket numbers, comment windows and the response-to-comments section that reveals which arguments the US has already rejected.",segments=('city', 'bush'),slots=E)
add("ug-evd-dashboard","Uganda MoH EVD daily dashboard","https://evd-daily.health.go.ug/",1,"UG","health","html",120,1,
    "Official daily case, admission, contact-tracing and point-of-entry screening counts — updated before WHO and press.",segments=('city', 'bush'),slots=ALL)
add("ug-mediacentre","Uganda Media Centre — press room","https://mediacentre.go.ug/press-room/",1,"UG","gov-comms","html",120,1,
    "Where Uganda government declarations land first — the 28 Jul 2026 Ebola end-of-outbreak declaration was published here before wire pickup. Note: page is client-rendered, so treat as page-change granularity.",segments=('city', 'bush'),slots=ALL)
add("ug-moh-news","Uganda Ministry of Health — news","https://health.go.ug/",1,"UG","health","html",120,1,
    "Primary source for Ugandan outbreak status, entry-screening changes and end-of-outbreak declarations.",segments=('city', 'bush'),slots=ALL)
add("ecdc-ebola","ECDC — DRC/Uganda Ebola outbreak page","https://www.ecdc.europa.eu/en/ebola-outbreak-democratic-republic-congo-and-uganda",1,"GLOBAL","health","html",180,2,
    "Keeps a running confirmed-case and death count for the DRC/Uganda outbreak — the number European source markets and insurers cite.",segments=('city', 'bush'),slots=('morning', 'evening'))
add("ke-usembassy-alerts","US Embassy Nairobi — alerts & messages","https://ke.usembassy.gov/category/alert/",1,"KE","advisory","html",120,2,
    "Demonstration and security alerts for US citizens post here first — ahead of any revision to the rendered travel.state.gov page, as the 29 Jul 2026 Kenya advisory re-issue showed.",slots=ALL)
add("osac-kenya","OSAC — Kenya reports & advisory notices","https://www.osac.gov/Country/Kenya/Content",1,"KE","advisory","html",360,3,
    "OSAC republishes State advisory changes with the operative wording| useful for confirming exactly what moved when travel.state.gov lags its own feed.",slots=M)

import os
_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.json")
with open(_OUT, "w") as f:
    json.dump(reg, f, indent=1)

by_tier = collections.Counter(s["tier"] for s in S)
by_country = collections.Counter(s["country"] for s in S)
by_method = collections.Counter(s["method"] for s in S)
by_cat = collections.Counter(s["category"] for s in S)
print(f"TOTAL SOURCES: {len(S)}")
print("tier:", dict(sorted(by_tier.items())))
print("country:", dict(by_country.most_common()))
print("method:", dict(by_method.most_common()))
print("category:", dict(by_cat.most_common()))
