"""
Phase 6: Export one tidy, order-level CSV for building the dashboard in Tableau Public.

One row per shipped order, with readable column names. Tableau does the aggregating;
see docs/tableau_guide.md for the step-by-step build.

Run from the project folder:
    .venv/bin/python scripts/07_export_tableau.py
"""

import os
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT = PROJECT_ROOT / "tableau" / "orders_for_tableau.csv"
os.chdir(PROJECT_ROOT)

con = duckdb.connect()
con.execute(Path("sql/00_views.sql").read_text())
OUT.parent.mkdir(exist_ok=True)
con.execute(f"""
    COPY (
        SELECT
            order_id                        AS "Order ID",
            CAST(order_date AS DATE)        AS "Order Date",
            shipping_mode                   AS "Shipping Mode",
            days_scheduled                  AS "Promised Days",
            days_actual                     AS "Actual Days",
            CAST(days_late AS INTEGER)      AS "Days Late",
            CAST(1 - is_late AS INTEGER)    AS "On Time",
            market                          AS "Market",
            order_region                    AS "Region",
            customer_segment                AS "Customer Segment",
            ROUND(order_sales, 2)           AS "Sales",
            ROUND(order_profit, 2)          AS "Profit"
        FROM orders
        ORDER BY order_date, order_id
    ) TO '{OUT.relative_to(PROJECT_ROOT)}' (HEADER, DELIMITER ',')
""")
n = con.sql(f"SELECT COUNT(*), ROUND(100 * AVG(\"On Time\"), 1) FROM '{OUT.relative_to(PROJECT_ROOT)}'").fetchall()[0]
print(f"Wrote {OUT.relative_to(PROJECT_ROOT)}: {n[0]:,} orders, on-time {n[1]}% "
      f"({OUT.stat().st_size / 1e6:.1f} MB)")
