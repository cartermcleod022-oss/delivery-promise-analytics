"""
Phase 5: How big, and how long, must the A/B test be?

The question the test answers: does showing an honest delivery window (which
looks slower) make fewer shoppers finish checkout?

That's a NON-INFERIORITY test. We don't need the window to *raise* checkout
completion, only to prove it doesn't lower it by more than an acceptable margin.

Sample size per group (one-sided test, equal true rates assumed):
    n = (z_alpha + z_beta)^2 * 2 * p * (1 - p) / (margin * p)^2
      p      = baseline checkout completion rate
      margin = the largest relative drop we'd accept (e.g. 5%)
      alpha  = 0.05 (5% false-alarm risk), power = 0.80 (80% chance to detect a real problem)

ASSUMPTION: the dataset has no checkout or session data, so the baseline completion
rate is unknown. We show a range of plausible values instead of pretending to know it.
Order volume IS in the data, and it decides how long the test takes.

Run from the project folder:
    .venv/bin/python scripts/05_test_plan.py
"""

import math
import os
from pathlib import Path
from statistics import NormalDist

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

ALPHA, POWER = 0.05, 0.80
BASELINES = [0.30, 0.45, 0.60]   # assumed checkout completion rates
MARGINS = [0.02, 0.05, 0.10]     # largest acceptable relative drop

con = duckdb.connect()
con.execute(Path("sql/00_views.sql").read_text())
orders_per_week = con.sql("""
    SELECT COUNT(DISTINCT order_id) / (DATE_DIFF('day', MIN(order_date), MAX(order_date)) / 7.0)
    FROM items
""").fetchall()[0][0]
print(f"Order volume from the data: {orders_per_week:,.0f} orders per week (all orders)")

z = NormalDist().inv_cdf
z_total = z(1 - ALPHA) + z(POWER)

rows = []
for p in BASELINES:
    # If p of checkouts become orders, checkouts per week = orders / p.
    checkouts_per_week = orders_per_week / p
    for margin in MARGINS:
        n_per_group = math.ceil(z_total ** 2 * 2 * p * (1 - p) / (margin * p) ** 2)
        weeks = 2 * n_per_group / checkouts_per_week  # two groups, 50/50 split
        rows.append({
            "baseline_completion": f"{p:.0%}",
            "max_acceptable_drop": f"{margin:.0%}",
            "checkouts_per_group": n_per_group,
            "weeks_to_run": round(weeks, 1),
        })

plan = pd.DataFrame(rows)
plan.to_csv(PROJECT_ROOT / "outputs" / "tables" / "p5_test_sample_size.csv", index=False)
print("\nSAMPLE SIZE AND DURATION (alpha = 0.05 one-sided, power = 0.80)")
print(plan.to_string(index=False))
