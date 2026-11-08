# Decision Log

Every judgment call in the project, who made it, and why. Data-driven facts live in
the phase findings; this file is for the **choices**.

| # | Phase | Decision | Made by | Reasoning |
|---|---|---|---|---|
| 1 | 1 | Focus on delivery promises, not inventory | Claude (proposed), Carter (approved) | `Product Status` is constant and there is no stock data |
| 2 | 2 | Headline KPI = on-time delivery (OTD), per order, excluding cancellations | Carter | Items in an order share one outcome; canceled orders never shipped |
| 3 | 2 | OTD target = **90%** | Carter | Chosen from 80 / 90 / 95% options |
| 4 | 2 | Keep repeat-purchase analysis (Q6) in scope | Carter | Tests whether lateness costs customers |
| 5 | 3 | Report Q6's null result rather than drop it | Claude | Honest negative results build credibility |
| 6 | 4 | Second Class: **merge into Standard** (rather than speed up, discount, or relabel) | Claude (recommended), Carter (accepted) | It is no faster than Standard; no cost data to justify speeding it up |
| 7 | 4 | Standard: show a **2–6 day window**, committed by day 6 | Claude (recommended), Carter (accepted) | Honest about the spread; early end keeps checkout appealing vs. a flat "6 days" |
| 8 | 4 | Same Day → **Next Day** (1-day promise) | Claude (recommended), Carter (accepted) | Same-day happens only 52% of the time; next-day 100% |
| 9 | 4 | RICE Confidence and Effort ratings | Claude (proposed), Carter (to review) | See reasons in `scripts/04_prioritize.py` and `phase4_prioritization.md` |
| 10 | 4 | Make **C** (delivery window) the Phase 5 feature; ship B after C's test | Claude (recommended), Carter (accepted) | Biggest single gain; B is worth 3× more after C |
| 11 | 5 | Committed date = smallest day covering ≥ 90% of orders, recomputed weekly | Claude (proposed), Carter (to review) | Matches the 90% OTD target; weekly refresh keeps it honest |
| 12 | 5 | A/B test margin = **5% relative** drop in checkout completion | Claude (proposed), Carter (to review) | At ~409 orders/week a 2% margin takes 1–2 years; 10% is too loose |
| 13 | 5 | Personas defined by need, not segment | Claude | Order value and segment mix are identical across shipping modes |

**Open for Carter:**
- **#9:** if you'd rate any Effort or Confidence differently, change `JUDGMENT` in
  `scripts/04_prioritize.py` and re-run. The ranking and chart update automatically.
- **#11, #12:** confirm or change the 90% commit level and the 5% test margin (PRD §6 and §8).
