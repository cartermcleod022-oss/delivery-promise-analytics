-- Q7 (success metrics): Baselines your PRD metrics will be measured against.
-- Every metric in a PRD needs a "from" number. These are yours.
-- Conversion and shipping revenue are NOT in the data; list them as
-- "to be measured in the A/B test".

SELECT
    COUNT(*)                                                             AS shipped_orders,
    ROUND(100 * AVG(1 - is_late), 1)                                     AS otd_pct,
    ROUND(100 * AVG(CASE WHEN days_late >= 2 THEN 1 ELSE 0 END), 1)      AS severe_late_pct,
    ROUND(AVG(CASE WHEN is_late = 1 THEN days_late END), 2)              AS avg_days_late_when_late,
    ROUND(100 * AVG(CASE WHEN shipping_mode IN ('First Class','Second Class','Same Day')
                         THEN 1 ELSE 0 END), 1)                          AS premium_mode_share_pct
FROM orders;
