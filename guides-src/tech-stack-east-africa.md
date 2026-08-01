---
title: The East African hotel tech stack — payment costs, PMS fit and where AI pricing actually works
slug: tech-stack-east-africa
description: What payment gateways actually cost by provider, which property management systems publish genuine offline capability, and the data volume AI pricing tools need before they're worth paying for — set against the real scale of most East African bush and beach properties.
category: Technology
updated: 2026-08-01
---

Three technology decisions recur across almost every conversation with an East African operator: which payment provider actually keeps the most of a booking's value, whether a given PMS survives a camp's connectivity reality rather than just claiming to, and whether an AI pricing tool is built for a property this size at all. This page carries the published, checkable facts behind each — not vendor marketing translated into a recommendation.

## What a payment actually costs you, by provider

The headline percentage a provider advertises is rarely the number that lands on your settlement statement. Compare the mechanism, not just the rate.

**M-Pesa direct (Buy Goods / Till).** For domestic Kenyan transactions taken directly through a Safaricom till number, the merchant fee is 0.5% of transaction value, capped at KES 200 per transaction, dropping to 0.25% for transactions under KES 200. The guest pays nothing extra. This is structurally the cheapest way to collect a Kenyan-shilling payment from a Kenyan guest — but it only works for domestic mobile money, not for an international card or an overseas bank transfer.

**Payment aggregators (Pesapal, Flutterwave, DPO Group).** These sit on top of M-Pesa and card rails to give you one integration covering multiple payment methods, and they charge for that convenience. Pesapal is reported at roughly 3–3.5% per transaction. Flutterwave is reported at approximately 1.4% for local Kenyan transactions, rising to around 3.8% for international cards. DPO Group — the aggregator most visibly built for hospitality specifically, marketing dedicated hotel payment tools across Kenya, Tanzania, Uganda, Rwanda and beyond — does not publish its fee schedule; pricing is negotiated per merchant, so treat any rate quoted to you as specific to your account, not a market benchmark.

**Stripe.** Worth a specific flag because assumptions about it are commonly wrong: Stripe does not officially support merchant accounts registered in Kenya. Businesses using it typically do so by registering the receiving entity in a Stripe-supported country, which is a real operational and compliance step, not a checkbox. Where Stripe is in use — commonly behind a booking engine or OTA integration rather than a direct guest-facing checkout — a card issued outside your account's country triggers a 1.5% cross-border fee, and a currency mismatch between the payment and your settlement currency adds a further 1% conversion fee on top of the base card rate. For a European or American guest's card settling into a Kenyan account, both surcharges typically apply simultaneously.

**The practical read.** If a guest is paying in Kenyan shillings from a Kenyan phone, M-Pesa direct is close to unbeatable on cost. Everything else — a UK card, a US card, a euro-denominated agent payment — routes through an aggregator or card network layer carrying real, stacking fees. Model your actual guest-payment mix by currency and method before assuming one provider's headline rate applies to your whole revenue base.

## Property management systems: what's claimed for low connectivity, and what isn't verified

A recurring, specific question from bush and remote-camp operators: which PMS actually keeps functioning when the link drops. The honest answer is that several vendors publish offline-mode claims aimed specifically at this problem — but the claims themselves come from the vendors, and we have not independently verified field performance at a remote East African camp for any of them. Treat what follows as what's marketed, not as a tested result.

**General cloud PMS with offline modes.** Several mainstream cloud platforms, including Hotelogix, publish an offline mode that caches critical front-desk data locally and continues basic check-in and guest-service functions through a connectivity outage, syncing automatically once the link returns. This is a general capability, not one built specifically for the African bush-camp case.

**Systems marketed specifically for safari and lodge operations.** CiMSO markets data replication across servers as a core feature, explicitly framed around remote camps with inconsistent connectivity operating locally and syncing centrally when possible. Semper markets a resort and lodge management system with offline access to bookings, point-of-sale and operations without requiring an internet connection. Both are positioned directly at the property type most exposed to this problem, which at minimum indicates the vendors understand the use case — independent verification of how either performs at an actual off-grid East African property is the missing piece.

**Channel managers.** SiteMinder is reported as the most-deployed independent-hotel channel manager among African hoteliers specifically, connecting to 450-plus OTAs, with per-property pricing typically in the USD 60–150/month range. RateGain pairs channel management with a genuine rate-intelligence and competitive-monitoring engine as a core product rather than an add-on, connecting to 300-plus channels, but does not publish first-party pricing — its sales process is demo-led. The choice is less about which is "better" and more about whether you need SiteMinder's breadth of OTA reach or RateGain's built-in competitive rate visibility more.

**If you run one of these systems at a genuinely low-connectivity property**, what you've actually experienced — sync reliability, how it behaves during a multi-day outage, what breaks first — is exactly the kind of operator-sourced fact no vendor page will tell you and this page currently can't verify independently. Get in touch.

## AI pricing tools: the data volume question decides fit before anything else does

The AI revenue-management pitch is consistent across vendors: connect your PMS, let the model set your rate. The part that gets glossed over is how much booking history the model needs before its output is worth trusting over a human's judgement — and that number is structural, not a vendor claim.

**Published data requirements.** Industry guidance is consistent that these models need roughly a full season of a property's own booking history to calibrate properly, with one commonly cited threshold being at least 12 months of data for a property of 20 rooms or more — below that scale and history, recommendation quality is explicitly reported as degraded. Some vendors, RoomPriceGenie among them, market a workaround: blending limited property-specific history with broader market data to shorten the calibration period. That is a genuine product feature worth evaluating — but it is the vendor's own claim about its own model, not an independently verified result, and should be tested against your actual booking calendar rather than taken as given.

**Set that against the real shape of East African inventory.** A meaningful share of the region's bush and beach product — tented camps, small owner-run lodges, boutique beach properties — sits well under the 20-room threshold the published guidance uses as a rough viability line, and carries booking volumes shaped by a hard dry-season/green-season split rather than the smoother year-round demand curve these models are generally built against. That is not a claim that AI pricing "doesn't work" for a nine-tent camp — it is a structural reason to expect the tool needs more calibration time, more caution in low-volume shoulder months, and more human override than the same tool would need running a 120-room Nairobi property with steady corporate demand. A city hotel operator and a six-tent Mara camp operator are evaluating a fundamentally different fit question, even when looking at the identical product.

**What we won't do here** is repeat a vendor-reported uplift statistic — a "19% RevPAR increase" or similar — as if it were a verified outcome. Those figures come from the vendor's own client base under unstated conditions, and repeating them without the denominator is exactly the kind of unearned confidence this publication exists to avoid.

## What we don't know, and are not going to guess

DPO Group's actual fee schedule, verified field performance of any PMS's offline mode at a real East African property during a multi-day outage, and any independently measured revenue impact of AI pricing tools specifically in this region are all currently unpublished or unverifiable at the level of specificity this page needs. If you have direct, first-hand experience with any of these — an actual settlement statement, a lived connectivity failure, a before/after RevPAR you're willing to share — that is precisely the kind of operator-sourced fact this publication exists to carry instead of a vendor's own claim about itself.
