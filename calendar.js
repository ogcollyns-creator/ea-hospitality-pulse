// EA Pulse Data Release Calendar — know when the numbers land, analyse them first.
// Most outlets report these 2-3 days late. That lag is the edge.
window.DATACAL = {
 updated: "29 July 2026",
 note: "Recurring statistical and policy releases across the five markets. Timings are the published pattern — confirm exact dates on the source site.",
 sources: [
  { body:"KNBS", country:"Kenya", flag:"🇰🇪", release:"Consumer Price Index & inflation", cadence:"Monthly — typically last few days of the month", why:"Sets the wage, food and laundry cost trajectory. Kenya is the region's inflation outlier.", url:"https://www.knbs.or.ke/" },
  { body:"KNBS", country:"Kenya", flag:"🇰🇪", release:"Leading Economic Indicators (incl. tourist arrivals, hotel bed-nights)", cadence:"Monthly", why:"The closest thing to official occupancy data. Arrivals by origin market.", url:"https://www.knbs.or.ke/" },
  { body:"Tourism Research Institute", country:"Kenya", flag:"🇰🇪", release:"Tourism performance & arrivals", cadence:"Quarterly + annual", why:"Authoritative arrivals by source market — the number to quote.", url:"https://tri.go.ke/" },
  { body:"Central Bank of Kenya", country:"Kenya", flag:"🇰🇪", release:"Weekly bulletin (FX, reserves, rates)", cadence:"Weekly, Fridays", why:"FX cross-rates and reserves — the cost-side input.", url:"https://www.centralbank.go.ke/" },
  { body:"Central Bank of Kenya", country:"Kenya", flag:"🇰🇪", release:"MPC rate decision", cadence:"Roughly every 2 months", why:"Sets borrowing costs for anyone with a refurbishment or expansion loan.", url:"https://www.centralbank.go.ke/" },
  { body:"EPRA", country:"Kenya", flag:"🇰🇪", release:"Fuel price review", cadence:"Monthly — announced ~14th, effective 15th", why:"Directly moves safari transfer, generator and supply costs. A diarised, knowable date.", url:"https://www.epra.go.ke/" },
  { body:"EPRA", country:"Kenya", flag:"🇰🇪", release:"Electricity tariff adjustment (fuel energy cost + forex charges)", cadence:"Monthly, published with the billing cycle", why:"The pass-through charges now add over KSh 5/kWh and move every month — a bigger swing for most properties than the fuel price review, and almost never reported.", url:"https://www.epra.go.ke/" },
  { body:"NBS Tanzania", country:"Tanzania", flag:"🇹🇿", release:"CPI / inflation", cadence:"Monthly", why:"Tanzania's benign cost base is a competitive advantage worth quantifying.", url:"https://www.nbs.go.tz/" },
  { body:"NBS Tanzania / MNRT", country:"Tanzania", flag:"🇹🇿", release:"International arrivals & tourism earnings", cadence:"Annual, with periodic updates", why:"Tanzania posted record US$4.41bn earnings in 2025 — the trend line matters.", url:"https://www.nbs.go.tz/" },
  { body:"OCGS Zanzibar", country:"Zanzibar", flag:"🇹🇿", release:"Zanzibar arrivals statistics", cadence:"Monthly", why:"Zanzibar now clears 100k visitors in peak months. Monthly granularity beats annual.", url:"https://www.ocgs.go.tz/" },
  { body:"UBOS", country:"Uganda", flag:"🇺🇬", release:"CPI / inflation", cadence:"Monthly, end of month", why:"Underpins the shilling's strength story.", url:"https://www.ubos.org/" },
  { body:"Bank of Uganda", country:"Uganda", flag:"🇺🇬", release:"MPC & FX data", cadence:"Bi-monthly MPC; regular FX", why:"UGX strength is a live margin issue for USD-earning operators.", url:"https://www.bou.or.ug/" },
  { body:"NISR", country:"Rwanda", flag:"🇷🇼", release:"CPI & tourism statistics", cadence:"Monthly CPI; periodic tourism", why:"Rwanda's source-market mix is shifting fast — DRC now leads.", url:"https://www.statistics.gov.rw/" },
  { body:"Rwanda Development Board", country:"Rwanda", flag:"🇷🇼", release:"Tourism revenue & arrivals", cadence:"Quarterly / annual", why:"RDB is the primary source for permit policy and arrivals by origin.", url:"https://rdb.rw/" },
  { body:"UN Tourism (UNWTO)", country:"Global", flag:"🌍", release:"World Tourism Barometer", cadence:"Roughly quarterly", why:"Global context and source-market outlook for long-haul demand.", url:"https://www.unwto.org/" },
  { body:"IATA", country:"Global", flag:"🌍", release:"Air passenger market analysis (incl. Africa)", cadence:"Monthly", why:"Regional air demand — the leading indicator for arrivals.", url:"https://www.iata.org/" }
 ]
};
