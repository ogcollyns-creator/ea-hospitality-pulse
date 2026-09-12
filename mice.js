// EA Pulse MICE Events Tracker.
// Confirmed conferences, congresses, expos and awards ceremonies across the five
// markets — the compression events that move a city's or island's room stock for
// several nights at a time. Maintained by the daily Pulse task (see SKILL.md Step 8):
// updated when an event is confirmed, moved, cancelled, or a bid is won/lost.
//
// HONEST SCOPE: this is not an exhaustive events calendar. It carries events we have
// individually verified against an official host, convention bureau or organiser
// source — mostly hospitality, tourism and business-events trade. Delegate counts are
// only included where a named source states one; we do not estimate or invent them.
window.MICE = {
 updated: "12 September 2026 (evening \u2014 no event confirmed| moved| cancelled or bid resolved today. MICE scan run: convention bureaux| KICC| Kigali| JNICC Dar| Speke Munyonyo and ICCA/AU/EAC calendars produced no new dated confirmation. Standing watch: the 8 October Tatler Best of Africa date remains UNCONFIRMED against KTB or Tatler. NEW OPERATIONAL NOTE for Nairobi city venues: police have barred large political rallies from the CBD from 12 September 2026 (Nairobi Regional Security Committee| via The Star 12 Sep)| with a procession routed All Saints Cathedral to Jacaranda Grounds on Sunday 13 September \u2014 CBD-cluster event organisers should confirm access arrangements with venues rather than assume normal Sunday movement.)",
 events: [
  { event:"Tatler Best of Africa (inaugural)", city:"Nairobi", country:"Kenya", flag:"\ud83c\uddf0\ud83c\uddea",
    dates:"Reported for 8 October 2026 \u2014 DATE UNCONFIRMED", status:"Announced", delegates:null,
    detail:"Kenya Tourism Board has signed a THREE-YEAR SUBVENTION AGREEMENT with Tatler Africa to bring the inaugural Tatler Best of Africa event to Kenya and to host the Tatler Africa office on the continent| framed inside a stated KSh 1 trillion tourism-GDP target (ATQ News| 9 September 2026). Several trade aggregators carry 8 October 2026 in Nairobi as the awards date| but we have NOT matched that date to a KTB or Tatler Group source| so it is logged as reported-not-confirmed. No delegate count published and none estimated.",
    soWhat:"An awards night is a one- or two-night top-end city compression event| not a congress \u2014 but the strategic point outweighs the room nights. A national tourism board is now subsidising the platform that will shape which African properties get international luxury shelf space for three years. Top-end Nairobi| Laikipia and coast properties should ask KTB directly how shortlisting and nomination work| this quarter| rather than waiting to be discovered. Do not block inventory against the 8 October date until it is confirmed by KTB or Tatler.",
    segment:"City, Bush, Beach", source:"ATQ News, 9 September 2026 (KTB\u2013Tatler Africa subvention agreement); date via trade aggregators, unconfirmed", verified:false, flagged:"watch" },

  { event:"Africa MICE Summit 2026 (incl. Africa MICE Awards & MICE Investors Round Table)", city:"Mombasa", country:"Kenya", flag:"\ud83c\uddf0\ud83c\uddea",
    dates:"1\u20132 October 2026", status:"Confirmed", delegates:"600+ attendees| 25+ speakers| 50+ exhibitors (organiser figures| africamicesummit.org)",
    detail:"NOTE THE MOVE. The 2025 edition ran 9\u201311 September in NAIROBI; the 2026 edition is 1\u20132 October in MOMBASA \u2014 anyone still holding the Nairobi September dates is holding last year\u2019s diary. Theme: \u2018Building Africa\u2019s Business Events Ecosystem for Trade| Investment and Innovation\u2019. Africa MICE Awards gala 2 October| 60+ categories. A MICE Investors & Stakeholders Round Table runs the same day| pitching convention-centre and exhibition-venue projects to investors and DFIs under an AfCFTA framing. Organised by Zuri Events. The 600+ figure is the organiser\u2019s own attendance claim and covers the summit| not a verified registration count.",
    soWhat:"Two nights| Mombasa| in the same week Kenya\u2019s autumn conference calendar opens \u2014 and Mombasa is the county carrying Kenya\u2019s heaviest dengue and mpox burden (3|989 dengue cases Jan\u2013May; 452 mpox cases). Coast properties should hold rate 30 Sep\u20132 Oct rather than discounting into the shoulder| AND have the daytime vector protocol visibly in place before a room full of Africa\u2019s business-events buyers arrives. This is the single audience most likely to notice. Right-size the block: 600+ is an organiser figure across two days| much of it Mombasa-based trade| so treat it as a venue-cluster event until registrations are published.",
    segment:"City, Beach", source:"africamicesummit.org (organiser site, read 9 September 2026)", verified:true, flagged:"action" },

  { event:"Kenya Transport Summit & Expo 2026", city:"Nairobi (Kenyatta International Convention Centre)", country:"Kenya", flag:"\ud83c\uddf0\ud83c\uddea",
    dates:"30 September \u2013 2 October 2026", status:"Confirmed", delegates:null,
    detail:"Policy-and-industry summit bringing together transport policymakers and sector stakeholders at KICC. No organiser delegate count published \u2014 we do not estimate one. Logged from the Central Bank of Kenya market perceptions survey coverage, which cited it as part of the Aug\u2013Nov Nairobi conference calendar underpinning improved forward hotel bookings.",
    soWhat:"A three-day city-centre event on the Wed\u2013Fri either side of the month end. KICC-cluster properties (CBD, Upper Hill) should hold corporate rate across 30 Sep\u20132 Oct rather than discounting into the shoulder. Right-size it: no delegate figure is published, so treat it as a CBD cluster event, not city-wide compression, until one is.",
    segment:"City", source:"Business Daily Africa, 25 Aug 2026 (CBK Market Perceptions Survey coverage)", verified:true, flagged:"action" },

  { event:"Africa Commerce and Industry Summit 2026", city:"Nairobi (Uhuru Gardens)", country:"Kenya", flag:"\ud83c\uddf0\ud83c\uddea",
    dates:"14\u201316 October 2026", status:"Confirmed", delegates:null,
    detail:"Hosted by the Kenya National Chamber of Commerce and Industry as part of its 60th anniversary. Programme covers investor forums, private deal rooms, government-business sessions and sector tracks in energy, agriculture, technology and manufacturing. No delegate count published.",
    soWhat:"Deal-room formats bring small numbers of high-value, late-booking corporate guests rather than a delegate block. Hold rate on suites and executive floors mid-October and brief sales on the sector tracks; do not close out inventory on an event with no published headcount.",
    segment:"City", source:"Business Daily Africa, 25 Aug 2026", verified:true },

  { event:"Kasneb International Conference for Professionals 2026", city:"Nairobi (The Edge Convention Centre)", country:"Kenya", flag:"\ud83c\uddf0\ud83c\uddea",
    dates:"26\u201330 October 2026", status:"Confirmed", delegates:"More than 500 physical delegates targeted (organiser target| per Business Daily)",
    detail:"Five-day professional-body congress at The Edge Convention Centre. The delegate figure is a stated target for PHYSICAL attendance| not a confirmed registration count \u2014 read it as an intention| and note that professional-body congresses typically run a large virtual tail that does not consume rooms.",
    soWhat:"The most room-relevant of Nairobi\u2019s three autumn events: five nights| a stated physical-attendance target above 500| and a professional audience that books accommodation rather than commuting. Hold rate across 26\u201330 Oct in the venue cluster and price a Sun-arrival package. Verify the registration count before allocating a block against the 500 figure.",
    segment:"City", source:"Business Daily Africa, 25 Aug 2026", verified:true, flagged:"action" },

  { event:"Tusker Lite Mt Rwenzori Marathon 2026", city:"Kasese (Rwenzori foothills)", country:"Uganda", flag:"🇺🇬",
    dates:"22 August 2026", status:"Held", delegates:"Runners from ~45 countries (organiser/govt figure); no single headcount published",
    detail:"Government- and Uganda Tourism Board-backed scenic marathon (42km/35km/10km/5km) positioned as a tourism-and-investment showcase for the Rwenzori region. Organisers and government flagged an accommodation shortfall in Kasese, whose bed stock is thin for the race weekend.",
    soWhat:"A genuine short compression on a small town. Hold rate on remaining Kasese inventory and price overflow into Queen Elizabeth NP lodges and Fort Portal; sell the marathon as a QENP/Kazinga Channel extension, not a one-night stay.",
    segment:"City, Bush", source:"APO Group / ATTA / Africa24, mid-Aug 2026; Uganda Ministry of Tourism, Wildlife & Antiquities post-event statement, 25 Aug 2026", verified:true, flagged:"action" },


  { event:"Miss Tourism East Africa 2026 \u2014 inaugural finals", city:"Kampala (Kampala Serena / Marriott)", country:"Uganda", flag:"\ud83c\uddfa\ud83c\uddec",
    dates:"5\u201312 September 2026", status:"Confirmed", delegates:"~24 contestants (7 countries + Zanzibar at ~3 each; no organiser headcount published)",
    detail:"First edition of the regional pageant, hosted at the Marriott in Kampala. Seven East African nations \u2014 Uganda, Kenya, Tanzania, Rwanda, DRC, Burundi and South Sudan \u2014 plus Zanzibar. Tanzania is sending six rather than the standard three, split three mainland and three Zanzibar.",
    soWhat:"LOGGED AS A NON-EVENT, DELIBERATELY. Roughly two dozen contestants plus chaperones, judges and crew is a single-property group booking, not city compression. Treat it as a house-count question for the host hotel. Kampala properties that lift BAR city-wide on this will hand a week of corporate share to the property next door. Recorded here so the claim can be checked rather than repeated.",
    segment:"City", source:"Daily News TZ / allAfrica, 17 Aug 2026", verified:true },

  { event:"Africa Global PR Week (AGPRW) 2026", city:"Nairobi (M\u00f6venpick Hotel & Residences)", country:"Kenya", flag:"\ud83c\uddf0\ud83c\uddea",
    dates:"26\u201328 August 2026", status:"Confirmed", delegates:"1,000+ expected IN PERSON AND ONLINE (organiser figure)",
    detail:"Kenya Tourism Board confirmed as Lead Destination Partner. KTB co-hosts a Destination Pavilion under the \'Magical Kenya\' brand with curated pre- and post-event packages covering the Great Wildebeest Migration, Nairobi city tours and cultural circuits. Theme: \'Redefining Africa: Africa as a Brand\'. Delegates drawn from 20+ African countries. KTB CEO June Chepkemei framed it as a MICE diversification play; AGPRW Chair is Mary Njoki.",
    soWhat:"READ THE DELEGATE NUMBER CAREFULLY. The organiser\'s 1,000+ covers in-person AND online attendance, and the event sits at a single Westlands venue \u2014 not a city-wide congress. Hold corporate rate on 26\u201328 Aug at properties in the M\u00f6venpick\'s immediate cluster and price the pre/post safari extensions; do not blanket-close Nairobi inventory on a headline figure that includes virtual delegates. Announced 8 Jul 2026, so this is a diary item, not news.",
    segment:"City, Bush", source:"ATTA (8 Jul 2026) / Capital FM / africaprweek.com", verified:true, flagged:"action" },

  { event:"Kwita Izina 2026 \u2014 21st gorilla naming ceremony", city:"Kinigi, Musanze District", country:"Rwanda", flag:"\ud83c\uddf7\ud83c\uddfc",
    dates:"4 September 2026 (Exhibition 28 Aug\u20138 Sep; Smart Green Village ground-breaking 27 Aug)", status:"Held", delegates:null,
    detail:"HELD 4 Sep 2026: RDB confirmed 22 baby mountain gorillas were named at Kinigi (RDB release, 4 September 2026). Originally: 22 baby mountain gorillas to be named by international Namers from conservation, business, sport, entertainment and public service. Total named gorillas expected to reach 460. No official delegate count published \u2014 we do not estimate one.",
    soWhat:"A three-week tail of activity around Musanze from 27 Aug to 8 Sep, not a single night. Volcanoes-area lodges should hold rate across the exhibition window rather than just the 4 Sep ceremony date, and Kigali city hotels should expect inbound/outbound transit either side. Note the date: this is early September, NOT late August \u2014 it does not overlap AfPIF or the WTA gala.",
    segment:"Bush, City", source:"RDB / Taarifa Rwanda (11 Aug 2026) / ATTA (12 Aug 2026)", verified:true, flagged:"action" },
  { event:"15th African Peering & Interconnection Forum (AfPIF 2026)", city:"Kigali (Kigali Marriott Hotel)", country:"Rwanda", flag:"\ud83c\uddf7\ud83c\uddfc",
    dates:"18\u201320 August 2026", status:"Confirmed", delegates:"300\u2013500 (historic range, per af-ix.org)",
    detail:"The African IXP Association (AFIX) holds the 15th annual peering and interconnection forum at the Kigali Marriott, with RICTA. One node in Rwanda\'s RDB MICE revenue target of US$156m for 2026. Kigali has ranked Africa\'s No.2 meetings city for five consecutive years behind Cape Town (2024 ICCA rankings).",
    soWhat:"A 300\u2013500 delegate tech forum fills the Kigali Marriott and its immediate neighbours for three midweek nights (18\u201320 Aug) \u2014 hold corporate rate that week rather than discounting. Right-size it: this fills a cluster of business hotels, not the whole city.",
    segment:"City", source:"af-ix.org / tech.africa, Jul 2026", verified:true, flagged:"action" },

  { event:"The Hotel Expo Kenya 2026", city:"Nairobi (KICC)", country:"Kenya", flag:"🇰🇪",
    dates:"19–21 August 2026", status:"Confirmed", delegates:null,
    detail:"Trade expo for hoteliers, restaurateurs and hospitality professionals at the Kenyatta International Convention Centre — technology, F&B, procurement and design. The 2025 edition drew 100+ exhibitors (organiser figure); no verified 2026 delegate count published.",
    soWhat:"A three-day city-centre trade event lands mid-August, ahead of the September–October peak. Nairobi city hotels near KICC should expect a short exhibitor-and-buyer midweek bump (19–21 Aug) — hold corporate rate through those nights rather than discounting into the shoulder.",
    segment:"City", source:"hotelexpo.africa / realtorkenya.com / cantonfair.net, verified Aug 2026", verified:true, flagged:"action" },

  { event:"World Travel Awards — Africa Gala Ceremony 2026", city:"Zanzibar (Diamonds Bijoux resort)", country:"Zanzibar", flag:"🇹🇿",
    dates:"28 August 2026", status:"Confirmed", delegates:null,
    detail:"First of two WTA events in Tanzania in 2026 — the Grand Final Gala follows in December. Winners announced across hotels, airlines, tour operators and destinations.",
    soWhat:"A single-night gala doesn't fill a city, but it fills THIS resort and its neighbours for the surrounding week — expect a short, sharp compression on Zanzibar's north/east coast in the last week of August. If you're not hosting delegates directly, this is still the week to hold rate rather than discount.",
    segment:"Beach", source:"World Travel Awards / Breaking Travel News", verified:true, flagged:"action" },

  { event:"Magical Kenya Travel Expo (MKTE) 2026 — 16th edition", city:"Nairobi (Uhuru Gardens)", country:"Kenya", flag:"🇰🇪",
    dates:"6–8 October 2026", status:"Confirmed", delegates:"10,000+ (record edition, per Kenya Tourism Board)",
    detail:"Three-day trade expo: 400+ exhibitors, 250+ vetted international buyers, delegates from 40 countries. Largest edition since MKTE's inception.",
    soWhat:"This is the single largest room-night compression event on this tracker. A record 10,000-plus delegate turnout means Nairobi city hotels should be closing out standard rate well ahead of October — and lodges within striking distance of Nairobi should expect a pre/post-expo safari extension bump.",
    segment:"City", source:"The Star / HapaKenya, late July 2026", verified:true, flagged:"action" },

  { event:"Swahili International Tourism Expo (S!TE) 2026", city:"Dar es Salaam (Mlimani City)", country:"Tanzania", flag:"🇹🇿",
    dates:"23–25 October 2026", status:"Confirmed", delegates:null,
    detail:"Tanzania's official tourism trade platform — buyers, exhibitors, sponsors, investors and destination partners, organised by the Tanzania Tourism Board.",
    soWhat:"Lands just over two weeks after MKTE Nairobi — the same October buyer and media circuit is likely working both. If you sell into both Kenya and Tanzania, plan a single October trade push covering both dates rather than two separate campaigns.",
    segment:"City", source:"Tanzania Tourism Board (site.tanzaniatourism.go.tz)", verified:true },

  { event:"World Travel Awards — Grand Final Gala Ceremony 2026", city:"Tanzania (venue not yet published)", country:"Tanzania", flag:"🇹🇿",
    dates:"12 December 2026", status:"Confirmed", delegates:null,
    detail:"Climax of WTA's Grand Tour 2026, marking Tanzania's second WTA event of the year after the August Africa Gala in Zanzibar.",
    soWhat:"Exact venue not yet confirmed — mainland Dar es Salaam and Zanzibar are both plausible given the August precedent. Confirm before quoting December group rates in either city; this note will update the moment a venue is named.",
    segment:"City, Beach", source:"World Travel Awards (worldtravelawards.com/event/africa-2026)", verified:false, flagged:"action" },

  { event:"Future Hospitality Summit (FHS) Africa 2027", city:"Kampala (Speke Resort Convention Centre)", country:"Uganda", flag:"🇺🇬",
    dates:"2–3 February 2027", status:"Bid won — first time in Uganda", delegates:"450+ expected (based on FHS Nairobi 2026 attendance)",
    detail:"Africa's leading hospitality investment and leadership forum moves to Uganda for the first time, after Nairobi hosted the 2026 edition (31 Mar–1 Apr, 450+ senior industry leaders, at the Radisson Blu Nairobi Upper Hill).",
    soWhat:"Uganda's first time hosting FHS is a direct signal the region's investor and developer circuit is testing Kampala as a serious destination — read together with the Hilton and Marriott Kampala openings, this is exactly the kind of event that turns a one-off signing into a sustained pipeline. Kampala city hotels have six months to get corporate and long-stay rate structures ready for a February investor influx.",
    segment:"City", source:"Breaking Travel News / ChimpReports / New Vision (UG)", verified:true, flagged:"action" },

  { event:"ICCA Congress 2027 — 66th edition", city:"Kigali Convention Centre", country:"Rwanda", flag:"🇷🇼",
    dates:"24–27 October 2027", status:"Bid won — first Africa host in 20 years", delegates:"2,000+",
    detail:"The International Congress and Convention Association's global congress returns to Africa for the first time in two decades. Brings together association representatives and industry leaders on growth strategy, capacity building and Africa's role in global business events.",
    soWhat:"A 14-month lead time and a confirmed 2,000+ delegate congress at Rwanda's flagship convention venue is about as clean a forward booking signal as this region produces. Kigali hotels and DMCs should be building October 2027 into 2026/27 rate planning now, not waiting for the pre-event rush — this is exactly the kind of confirmed compression a ledger entry is for.",
    segment:"City", source:"Tourism Update / VoyagesAfriq, Feb 2026", verified:true, flagged:"action" },

  { event:"Africa Fintech Summit (AFTS) Kigali 2026", city:"Kigali Convention Centre", country:"Rwanda", flag:"🇷🇼",
    dates:"18–20 November 2026 (main days 18–19)", status:"Confirmed", delegates:null,
    detail:"The largest bi-annual gathering of Africa's fintech ecosystem — regulators, policymakers, financial-industry executives, fintech founders, investors and startups — returns to the Kigali Convention Centre. Founded 2017; format runs keynotes, workshops, an awards ceremony, exhibition and startup pitch. No official delegate count published for the Kigali edition.",
    soWhat:"A two-day continental fintech congress at KCC in mid-November is a genuine city-compression event for Kigali, drawing a pan-African regulator-and-investor crowd into the low-season shoulder. It also lands in the SAME week Uganda Airlines launches its daily Entebbe–Kigali service (18 Nov) — twin demand signals on the same dates. Kigali city hotels should hold corporate rate across 17–20 Nov rather than discounting into November.",
    segment:"City", source:"africafintechsummit.com / Africa Business Communities, verified Aug 2026", verified:true, flagged:"action" },

  { event:"Kwita Izina 2026 — 21st gorilla naming ceremony", city:"Kinigi, Musanze (Volcanoes NP)", country:"Rwanda", flag:"🇷🇼",
    dates:"4 September 2026", status:"Confirmed", delegates:null,
    detail:"Rwanda's annual gorilla-naming ceremony, organised by the Rwanda Development Board at the foothills of Volcanoes National Park in Kinigi. Draws heads of state, conservationists, celebrities and diplomats; the flagship event of Rwanda's premium gorilla-tourism calendar. RDB formally unveiled the 21st-edition plans on 11 Aug 2026: 22 baby gorillas to be named.",
    soWhat:"A fixed early-September compression on premium Volcanoes-area lodges and on Kigali city stock (delegates route through Kigali). Gorilla-trekking and exclusive-use inventory around Musanze should hold rate through the first week of September rather than discounting into the shoulder; Kigali city hotels should expect a pre/post-ceremony bump.",
    segment:"Bush, City", source:"Rwanda Development Board / Taarifa, 11 Aug 2026 / kwitaizina.rw", verified:true, flagged:"action" }

 ],
 caveat: "Coverage favours large, publicly announced trade and business-events gatherings picked up by tourism boards, convention bureaux and trade press — it under-represents smaller academic, medical and association congresses that book a single hotel rather than a citywide block. A missing event here is not evidence one isn't happening; check directly with KICC, Rwanda Convention Bureau, JNICC (Dar) or your local convention bureau for anything sector-specific."
};
