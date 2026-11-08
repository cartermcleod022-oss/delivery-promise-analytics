-- Q3. Are premium shipping modes actually faster?
-- Distribution of actual shipping days per mode: what share of each mode's
-- orders took 0, 1, 2 ... 6 days.

SELECT
    shipping_mode,
    days_actual,
    ANY_VALUE(days_scheduled)                                          AS promised_days,
    COUNT(*)                                                           AS orders,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY shipping_mode), 1) AS pct_of_mode
FROM orders
GROUP BY shipping_mode, days_actual
ORDER BY shipping_mode, days_actual;
