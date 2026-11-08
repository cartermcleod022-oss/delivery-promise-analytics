# PRD: Reliable Delivery Window

| | |
|---|---|
| **Author** | Carter McLeod (drafted with Claude Code) |
| **Status** | Draft for review |
| **Evidence** | [Phase 3 findings](phase3_findings.md) · [Phase 4 prioritization](phase4_prioritization.md) |
| **Code** | `sql/p5_delivery_windows.sql` (window rule) · `scripts/05_test_plan.py` (test sizing) |

## 1. Summary

DataCo breaks its delivery promise on **57% of orders**. The cause isn't slow shipping:
the promise is a fixed number per shipping mode that fulfillment never matches. This
feature replaces the fixed number with a **delivery window computed from real fulfillment
times**, such as *"Arrives Tue–Sat, usually Thu"*. Historically, this window would have been met 100% of the time.

Shipped with two small companion fixes, it lifts on-time delivery from **42.7% to 84.4%**.
Merging Second Class into Standard afterward takes it past the 90% target.

## 2. Problem

| Evidence | Source |
|---|---|
| On-time delivery (OTD) is 42.7%, flat for 3 years | Phase 3, Q1 |
| First Class is late on **100%** of orders: it always ships in 2 days but promises 1 | Q2 |
| Standard ships in 2–6 days (evenly spread) but promises 4, so 40% are late | Q3 |
| Region, product and customer barely matter (≤7 pts); shipping mode explains it (60 pts) | Q4 |

**The real problem is trust.** A customer who plans around a date (a gift, a work deadline,
being home for a delivery) gets the wrong date more often than the right one. The customers
paying extra for speed fare worst.

## 3. Goals and non-goals

**Goals**
1. Promise dates customers can rely on: **OTD ≥ 90%** against the promised date.
2. Keep promises as attractive as honesty allows, by showing the *earliest* and *typical* arrival, not only the latest.
3. Don't lose sales by showing longer-looking promises (see guardrails).

**Non-goals**
- Making shipping **faster**. This feature fixes the promise, not the speed. Narrowing Standard's
  2–6 day spread is a separate operations initiative (see §10).
- Per-order prediction with machine learning. Phase 3 showed shipping mode explains nearly all
  of the variation, so a model would add complexity without accuracy.
- Changing shipping prices. That's part of the Second Class decision (fix B), which comes after this test.

## 4. Users

| User | Need | Today | With this feature |
|---|---|---|---|
| **Planner:** a Standard shopper buying something they need by a date | Know the latest it will arrive | Told "4 days"; 40% of the time it's later | Told "Tue–Sat"; it's never later |
| **Speed buyer:** pays for First Class to get it fast | Get what they paid for | Promised 1 day, always gets 2 | Promised 2 days, always gets 2 |
| **Support agent** (internal) | Fewer "where is my order?" contacts | Over half of orders become late | Late orders become rare |

*Note: average order value (~$500) and customer segment mix are identical across shipping modes,
so personas are defined by **need**, not by spending or segment.*

User stories:
- As a **planner**, I want to see the latest date my order can arrive, so I can decide whether to buy now.
- As a **speed buyer**, I want the date shown for a faster option to be true, so the extra I pay is worth it.
- As a **support agent**, I want orders to arrive inside the promised window, so customers don't contact us about lateness.

## 5. The experience

**Checkout shipping selector: today vs. proposed**

```
TODAY                                    PROPOSED
( ) Standard        4 days               ( ) Standard     Arrives Tue–Sat · usually Thu
( ) Second Class    2 days               ( ) First Class  Arrives Tue (2 days)
( ) First Class     1 day                ( ) Next Day     Arrives tomorrow · often today
( ) Same Day        today
```
*(Second Class is still shown during the test and removed only if fix B is approved later.)*

Where the window appears (in priority order):

| Surface | Priority | Content |
|---|---|---|
| Checkout shipping selector | **P0** | Window plus typical day for each mode |
| Order confirmation email | **P0** | The same window, matching checkout exactly |
| Order tracking page | P1 | Window, then the actual ship date once known |
| Product page | P2 | "Order today, arrives Tue–Sat" (later phase) |

## 6. Requirements

**The window rule** (computed per shipping mode from fulfillment history; see `sql/p5_delivery_windows.sql`):

| Field | Definition | Standard | First Class | Same Day → Next Day |
|---|---|---|---|---|
| Earliest | Fastest actual shipping time seen | 2 days | 2 | 0 |
| Typical | Median actual shipping time | 4 | 2 | 0 |
| **Committed** | Smallest day count covering ≥ 90% of orders. This is what OTD is measured against. | **6** | **2** | **1** |
| OTD at committed day (historical) | | 100% | 100% | 100% |

| # | Requirement | Priority |
|---|---|---|
| R1 | Compute earliest / typical / committed per mode with the rule above | P0 |
| R2 | Recompute weekly on a rolling 90 days of orders, so the window follows real performance | P0 |
| R3 | If a mode has too few recent orders (< 200 in 90 days), keep the last valid window | P0 |
| R4 | Show the window in checkout and confirmation email with identical dates | P0 |
| R5 | Convert day counts to calendar dates (e.g. "Tue–Sat") | P0 |
| R6 | Log the committed date on every order, so OTD can be measured against what the customer saw | P0 |
| R7 | Ops dashboard: OTD vs. committed date, by mode, weekly | P1 |
| R8 | Alert when weekly OTD vs. committed date falls below 90% for any mode | P1 |
| R9 | Tracking page shows the window, then the actual ship date | P1 |

**Launch companions** (no new build; the rule produces these automatically):
- **Fix A:** First Class committed date becomes 2 days.
- **Fix D:** "Same Day" is renamed "Next Day", committed at 1 day.

## 7. Success metrics

| Type | Metric | Baseline (data) | Target |
|---|---|---|---|
| **Primary** | OTD vs. committed date (shipped orders) | 42.7% | ≥ 84% at launch (A + C + D); ≥ 90% after fix B |
| Secondary | Severe lateness (≥ 2 days late) | 23.7% | < 5% |
| Secondary | "Where is my order?" support contacts | *not in data* | Decrease (measure from launch) |
| **Guardrail** | Checkout completion rate | *not in data* | No drop greater than 5% relative (non-inferiority test, §8) |
| **Guardrail** | Share of orders choosing premium shipping | 40.2% | No drop greater than 5 pts |
| **Guardrail** | Average actual shipping days | 3.5 days | Must not increase |

The last guardrail matters. Looser promises could let operations get slower without anyone
noticing, so actual speed is tracked separately from OTD.

## 8. Experiment design

**Why test at all?** The OTD gain is certain: replaying history shows it. What's unknown is
whether shoppers who see a later-looking date ("Tue–Sat" instead of "4 days") **abandon checkout**.
That's what the test measures.

| | |
|---|---|
| Design | A/B test, shopper-level randomization, 50/50 split |
| Control | Today's fixed promises |
| Treatment | Delivery window (with fixes A and D) |
| Primary test metric | Checkout completion rate |
| Test type | **Non-inferiority:** prove the window doesn't lower completion by more than the margin |
| Margin | **5% relative** |
| Significance / power | α = 0.05 (one-sided), 80% power |
| Duration | **10–17 weeks**, depending on the baseline completion rate (unknown, see table) |

**Why a 5% margin, not 2%?** DataCo processes about **409 orders a week**, so test duration
depends on that volume:

| Baseline completion (assumed) | 2% margin | **5% margin** | 10% margin |
|---|---|---|---|
| 30% | 106 weeks | **17 weeks** | 4 weeks |
| 45% | 83 weeks | **13 weeks** | 3 weeks |
| 60% | 61 weeks | **10 weeks** | 2 weeks |

A 2% margin would take one to two years, which is too slow to be useful. A 10% margin would
let a real loss slip through. **5% balances speed and safety.** The first step before
launch is to pull the real baseline from web analytics; it decides which row applies.

**Decision rules**
- **Ship** if the completion rate is non-inferior (the confidence interval's lower bound is above −5%) and no guardrail is breached.
- **Iterate** if it's inferior only for Standard. Try showing "usually Thu" more prominently, or a narrower window with a lower commit level (e.g. day 5 = 80% OTD).
- **Kill** if completion drops by more than 5% across modes. Fall back to fixes A + D only (+17.9 pts OTD, no checkout change).

## 9. Rollout

| Step | What | Gate to move on |
|---|---|---|
| 0 | Instrument: log committed date per order (R6); pull baseline checkout completion | Data flowing |
| 1 | Ship **A + D** to everyone (promise numbers only) | Premium-share guardrail holds for 2 weeks |
| 2 | **A/B test** the delivery window (C) | Decision rules in §8 |
| 3 | Roll out C to 100% | Ship decision |
| 4 | Decide **B** (merge Second Class) using step 2's data on Second Class choice | Finance review of shipping revenue |

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Competitors show shorter (if unreliable) promises, so DataCo looks slow | Lead with the earliest and typical day ("usually Thu"); test measures the real effect |
| Looser promises let operations slow down | "Actual shipping days" guardrail and R8 alerts |
| A 2–6 day window looks vague | Show calendar dates and a typical day, not "2–6 days" |
| Window goes stale if fulfillment changes | Weekly recompute (R2), plus alerts (R8) |
| Shipping-fee revenue falls if fewer customers pick premium | Premium-share guardrail; finance review before fix B |
| **Analysis based on a likely synthetic dataset** | Re-run the window rule and test sizing on real order history before committing |

## 11. Stakeholders

| Team | Likely concern | Response |
|---|---|---|
| Operations | "Promises got easier, so will we be judged on them?" | Yes, and actual speed is tracked separately; the long-term goal is narrowing the 2–6 day spread |
| Finance | Shipping-fee revenue from premium tiers | Guardrail plus a gate before fix B |
| Marketing | "Our promises look slower than competitors'" | Test the actual effect; position on reliability ("arrives when we say") |
| Customer support | Fewer lateness contacts | Primary beneficiary; help define the contact metric |
| Engineering | Scope | P0 set is a weekly batch job plus two display surfaces |

## 12. Open questions

1. What is today's checkout completion rate? (It sets the test length.)
2. Do weekends count as delivery days? (It affects how "Tue–Sat" is computed.)
3. What does Second Class cost customers, and what share of shipping revenue is it? (Needed for fix B.)
4. Is 90% the right confidence level for the committed date, or should premium modes use a stricter 95%?
