-- Q5. What promise would hit the 90% OTD target?
-- For each mode and each candidate promise P (0-6 days), the OTD we WOULD get
-- if we promised P days: share of orders with days_actual <= P.
-- This is a cumulative distribution, computed with a window SUM.

WITH dist AS (
    SELECT shipping_mode, days_actual, COUNT(*) AS n
    FROM orders
    GROUP BY shipping_mode, days_actual
),
candidates AS (
    SELECT m.shipping_mode, p.promise_days
    FROM (SELECT DISTINCT shipping_mode FROM orders) m
    CROSS JOIN range(0, 7) p(promise_days)
)
SELECT
    c.shipping_mode,
    c.promise_days,
    ROUND(100 * SUM(CASE WHEN d.days_actual <= c.promise_days THEN d.n ELSE 0 END)
          / SUM(d.n), 1) AS otd_if_promised_pct
FROM candidates c
JOIN dist d USING (shipping_mode)
GROUP BY c.shipping_mode, c.promise_days
ORDER BY c.shipping_mode, c.promise_days;
