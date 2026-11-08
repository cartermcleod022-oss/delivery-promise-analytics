-- Q4. Does lateness depend on where, what or who?
-- Late rate for every group of several dimensions, stacked into one long table.
-- Order-level attributes use the orders view. Product attributes (category,
-- department) can differ within one order, so they are measured per item.
-- Groups with fewer than 500 orders/items are dropped as too small to compare.

WITH long AS (
    SELECT 'Shipping mode'    AS dimension, shipping_mode    AS grp, is_late FROM orders UNION ALL
    SELECT 'Market',                         market,                 is_late FROM orders UNION ALL
    SELECT 'Order region',                   order_region,           is_late FROM orders UNION ALL
    SELECT 'Customer segment',               customer_segment,       is_late FROM orders UNION ALL
    SELECT 'Order weekday',                  order_weekday,          is_late FROM orders UNION ALL
    SELECT 'Payment type',                   payment_type,           is_late FROM orders UNION ALL
    SELECT 'Product category (items)',       category_name,          is_late FROM items WHERE NOT is_canceled UNION ALL
    SELECT 'Department (items)',             department_name,        is_late FROM items WHERE NOT is_canceled
)
SELECT
    dimension,
    grp,
    COUNT(*)                         AS n,
    ROUND(100 * AVG(is_late), 1)     AS late_pct
FROM long
GROUP BY dimension, grp
HAVING COUNT(*) >= 500
ORDER BY dimension, late_pct DESC;
