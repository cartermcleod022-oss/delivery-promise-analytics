"""
Phase 1: First look at the DataCo Smart Supply Chain dataset.

Goal: understand what is in the data BEFORE asking business questions.
We answer: How big is it? What columns exist? What types are they?
Where is data missing? What looks suspicious?

Run from the project folder:
    .venv/bin/python scripts/01_first_look.py
"""

from pathlib import Path

import pandas as pd

# --- 1. Locate the file -------------------------------------------------------
# Path(__file__) is this script's location; .parent.parent is the project root.
# Building paths this way means the script works no matter where you run it from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"

# --- 2. Load it ---------------------------------------------------------------
# ASSUMPTION: the file is not UTF-8 (it contains accented characters saved in
# the older "latin-1" encoding). Reading it as UTF-8 would crash, so we say so.
df = pd.read_csv(CSV_PATH, encoding="latin-1")

# --- 3. Size ------------------------------------------------------------------
print("=" * 70)
print(f"Rows: {len(df):,}   Columns: {df.shape[1]}")
print("=" * 70)

# --- 4. Column-by-column profile ----------------------------------------------
# For every column we collect: its type, how many values are missing,
# how many distinct values it has, and one example value.
profile = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "missing": df.isna().sum(),
    "missing_%": (df.isna().mean() * 100).round(1),
    "unique": df.nunique(),
    "example": df.iloc[0],
})
pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)
pd.set_option("display.max_colwidth", 40)
print("\nCOLUMN PROFILE")
print(profile.to_string())

# Save the profile so it can become our data dictionary in the repo.
out_path = PROJECT_ROOT / "data" / "column_profile.csv"
profile.to_csv(out_path, index_label="column")
print(f"\nSaved column profile to {out_path.relative_to(PROJECT_ROOT)}")

# --- 5. A first peek at the columns we expect to matter most -------------------
# ASSUMPTION (to verify): these columns describe the late-delivery problem.
print("\nDELIVERY STATUS (share of orders)")
print(df["Delivery Status"].value_counts(normalize=True).round(3).to_string())

print("\nLATE DELIVERY RISK flag (1 = late)")
print(df["Late_delivery_risk"].value_counts(normalize=True).round(3).to_string())

print("\nSHIPPING DAYS: actual vs. scheduled")
print(df[["Days for shipping (real)", "Days for shipment (scheduled)"]].describe().round(2).to_string())

# --- 6. Quick sanity checks ---------------------------------------------------
print("\nSANITY CHECKS")
print(f"Duplicate rows: {df.duplicated().sum():,}")
# Each row should be one item within an order, so order IDs repeat.
print(f"Unique orders: {df['Order Id'].nunique():,}  (rows are order *items*)")
# Does the Late_delivery_risk flag really mean "real days > scheduled days"?
recomputed_late = (df["Days for shipping (real)"] > df["Days for shipment (scheduled)"]).astype(int)
print(f"Late flag matches real > scheduled: {(recomputed_late == df['Late_delivery_risk']).mean():.1%} of rows")
