-- Phase 4: What would each fix do to on-time delivery (OTD)?
--
-- Each fix = a new promise for one or more shipping modes. We replay every
-- historical order against the new promise and count how many would have been
-- on time. Actual shipping days stay the same, because these fixes change the
-- PROMISE, not the speed. That's why we also report how much longer the promise
-- gets: the honest cost of each fix.
--
-- Fixes A-D are scored one at a time against today's promises.
-- 'ALL' applies all four together (B and C combined means Second Class
-- orders get Standard's new 6-day window).

WITH fixes(fix_id, fix_name, shipping_mode, new_promise) AS (
    VALUES
    ('A',   'First Class: promise 2 days',          'First Class',    2),
    ('B',   'Merge Second Class into Standard',     'Second Class',   4),
    ('C',   'Standard: show a 2-6 day window',      'Standard Class', 6),
    ('D',   'Rename Same Day to Next Day (1 day)',  'Same Day',       1),
    ('ALL', 'All four fixes together',              'First Class',    2),
    ('ALL', 'All four fixes together',              'Second Class',   6),
    ('ALL', 'All four fixes together',              'Standard Class', 6),
    ('ALL', 'All four fixes together',              'Same Day',       1)
),
totals AS (
    SELECT
        COUNT(*)                           AS all_orders,
        SUM(1 - is_late)                   AS on_time_today,
        COUNT(DISTINCT order_month)        AS months
    FROM orders
),
affected AS (
    -- Every order touched by a fix, with on-time status before and after.
    SELECT
        f.fix_id,
        f.fix_name,
        o.days_scheduled                                        AS old_promise,
        f.new_promise,
        1 - o.is_late                                           AS on_time_before,
        CASE WHEN o.days_actual <= f.new_promise THEN 1 ELSE 0 END AS on_time_after
    FROM fixes f
    JOIN orders o USING (shipping_mode)
)
SELECT
    a.fix_id,
    a.fix_name,
    -- Reach: orders the fix touches, per month on average
    ROUND(COUNT(*) / t.months, 0)                                   AS reach_orders_per_month,
    -- Impact on the affected orders
    ROUND(100 * AVG(a.on_time_before), 1)                           AS affected_otd_before_pct,
    ROUND(100 * AVG(a.on_time_after), 1)                            AS affected_otd_after_pct,
    -- Extra on-time orders per month = Reach x Impact, in one interpretable number
    ROUND(SUM(a.on_time_after - a.on_time_before) / t.months, 0)    AS extra_on_time_orders_per_month,
    -- Company-wide OTD if only this fix shipped
    ROUND(100 * t.on_time_today / t.all_orders, 1)                  AS overall_otd_today_pct,
    ROUND(100 * (t.on_time_today + SUM(a.on_time_after - a.on_time_before))
          / t.all_orders, 1)                                        AS overall_otd_after_pct,
    -- The cost: how many days longer the promise gets for affected orders
    ROUND(AVG(a.new_promise - a.old_promise), 2)                    AS promise_longer_by_days
FROM affected a, totals t
GROUP BY a.fix_id, a.fix_name, t.months, t.on_time_today, t.all_orders
ORDER BY a.fix_id;
