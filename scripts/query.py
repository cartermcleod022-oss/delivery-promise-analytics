"""
Run any SQL against the project data and print the result.

The `items` and `orders` views from sql/00_views.sql are loaded first,
so you can query them straight away.

Usage (from the project folder):
    .venv/bin/python scripts/query.py "SELECT shipping_mode, COUNT(*) FROM orders GROUP BY 1"
    .venv/bin/python scripts/query.py sql/explore/my_query.sql
"""

import os
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if len(sys.argv) != 2:
    sys.exit(__doc__)

arg = sys.argv[1]
# If the argument is a path to a .sql file, read the query from it.
sql = Path(arg).read_text() if arg.endswith(".sql") else arg

os.chdir(PROJECT_ROOT)  # the views use paths relative to the project folder
con = duckdb.connect()
con.execute((PROJECT_ROOT / "sql" / "00_views.sql").read_text())
con.sql(sql).show(max_rows=100, max_width=200)
