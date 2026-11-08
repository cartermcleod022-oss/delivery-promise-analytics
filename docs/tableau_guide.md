# Rebuild the Dashboard in Tableau Public

You'll rebuild the web dashboard (`dashboard/index.html`) in Tableau Public yourself, so
you can put Tableau on your resume honestly. It takes about 2–3 hours the first time. Work
through it in order, and check your numbers against the **checkpoints** as you go: if they
match, your calculations are right.

**Data file:** `tableau/orders_for_tableau.csv` (one row per shipped order, 62,897 rows).
Rebuild it any time with `.venv/bin/python scripts/07_export_tableau.py`.

| Column | Meaning |
|---|---|
| Order ID, Order Date | Identifiers |
| Shipping Mode | Same Day, First Class, Second Class, Standard Class |
| Promised Days / Actual Days | What we promised vs. how long it took |
| Days Late | Actual − Promised (negative means early) |
| On Time | 1 if Actual ≤ Promised, else 0 |
| Market, Region, Customer Segment | For filters and breakdowns |
| Sales, Profit | Order totals |

> Menu names below match recent Tableau Public versions. If a menu looks slightly
> different, search the Tableau help for the term in **bold**.

## Step 0: Install and connect (15 min)

1. Create a free account at **public.tableau.com**, then download and install **Tableau Public** for Mac.
2. Open it. Under **Connect → To a File → Text file**, choose `tableau/orders_for_tableau.csv`.
3. In the data preview, check the types: *Order Date* should be a date and *Promised Days*,
   *Actual Days*, *Days Late*, *On Time*, *Sales* and *Profit* numbers. Click the type icon above a column to fix it.
4. Click **Sheet 1** at the bottom to start building.

## Step 1: Calculated fields (20 min)

**Analysis → Create Calculated Field** for each. Type the formula exactly.

| Name | Formula |
|---|---|
| OTD | `AVG([On Time])` |
| Late Rate | `1 - AVG([On Time])` |
| Severe Late Rate | `AVG(IF [Days Late] >= 2 THEN 1 ELSE 0 END)` |
| Avg Days Late (when late) | `AVG(IF [Days Late] > 0 THEN [Days Late] END)` |
| Promise Gap | `AVG([Actual Days]) - AVG([Promised Days])` |

Right-click OTD, Late Rate and Severe Late Rate → **Default Properties → Number Format → Percentage**, 1 decimal.

**Checkpoint:** drag *OTD* onto an empty sheet. It should read **42.7%**. Severe Late Rate should be **23.7%**,
Avg Days Late **1.62**, and Promise Gap **0.57**.

## Step 2: The what-if parameters (20 min)

This is what makes the dashboard interactive. A **parameter** is a value the viewer can change.

1. **Create Parameter** (data pane ▾ menu) four times, each with *Data type: Integer*, *Allowable values: Range*, min 0, max 6, step 1:

   | Name | Current value |
   |---|---|
   | Promise Same Day | 0 |
   | Promise First Class | 1 |
   | Promise Second Class | 2 |
   | Promise Standard | 4 |

2. Create one more: **Merge Second Class**, *Data type: Boolean*, current value False.
3. Calculated fields:

   **Simulated Promise**
   ```
   CASE [Shipping Mode]
   WHEN 'Same Day'       THEN [Promise Same Day]
   WHEN 'First Class'    THEN [Promise First Class]
   WHEN 'Second Class'   THEN IF [Merge Second Class] THEN [Promise Standard] ELSE [Promise Second Class] END
   WHEN 'Standard Class' THEN [Promise Standard]
   END
   ```
   **Simulated On Time:** `IF [Actual Days] <= [Simulated Promise] THEN 1 ELSE 0 END`
   **Simulated OTD:** `AVG([Simulated On Time])` (format as a percentage)
   **On Time Label:** `IF [Actual Days] <= [Simulated Promise] THEN "On time or early" ELSE "Late" END`

4. Right-click each parameter → **Show Parameter**.

**Checkpoint:** set First Class to 2, Same Day to 1, Standard to 6. Simulated OTD should read **84.4%**.
Tick Merge Second Class and it should read **100.0%**. Set them back to 0 / 1 / 2 / 4 / False afterward.

## Step 3: Build the sheets (60–90 min)

Make a new sheet for each (bottom tab bar → new sheet icon), and name it.

**KPI: On-time delivery.** Drag *OTD* to **Text** on the Marks card. Format it large (Format → Font, ~28pt).
Repeat on separate sheets for Severe Late Rate, Avg Days Late, and Simulated OTD.

**Trend.**
- Right-click-drag *Order Date* to Columns and choose **MONTH(Order Date)**, the continuous (green) version.
- Put *OTD* on Rows and *Shipping Mode* on **Color**.
- Right-click the y-axis → **Add Reference Line** → Constant 0.9, labeled "Target 90%".
- **Checkpoint:** First Class is a flat line at 0%, and Standard hovers around 60%.

**Scorecard.**
- *Shipping Mode* on Rows.
- *OTD* on Columns (bar chart).
- Drag *AVG(Promised Days)* and *AVG(Actual Days)* to **Label** or **Tooltip**.
- **Checkpoint:** First Class 0%, Second Class 20%, Same Day 52%, Standard 60%.

**Promise vs. reality (the simulator).**
1. Put *Shipping Mode* on Columns, then *Actual Days* on Columns to its right. *Actual Days* must be a **dimension**: right-click it → Convert to Dimension, and make it Discrete (blue).
2. Put **CNT(Order ID)** on Rows.
3. Right-click it → **Quick Table Calculation → Percent of Total**, then **Compute Using → Actual Days**, so each mode adds up to 100%.
4. Put *On Time Label* on **Color**: green for on time, red for late.
5. **Checkpoint:** Standard shows five bars of ~20% each (days 2–6). Moving the *Promise Standard* parameter turns bars green or red.

**Regions.**
- *Region* on Rows and *Late Rate* on Columns.
- Sort descending (toolbar sort button).
- Add an **Average** reference line on the x-axis.
- **Checkpoint:** every region lands between ~53% and 60%.

## Step 4: Assemble the dashboard (30 min)

1. **Dashboard → New Dashboard.** Set Size to *Automatic* or *Fixed 1200 × 900*.
2. Drag sheets in, matching the web version's layout:
   - top: the KPI sheets in a row
   - middle: Trend and Scorecard side by side
   - lower: the simulator sheet with Simulated OTD beside it
   - bottom: Regions
3. **Filters:** on the Trend sheet, right-click *Order Date* → Show Filter (choose *Years*), and do the same for *Market*
   and *Customer Segment*. On each filter: ▾ → **Apply to Worksheets → All Using This Data Source**.
4. Show the five parameter controls next to the simulator sheet (▾ on the sheet → Parameters).
5. Add a title and a text box with one line of method: "On time = actual ≤ promised days; canceled orders excluded."

**Checkpoint:** set the Year filter to 2016. Every sheet should change, and OTD should stay near 43%.

## Step 5: Publish (10 min)

1. **File → Save to Tableau Public** and sign in. Name it *Delivery Promise Monitor*.
2. On the public page, open **Settings**, untick *Allow workbook to be downloaded* if you prefer, and copy the link.
3. Add the link to this repo's README ("Tableau version: …") and to your resume or LinkedIn.

## What you can now say

> *Built an interactive Tableau Public dashboard with parameter-driven what-if analysis, letting
> users test delivery-promise policies against 63K historical orders.*

Be ready to explain in an interview:
- **Why parameters?** They let the viewer change an assumption (the promise) and see the effect,
  which turns a report into a decision tool.
- **Why *Percent of Total, compute using Actual Days*?** So each mode's bars add up to 100% within that mode.
- **Why does Simulated OTD go to 100%?** Shipping times have a hard maximum in this data. On real data
  it wouldn't, and that's why the PRD commits at the 90th percentile instead of the maximum.
