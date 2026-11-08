# Phase 1: First Look at the DataCo Dataset

**Source:** [DataCo Smart Supply Chain for Big Data Analysis](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) (Kaggle)
**Script:** `scripts/01_first_look.py` · **Column profile:** `data/column_profile.csv`

## Shape of the data

- 180,519 rows × 53 columns, no duplicate rows
- Each row is one **order item**; there are 65,752 unique orders
- Order dates: January 2015 to January 2018
- File encoding is latin-1 (not UTF-8)

## Key findings

### 1. Late delivery is the dominant problem

| Delivery status | Share of items |
|---|---|
| Late delivery | 54.8% |
| Advance shipping | 23.0% |
| Shipping on time | 17.8% |
| Shipping canceled | 4.3% |

Average actual shipping time is 3.5 days against 2.9 scheduled.

### 2. The `Late_delivery_risk` flag is reliable

It equals `real days > scheduled days` on 97.5% of rows. All 4,423 exceptions are
canceled shipments, which were never delivered. **Decision:** exclude canceled
shipments from late-delivery KPIs.

### 3. Premium shipping modes are late most often

| Shipping mode | Promised days | Late rate |
|---|---|---|
| Standard Class | 4 | 38% |
| Same Day | 0 | 46% |
| Second Class | 2 | 77% |
| First Class | 1 | 95% |

Each mode always carries the same promised days, which suggests a fixed promise rule
rather than one based on the order. **Hypothesis:** the promise is unrealistic, rather
than fulfillment being slow.

### 4. There is no inventory signal

`Product Status` (stock availability) is 0 for every row, and there are no stock or
warehouse fields. **Decision:** the project focuses on delivery promises and
late-delivery risk, not inventory forecasting.

## Data quality issues (handled in Phase 2)

| Issue | Action |
|---|---|
| 6 pairs of identical columns (e.g. `Benefit per order` = `Order Profit Per Order`) | Keep one of each |
| `Product Description` 100% empty, `Order Zipcode` 86% empty | Drop |
| `Product Status` constant | Drop |
| Personal or masked fields (email, password, names, street) | Drop |
| Dates stored as text | Convert to datetime |
| Monthly *item* volume drops from Oct 2017 (~5,200 to ~2,100). Phase 2 showed *order* volume is steady (~1,700–2,100/month); orders simply switch from ~3 items to 1 item each | Flag with `is_low_volume_period`; analyze at order level |
| 18.7% of items have negative profit | Secondary angle |
| `Customer *` fields = buyer (US / Puerto Rico); `Order *` fields = destination (164 countries) | Use `Order *` fields for delivery analysis |
