-- Q1. How often do we break our delivery promise, and is it changing over time?
-- OTD (on-time delivery rate) = share of shipped orders with is_late = 0.
-- One row per month per shipping mode, plus an 'All modes' row per month.

SELECT
    order_month,
    COALESCE(shipping_mode, 'All modes')      AS shipping_mode,
    COUNT(*)                                   AS orders,
    ROUND(100 * AVG(1 - is_late), 1)           AS otd_pct
FROM orders
GROUP BY GROUPING SETS ((order_month, shipping_mode), (order_month))
ORDER BY order_month, shipping_mode;
