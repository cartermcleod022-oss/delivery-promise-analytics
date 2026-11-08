-- Phase 5: The delivery-window rule the feature would use, derived from history.
--
-- For each shipping mode:
--   window_start  = earliest actual shipping time seen (what we show as "as soon as")
--   typical_days  = median actual shipping time
--   commit_days   = smallest number of days that covers >= 90% of orders
--                   (the date we promise and measure OTD against)
-- In production this would be recomputed regularly (e.g. weekly, on a rolling
-- 90 days of orders) so the window tracks real fulfillment.

WITH dist AS (
    SELECT shipping_mode, days_actual, COUNT(*) AS n
    FROM orders
    GROUP BY shipping_mode, days_actual
),
cumulative AS (
    SELECT
        shipping_mode,
        days_actual,
        SUM(n) OVER (PARTITION BY shipping_mode ORDER BY days_actual)
            / SUM(n) OVER (PARTITION BY shipping_mode)              AS share_by_day
    FROM dist
)
SELECT
    c.shipping_mode,
    ANY_VALUE(o.days_scheduled)                                     AS current_promise,
    MIN(c.days_actual)                                              AS window_start,
    (SELECT MEDIAN(days_actual) FROM orders o2
      WHERE o2.shipping_mode = c.shipping_mode)                     AS typical_days,
    MIN(CASE WHEN c.share_by_day >= 0.90 THEN c.days_actual END)    AS commit_days,
    ROUND(100 * MIN(CASE WHEN c.share_by_day >= 0.90 THEN c.share_by_day END), 1)
                                                                    AS otd_at_commit_pct
FROM cumulative c
JOIN (SELECT DISTINCT shipping_mode, days_scheduled FROM orders) o USING (shipping_mode)
GROUP BY c.shipping_mode
ORDER BY current_promise;
