# Phase 2: Business Questions and KPIs (approved)

**Data:** `data/processed/order_items.parquet` (built by `scripts/02_clean.py`)
**Baselines:** computed with DuckDB SQL on shipped (non-canceled) orders, Jan 2015 to Jan 2018

## Problem statement (draft)

> DataCo breaks its delivery promise on **57% of shipped orders**. Customers who pay for
> faster shipping are hit hardest: **every** First Class order arrives late. We want to
> find out whether the cause is slow fulfillment or unrealistic promises, and design a
> product change that makes delivery promises customers can trust.

## Unit of analysis

All items in an order share the same shipping mode, dates and late status (verified on
all 65,752 orders). So **delivery KPIs are measured per order**, not per item.
Measuring per item would over-weight multi-item orders, and orders switched from about
3 items to 1 item in Oct 2017, which would distort trends. Profit KPIs stay per item.

Canceled shipments (order status `CANCELED` or `SUSPECTED_FRAUD`, 4.3% of items) are
excluded from delivery KPIs because they never shipped.

## KPI definitions

| KPI | Definition | Baseline |
|---|---|---|
| **On-time delivery rate (OTD)** | Shipped orders where `days_actual <= days_scheduled` ÷ shipped orders | **42.7%** |
| Late rate | 1 − OTD | 57.3% |
| Avg days late (when late) | Mean of `days_actual − days_scheduled` over late orders | 1.62 days |
| Severe late rate | Shipped orders ≥ 2 days late ÷ shipped orders | 23.7% |
| Promise gap | Mean `days_actual − days_scheduled`, per shipping mode | see Q2 |
| Premium speed advantage | Avg `days_actual` (Standard) − avg `days_actual` (premium mode) | see Q3 |

## Business questions

### Q1. How often do we break our delivery promise?
Headline KPI: OTD = 42.7%. Phase 3 adds the trend over time, to see whether it is
getting better or worse.

### Q2. Which shipping modes break the promise most, and by how much?

| Mode | Share of orders | Promise | Late rate | Avg promise gap |
|---|---|---|---|---|
| First Class | 15.3% | 1 day | **100%** | +1.0 day |
| Second Class | 19.5% | 2 days | 80% | +2.0 days |
| Same Day | 5.4% | 0 days | 48% | +0.5 day |
| Standard Class | 59.8% | 4 days | 40% | 0.0 days |

### Q3. Are premium shipping modes actually faster?
Early evidence says **Second Class is not faster than Standard**. Both take 2, 3, 4, 5
or 6 days, each about 20% of the time. First Class always takes exactly 2 days.
Phase 3 confirms this and puts it in customer terms: *"Second Class buyers pay for
speed they don't get."*

### Q4. Does lateness depend on where, what or who?
Early evidence says **barely**. Late rates only range 55–60% across 21 regions,
14 categories, 3 customer segments, 7 order weekdays, 4 payment types and
8 departments. Shipping mode explains almost all of the difference.
**Implication:** the problem is the *promise rule*, not a specific warehouse, region or product.

### Q5. What promise would hit a target on-time rate?
For each mode, find the smallest promised days that would achieve 80% / 90% / 95% OTD,
based on the actual-days distribution. This sizes the product feature.

### Q6. Does lateness hurt the business?
- Profit: no visible link (late items average $21.62 profit vs $22.58 on time; both ~19% loss-making).
- **Repeat purchase:** are customers whose order arrived late less likely to order again? (Phase 3)
- Limitation: there are no reviews, returns or support tickets, so customer harm can only be
  measured through repeat behavior.

## An honest caveat for the write-up

Lateness is spread so evenly (identical shipping-time distributions, no regional
effect) that the dataset is **very likely synthetic**. A strong portfolio states this
plainly, and it changes what we should build:

- ❌ **A machine-learning "late delivery predictor"** would mostly learn "First Class = late".
  It would look impressive but contribute nothing.
- ✅ **A promise-calibration feature**: set each mode's promised delivery date from
  observed fulfillment times, and show honest ETAs at checkout. This follows directly
  from Q2, Q3 and Q5.

## Decisions (approved)

1. Headline KPI: **OTD, measured per order, excluding cancellations**.
2. Target for the proposed feature: **90% OTD**.
3. Q6 (repeat purchase) stays in scope.
