"""
Phase 2: Clean the DataCo dataset.

Input : data/raw/DataCoSupplyChainDataset.csv  (raw Kaggle file, 53 columns)
Output: data/processed/order_items.parquet      (one row per order item, tidy columns)

Every decision below traces back to a finding in docs/phase1_findings.md.

Run from the project folder:
    .venv/bin/python scripts/02_clean.py
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_PATH = OUT_DIR / "order_items.parquet"

# Orders from this month onward arrive at less than half the earlier volume.
# We don't know why yet, so we flag these rows instead of deleting them.
LOW_VOLUME_START = "2017-10-01"

df = pd.read_csv(RAW_PATH, encoding="latin-1")
print(f"Loaded raw file: {df.shape[0]:,} rows x {df.shape[1]} columns")

# --- 1. Drop columns we don't want ---------------------------------------------
# Some raw column names have trailing spaces (e.g. "Days for shipping (real)  "),
# so we strip them first to make the names predictable.
df.columns = df.columns.str.strip()

DROP = [
    # Exact duplicates of another column (verified in Phase 1)
    "Benefit per order",         # = Order Profit Per Order
    "Sales per customer",        # = Order Item Total
    "Order Item Product Price",  # = Product Price
    "Order Customer Id",         # = Customer Id
    "Product Category Id",       # = Category Id
    "Order Item Cardprod Id",    # = Product Card Id
    # Empty, mostly empty or constant
    "Product Description",       # 100% missing
    "Order Zipcode",             # 86% missing
    "Product Status",            # always 0, so it carries no information
    # Personal or masked data we don't need
    "Customer Email", "Customer Password", "Customer Fname",
    "Customer Lname", "Customer Street", "Customer Zipcode",
    # Not useful for analysis
    "Product Image",             # a URL
]
df = df.drop(columns=DROP)

# --- 2. Rename to snake_case -----------------------------------------------------
# Short lowercase names are easier to type in Python AND in SQL
# (no quotes needed around names with spaces or parentheses).
RENAME = {
    "Type": "payment_type",
    "Days for shipping (real)": "days_actual",
    "Days for shipment (scheduled)": "days_scheduled",
    "Delivery Status": "delivery_status",
    "Late_delivery_risk": "late_flag_raw",
    "Category Id": "category_id",
    "Category Name": "category_name",
    "Customer City": "customer_city",
    "Customer Country": "customer_country",
    "Customer Id": "customer_id",
    "Customer Segment": "customer_segment",
    "Customer State": "customer_state",
    "Department Id": "department_id",
    "Department Name": "department_name",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Market": "market",
    "Order City": "order_city",
    "Order Country": "order_country",
    "order date (DateOrders)": "order_date",
    "Order Id": "order_id",
    "Order Item Discount": "item_discount",
    "Order Item Discount Rate": "item_discount_rate",
    "Order Item Id": "order_item_id",
    "Order Item Profit Ratio": "item_profit_ratio",
    "Order Item Quantity": "item_quantity",
    "Sales": "item_sales_gross",       # price x quantity, before discount
    "Order Item Total": "item_sales_net",  # after discount
    "Order Profit Per Order": "item_profit",  # despite the name, it's per item
    "Order Region": "order_region",
    "Order State": "order_state",
    "Order Status": "order_status",
    "Product Card Id": "product_id",
    "Product Name": "product_name",
    "Product Price": "product_price",
    "shipping date (DateOrders)": "shipping_date",
    "Shipping Mode": "shipping_mode",
}
# Fail loudly if we forgot a column. Better to find out now than in Phase 3.
missing = set(df.columns) - set(RENAME)
assert not missing, f"Columns without a new name: {missing}"
df = df.rename(columns=RENAME)

# --- 3. Fix types -------------------------------------------------------------------
# Dates arrive as text like "1/31/2018 22:56". Converting them lets us
# group by month, compute gaps, etc.
for col in ["order_date", "shipping_date"]:
    df[col] = pd.to_datetime(df[col], format="%m/%d/%Y %H:%M")

df["product_name"] = df["product_name"].str.strip()

# --- 4. Add the columns our KPIs are built on ---------------------------------------
# A shipment is "canceled" when the order was canceled or flagged as fraud.
# These never shipped, so they can't be on time or late.
df["is_canceled"] = df["delivery_status"].eq("Shipping canceled")

# is_late: our own definition, so it's transparent and testable.
#   1 = took longer than promised, 0 = on time or early, missing = canceled.
# "Int8" (capital I) is pandas' integer type that allows missing values.
df["is_late"] = (df["days_actual"] > df["days_scheduled"]).astype("Int8")
df.loc[df["is_canceled"], "is_late"] = pd.NA

# How many days late (positive) or early (negative).
df["days_late"] = df["days_actual"] - df["days_scheduled"]
df.loc[df["is_canceled"], "days_late"] = pd.NA

# Calendar helpers for trend analysis.
df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
df["order_weekday"] = df["order_date"].dt.day_name()
df["is_low_volume_period"] = df["order_date"] >= LOW_VOLUME_START

# --- 5. Validate ----------------------------------------------------------------------
# Checks that guard our assumptions. If one fails, the script stops.
assert df["order_item_id"].is_unique, "order_item_id should identify each row"
# Our is_late should match the dataset's own late flag for every shipped item.
shipped = df[~df["is_canceled"]]
assert (shipped["is_late"] == shipped["late_flag_raw"]).all(), "is_late disagrees with raw flag"

print("\nVALIDATION")
print("  order_item_id is unique: OK")
print("  is_late matches raw late flag on all shipped items: OK")
# The gap between the two date columns should equal days_actual. Where it doesn't,
# print by how much, so we know whether it matters.
gap_days = (df["shipping_date"] - df["order_date"]).dt.days
diff = (df["days_actual"] - gap_days)
print(f"  shipping_date - order_date == days_actual on {(diff == 0).mean():.1%} of rows")
print(f"  where they differ, days_actual minus date gap is: {diff[diff != 0].value_counts().to_dict()}")

# --- 6. Save --------------------------------------------------------------------------
OUT_DIR.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT_PATH, index=False)

print(f"\nSaved {df.shape[0]:,} rows x {df.shape[1]} columns to {OUT_PATH.relative_to(PROJECT_ROOT)}")
print(f"  shipped items: {(~df['is_canceled']).sum():,}   canceled: {df['is_canceled'].sum():,}")
print(f"  low-volume period rows (from {LOW_VOLUME_START}): {df['is_low_volume_period'].sum():,}")
print("\nFINAL COLUMNS")
print(df.dtypes.astype(str).to_string())
