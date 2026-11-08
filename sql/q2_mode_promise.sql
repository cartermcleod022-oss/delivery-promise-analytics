-- Q2. Which shipping modes break the promise most, and by how much?
-- promise_gap = actual days - promised days (positive = late).

SELECT
    shipping_mode,
    COUNT(*)                                            AS orders,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)    AS pct_of_orders,
    ANY_VALUE(days_scheduled)                           AS promised_days,
    ROUND(AVG(days_actual), 2)                          AS avg_actual_days,
    ROUND(AVG(days_late), 2)                            AS avg_promise_gap,
    ROUND(100 * AVG(1 - is_late), 1)                    AS otd_pct,
    ROUND(100 * AVG(CASE WHEN days_late >= 2 THEN 1 ELSE 0 END), 1) AS severe_late_pct
FROM orders
GROUP BY shipping_mode
ORDER BY otd_pct;
