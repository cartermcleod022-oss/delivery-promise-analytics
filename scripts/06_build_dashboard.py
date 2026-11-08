"""
Phase 6: Build the interactive dashboard (dashboard/index.html).

How it works:
  1. SQL aggregates shipped orders to one row per
     (month, shipping mode, region, customer segment, actual shipping days) with an order count.
     That's ~6,500 rows, small enough to embed in the page.
  2. The rows are inserted into dashboard/template.html as JSON.
  3. JavaScript in the page recomputes every KPI and chart from those rows whenever
     a filter or a what-if promise changes. No server needed: the file opens by
     double-click and works on GitHub Pages.

Outputs:
  dashboard/index.html     standalone page (commit this)
  dashboard/.artifact.html same page without the document wrapper, for publishing as an Artifact

Run from the project folder:
    .venv/bin/python scripts/06_build_dashboard.py
"""

import json
import os
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASH_DIR = PROJECT_ROOT / "dashboard"
os.chdir(PROJECT_ROOT)

con = duckdb.connect()
con.execute(Path("sql/00_views.sql").read_text())

# Fixed display order for shipping modes (fastest promise first) and their current promise.
MODES = ["Same Day", "First Class", "Second Class", "Standard Class"]
PROMISE = [int(con.sql(f"SELECT ANY_VALUE(days_scheduled) FROM orders WHERE shipping_mode = '{m}'")
               .fetchall()[0][0]) for m in MODES]

agg = con.sql("""
    SELECT strftime(order_month, '%Y-%m') AS month, shipping_mode, order_region, market,
           customer_segment, days_actual, COUNT(*) AS n
    FROM orders
    GROUP BY ALL
""").df()

# Replace repeated text with small integer codes to keep the embedded data compact.
months = sorted(agg["month"].unique())
regions = sorted(agg["order_region"].unique())
region_market = agg.groupby("order_region")["market"].first().reindex(regions).tolist()
markets = sorted(agg["market"].unique())
segments = sorted(agg["customer_segment"].unique())
idx = lambda values: {v: i for i, v in enumerate(values)}
m_i, mo_i, r_i, s_i = idx(months), idx(MODES), idx(regions), idx(segments)

rows = [[m_i[r.month], mo_i[r.shipping_mode], r_i[r.order_region], s_i[r.customer_segment],
         int(r.days_actual), int(r.n)] for r in agg.itertuples()]

data = {
    "months": months, "modes": MODES, "promise": PROMISE,
    "regions": regions, "regionMarket": region_market, "markets": markets, "segments": segments,
    "rows": rows,  # [monthIdx, modeIdx, regionIdx, segmentIdx, actualDays, orders]
}
assert sum(r[5] for r in rows) == con.sql("SELECT COUNT(*) FROM orders").fetchall()[0][0]

template = (DASH_DIR / "template.html").read_text()
fragment = template.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))

(DASH_DIR / ".artifact.html").write_text(fragment)
(DASH_DIR / "index.html").write_text(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
)
print(f"Embedded {len(rows):,} aggregate rows ({sum(r[5] for r in rows):,} orders)")
print(f"Wrote dashboard/index.html ({(DASH_DIR / 'index.html').stat().st_size / 1024:.0f} KB)")
