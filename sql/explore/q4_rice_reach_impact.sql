-- Q4 (RICE): Reach and Impact for one fix: re-promising First Class to 2 days.
-- Reach  = how many orders the fix touches.
-- Impact = how much OVERALL on-time delivery rises if we make the change.
-- To score another fix, copy this file and edit the CASE line, e.g.
--   WHEN shipping_mode = 'Standard Class' THEN 6

WITH scenario AS (
    SELECT
        *,
        CASE WHEN shipping_mode = 'First Class' THEN 2   -- <-- the fix
             ELSE days_scheduled END                    AS new_promise
    FROM orders
)
SELECT
    SUM(CASE WHEN new_promise <> days_scheduled THEN 1 ELSE 0 END)          AS reach_orders,
    ROUND(100 * AVG(CASE WHEN days_actual <= days_scheduled THEN 1 ELSE 0 END), 1) AS otd_today_pct,
    ROUND(100 * AVG(CASE WHEN days_actual <= new_promise   THEN 1 ELSE 0 END), 1) AS otd_after_fix_pct
FROM scenario;
