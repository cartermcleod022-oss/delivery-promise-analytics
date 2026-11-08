"""
Phase 4: Rank the fixes with RICE and show how far each one moves OTD.

RICE = Reach x Impact x Confidence / Effort
  Reach x Impact : extra on-time orders per month (from sql/p4_fix_scenarios.sql)
  Confidence     : judgment (high 1.0 / medium 0.8 / low 0.5), reasons below
  Effort         : judgment, in person-weeks, reasons below
Confidence and Effort are ASSUMPTIONS, not data. They are written out with their
reasons so anyone can challenge them, and docs/decision_log.md records who made them.

Run from the project folder:
    .venv/bin/python scripts/04_prioritize.py
"""

import os
import textwrap
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
os.chdir(PROJECT_ROOT)

# --- Judgment inputs (the part data can't supply) ----------------------------------
CONFIDENCE = {"high": 1.0, "medium": 0.8, "low": 0.5}
JUDGMENT = pd.DataFrame([
    # fix_id, confidence, effort (person-weeks), reasoning
    ("A", "high", 1,
     "Changes one number in the promise rules; First Class always ships in exactly 2 days."),
    ("B", "low", 4,
     "Checkout, pricing and finance sign-off; no shipping-fee data, so the revenue effect is unknown."),
    ("C", "medium", 6,
     "New delivery-window logic plus UI in checkout, emails and tracking; OTD gain is certain, "
     "but the effect on conversion is unknown."),
    ("D", "medium", 2,
     "Rename plus a promise change; renaming may reduce demand for the premium tier."),
], columns=["fix_id", "confidence", "effort_weeks", "reasoning"])

# --- Data inputs ----------------------------------------------------------------------
con = duckdb.connect()
con.execute(Path("sql/00_views.sql").read_text())
scenarios = con.sql(Path("sql/p4_fix_scenarios.sql").read_text()).df()
scenarios.to_csv(TABLE_DIR / "p4_fix_scenarios.csv", index=False)

rice = scenarios[scenarios["fix_id"] != "ALL"].merge(JUDGMENT, on="fix_id")
rice["rice_score"] = (rice["extra_on_time_orders_per_month"]
                      * rice["confidence"].map(CONFIDENCE) / rice["effort_weeks"]).round(1)
rice = rice.sort_values("rice_score", ascending=False).reset_index(drop=True)
rice.insert(0, "rank", rice.index + 1)
rice.to_csv(TABLE_DIR / "p4_rice_ranking.csv", index=False)

pd.set_option("display.width", 200)
print("RICE RANKING")
print(rice[["rank", "fix_id", "fix_name", "reach_orders_per_month", "extra_on_time_orders_per_month",
            "confidence", "effort_weeks", "rice_score", "promise_longer_by_days"]].to_string(index=False))

# --- Cumulative impact, adding fixes in rank order ------------------------------------------
# Fixes interact: Merging Second Class (B) helps more once Standard has a 6-day
# window (C). So we replay orders with fixes stacked in rank order, rather than
# adding up the one-at-a-time numbers.
NEW_PROMISE = {  # what each fix sets, for the mode(s) it touches
    "A": {"First Class": 2},
    "C": {"Standard Class": 6},
    "D": {"Same Day": 1},
    "B": {"Second Class": "Standard Class"},  # Second Class takes Standard's promise
}
orders = con.sql("SELECT shipping_mode, days_scheduled, days_actual FROM orders").df()
promise = orders.set_index("shipping_mode")["days_scheduled"].groupby(level=0).first().to_dict()

steps = [("Today", 100 * (orders["days_actual"] <= orders["days_scheduled"]).mean(),
          orders["days_scheduled"].mean())]
for fix_id in rice["fix_id"]:
    for mode, value in NEW_PROMISE[fix_id].items():
        promise[mode] = promise[value] if isinstance(value, str) else value
    new = orders["shipping_mode"].map(promise)
    steps.append((fix_id, 100 * (orders["days_actual"] <= new).mean(), new.mean()))
cumulative = pd.DataFrame(steps, columns=["step", "overall_otd_pct", "avg_promise_days"]).round(2)
cumulative["avg_actual_days"] = round(orders["days_actual"].mean(), 2)
cumulative.to_csv(TABLE_DIR / "p4_cumulative_impact.csv", index=False)
print("\nCUMULATIVE (fixes added in rank order)")
print(cumulative.to_string(index=False))

# --- Chart: waterfall of OTD gains -----------------------------------------------------------
INK, INK_MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BASE_COLOR, GAIN_COLOR = "#9a9993", "#2a78d6"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.edgecolor": GRID, "axes.labelcolor": INK_MUTED, "xtick.color": INK_MUTED, "ytick.color": INK_MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
})
names = dict(zip(rice["fix_id"], rice["fix_name"]))
otd = cumulative["overall_otd_pct"].tolist()
labels = (["Today"] + [textwrap.fill(f"{fid}. {names[fid]}", 18) for fid in rice["fix_id"]]
          + ["After all fixes"])

fig, ax = plt.subplots(figsize=(11, 5.2))
x = range(len(labels))
ax.bar(0, otd[0], color=BASE_COLOR, width=0.62)
for i in range(1, len(otd)):
    ax.bar(i, otd[i] - otd[i - 1], bottom=otd[i - 1], color=GAIN_COLOR, width=0.62)
    ax.text(i, otd[i] + 1.5, f"+{otd[i] - otd[i - 1]:.1f} pts", ha="center", fontsize=9, color=INK,
            fontweight="bold")
    p_before, p_after = cumulative["avg_promise_days"].iloc[i - 1], cumulative["avg_promise_days"].iloc[i]
    ax.text(i, otd[i - 1] - 4, f"promise +{p_after - p_before:.2f}d", ha="center", va="top",
            fontsize=8, color=INK_MUTED)
ax.bar(len(otd), otd[-1], color=GAIN_COLOR, width=0.62)
ax.text(0, otd[0] + 1.5, f"{otd[0]:.1f}%", ha="center", fontsize=9, color=INK, fontweight="bold")
ax.text(len(otd), otd[-1] + 1.5, f"{otd[-1]:.1f}%", ha="center", fontsize=9, color=INK, fontweight="bold")
ax.axhline(90, color=INK_MUTED, linestyle="--", linewidth=1)
ax.text(-0.3, 91.5, "Target 90%", color=INK_MUTED, fontsize=9)
ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylim(0, 110)
ax.set_ylabel("Overall on-time delivery (%)")
ax.grid(axis="x", visible=False)
ax.set_title("The top two fixes alone take on-time delivery from 43% to 82%", pad=24)
ax.text(0, 1.02, "Fixes added in RICE rank order · grey note = how much longer the average promise gets"
        f" (actual shipping stays {cumulative['avg_actual_days'].iloc[0]:.1f} days)",
        transform=ax.transAxes, color=INK_MUTED, fontsize=9)
path = FIG_DIR / "fig5_fix_waterfall.png"
fig.savefig(path, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"\nchart -> {path.relative_to(PROJECT_ROOT)}")
