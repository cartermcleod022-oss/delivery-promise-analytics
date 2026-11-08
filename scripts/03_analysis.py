"""
Phase 3: Answer the business questions (Q1-Q6) with SQL, then chart the results.

How it's organized:
  sql/00_views.sql    shared views: `items` (per item) and `orders` (per shipped order)
  sql/qN_*.sql        one query per business question
  This script runs each query with DuckDB, saves the result to outputs/tables/,
  and draws the charts in outputs/figures/.

Keeping the SQL in .sql files (instead of strings in Python) means each query
can be read, reviewed and reused on its own.

Run from the project folder:
    .venv/bin/python scripts/03_analysis.py
"""

import math
import os
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")  # draw straight to files; no window needed
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

OTD_TARGET = 90  # approved in Phase 2

# --- Chart style --------------------------------------------------------------------
# One fixed color per shipping mode, used in EVERY chart, so a reader learns it once.
# Colors come from a palette checked for color-blind readability.
MODE_ORDER = ["Same Day", "First Class", "Second Class", "Standard Class"]
MODE_COLOR = {
    "First Class": "#2a78d6",     # blue
    "Second Class": "#eb6834",    # orange
    "Same Day": "#1baf7a",        # aqua
    "Standard Class": "#eda100",  # yellow
}
INK, INK_MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
ON_TIME_COLOR, LATE_COLOR = "#2a78d6", "#eb6834"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.edgecolor": GRID, "axes.labelcolor": INK_MUTED, "xtick.color": INK_MUTED, "ytick.color": INK_MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "legend.frameon": False,
})


def title(ax, main, sub):
    """Bold title with a muted subtitle underneath (pad leaves room for it)."""
    ax.set_title(main, pad=24)
    ax.text(0, 1.02, sub, transform=ax.transAxes, color=INK_MUTED, fontsize=9)


def save(fig, name):
    path = FIG_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  chart -> {path.relative_to(PROJECT_ROOT)}")


# --- Run the SQL ------------------------------------------------------------------------
# The views read 'data/processed/...' as a relative path, so run from the project root.
os.chdir(PROJECT_ROOT)
con = duckdb.connect()
con.execute((SQL_DIR / "00_views.sql").read_text())

results = {}
for sql_file in sorted(SQL_DIR.glob("q*.sql")):
    df = con.sql(sql_file.read_text()).df()
    results[sql_file.stem] = df
    df.to_csv(TABLE_DIR / f"{sql_file.stem}.csv", index=False)
    print(f"{sql_file.name}: {len(df)} rows -> outputs/tables/{sql_file.stem}.csv")


# --- Q1: OTD over time -------------------------------------------------------------------
q1 = results["q1_otd_trend"]
allm = q1[q1["shipping_mode"] == "All modes"]
print(f"\nQ1  Overall OTD by month ranges {allm.otd_pct.min()}% to {allm.otd_pct.max()}% "
      f"(average {allm.otd_pct.mean():.1f}%)")

fig, ax = plt.subplots(figsize=(10, 5))
for mode in MODE_ORDER:
    d = q1[q1["shipping_mode"] == mode]
    ax.plot(d["order_month"], d["otd_pct"], color=MODE_COLOR[mode], linewidth=2)
    ax.annotate(mode, (d["order_month"].iloc[-1], d["otd_pct"].iloc[-1]), xytext=(6, 0),
                textcoords="offset points", va="center", color=INK, fontsize=9)
ax.plot(allm["order_month"], allm["otd_pct"], color=INK, linewidth=2.5)
ax.annotate("All modes", (allm["order_month"].iloc[-1], allm["otd_pct"].iloc[-1]), xytext=(6, 0),
            textcoords="offset points", va="center", color=INK, fontsize=9, fontweight="bold")
ax.axhline(OTD_TARGET, color=INK_MUTED, linestyle="--", linewidth=1)
ax.text(allm["order_month"].iloc[0], OTD_TARGET + 2, f"Target {OTD_TARGET}%", color=INK_MUTED, fontsize=9)
ax.set_ylim(-3, 105)
ax.set_ylabel("On-time delivery (% of shipped orders)")
title(ax, "On-time delivery has been flat at ~43% for three years",
      "Monthly OTD by shipping mode, Jan 2015 to Jan 2018")
save(fig, "fig1_otd_by_month.png")


# --- Q2 + Q3: promise vs. reality, per mode ----------------------------------------------------
q2 = results["q2_mode_promise"]
print("\nQ2  Promise performance by mode")
print(q2.to_string(index=False))

q3 = results["q3_actual_days_dist"]
fig, axes = plt.subplots(1, 4, figsize=(12, 3.8), sharey=True)
for ax, mode in zip(axes, MODE_ORDER):
    # Fill in days with no orders as 0% so every panel shows days 0-6.
    pct = (q3[q3["shipping_mode"] == mode].set_index("days_actual")["pct_of_mode"]
           .reindex(range(7), fill_value=0))
    promised = int(q3.loc[q3["shipping_mode"] == mode, "promised_days"].iloc[0])
    colors = [ON_TIME_COLOR if day <= promised else LATE_COLOR for day in pct.index]
    ax.bar(pct.index, pct.values, color=colors, width=0.8)
    ax.axvline(promised + 0.5, color=INK, linestyle="--", linewidth=1)
    ax.text(promised + 0.6, 111, f"promise: {promised}d", fontsize=8, color=INK, va="top")
    otd = q2.loc[q2["shipping_mode"] == mode, "otd_pct"].iloc[0]
    ax.set_title(f"{mode}\n{otd:.0f}% on time", fontsize=10)
    ax.set_xticks(range(7))
    ax.set_xlabel("Actual days to ship")
    ax.grid(axis="x", visible=False)
axes[0].set_ylabel("% of the mode's orders")
axes[0].set_ylim(0, 113)
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=ON_TIME_COLOR), plt.Rectangle((0, 0), 1, 1, color=LATE_COLOR)],
           labels=["On time or early", "Late"], loc="upper right", ncol=2, bbox_to_anchor=(1, 1.0))
fig.suptitle("Second Class takes exactly as long as Standard, but promises 2 days instead of 4",
             x=0.01, ha="left", y=0.99, fontweight="bold", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "fig2_actual_vs_promised.png")


# --- Q4: what drives lateness? ----------------------------------------------------------------
q4 = results["q4_late_spread"]
spread = q4.groupby("dimension")["late_pct"].agg(["min", "max"])
spread["range"] = spread["max"] - spread["min"]
spread = spread.sort_values("range")
print("\nQ4  Late-rate spread (max - min, percentage points) by dimension")
print(spread.round(1).to_string())

fig, ax = plt.subplots(figsize=(9, 4.5))
for i, dim in enumerate(spread.index):
    d = q4[q4["dimension"] == dim]
    highlight = dim == "Shipping mode"
    color = MODE_COLOR["First Class"] if highlight else INK_MUTED
    ax.hlines(i, spread.loc[dim, "min"], spread.loc[dim, "max"], color=color, linewidth=2)
    ax.scatter(d["late_pct"], [i] * len(d), color=color, s=36, zorder=3, edgecolor=SURFACE, linewidth=1.5)
    ax.text(spread.loc[dim, "max"] + 1.5, i, f"{spread.loc[dim, 'range']:.0f} pts", va="center",
            fontsize=9, color=INK, fontweight="bold" if highlight else "normal")
ax.set_yticks(range(len(spread)))
ax.set_yticklabels(spread.index)
ax.set_xlim(30, 112)
ax.set_xlabel("Late rate of each group (%)  ·  one dot per group")
ax.grid(axis="y", visible=False)
title(ax, "Only the shipping mode moves the late rate",
      "Late rate across groups within each dimension (spread = highest minus lowest group)")
save(fig, "fig3_late_rate_by_dimension.png")


# --- Q5: what promise would reach 90% OTD? ------------------------------------------------------
q5 = results["q5_promise_calibration"]
needed = (q5[q5["otd_if_promised_pct"] >= OTD_TARGET]
          .groupby("shipping_mode")["promise_days"].min()
          .rename("promise_for_target").reset_index())
calib = q2[["shipping_mode", "orders", "promised_days", "otd_pct"]].merge(needed, on="shipping_mode")
calib = calib.set_index("shipping_mode").loc[MODE_ORDER].reset_index()
# OTD if every mode used its new promise. All modes reach 100% here because the
# distributions are discrete, so the smallest promise above 90% is also the maximum.
new_otd = q5.merge(needed, left_on=["shipping_mode", "promise_days"],
                   right_on=["shipping_mode", "promise_for_target"])
new_otd = new_otd.merge(q2[["shipping_mode", "orders"]], on="shipping_mode")
overall_new = (new_otd["otd_if_promised_pct"] * new_otd["orders"]).sum() / new_otd["orders"].sum()
calib.to_csv(TABLE_DIR / "q5_recommended_promises.csv", index=False)
print(f"\nQ5  Smallest promise (days) that reaches {OTD_TARGET}% OTD, per mode")
print(calib.to_string(index=False))
print(f"    Overall OTD if all modes used these promises: {overall_new:.1f}%")

fig, ax = plt.subplots(figsize=(9, 5))
# Second Class sits exactly on top of Standard, so draw it last and dashed.
for mode in ["Same Day", "First Class", "Standard Class", "Second Class"]:
    d = q5[q5["shipping_mode"] == mode]
    ax.plot(d["promise_days"], d["otd_if_promised_pct"], color=MODE_COLOR[mode], linewidth=2,
            linestyle="--" if mode == "Second Class" else "-",
            marker="o", markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5, label=mode)
    cur = calib.loc[calib["shipping_mode"] == mode].iloc[0]
    ax.scatter(cur["promised_days"], cur["otd_pct"], s=140, facecolor="none", edgecolor=MODE_COLOR[mode],
               linewidth=2, zorder=4)
ax.axhline(OTD_TARGET, color=INK_MUTED, linestyle="--", linewidth=1)
ax.text(0, OTD_TARGET + 2, f"Target {OTD_TARGET}%", color=INK_MUTED, fontsize=9)
ax.set_xlabel("Promised days")
ax.set_ylabel("On-time delivery if we promised this (%)")
ax.set_xticks(range(7))
ax.set_ylim(-3, 108)
ax.legend(loc="lower right")
title(ax, "Hitting 90% on time needs a 6-day promise for Second Class and Standard",
      "OTD each mode would achieve at each promise · open circle = today's promise")
ax.annotate("Second Class and Standard\nfollow the same curve", xy=(4, 60), xytext=(4.4, 30),
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK_MUTED))
save(fig, "fig4_promise_calibration.png")


# --- Q6: repeat purchase after a late first order ---------------------------------------------
# A two-proportion z-test asks: if lateness made NO difference, how surprising would
# a gap this big be? A p-value above 0.05 means "not surprising, no evidence of an effect".
q6 = results["q6_repeat_purchase"].set_index("first_order")
n1, x1 = q6.loc["Late", "customers"], q6.loc["Late", "repurchased"]
n2, x2 = q6.loc["On time", "customers"], q6.loc["On time", "repurchased"]
p1, p2 = x1 / n1, x2 / n2
pooled = (x1 + x2) / (n1 + n2)
z = (p1 - p2) / math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
p_value = math.erfc(abs(z) / math.sqrt(2))  # two-sided
print("\nQ6  90-day repurchase after the customer's FIRST order")
print(q6.to_string())
print(f"    Difference (late - on time): {100 * (p1 - p2):+.1f} pts   z = {z:.2f}   p = {p_value:.2f}")
