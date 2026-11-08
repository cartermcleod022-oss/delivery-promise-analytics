-- Q1 (persona): Who picks each shipping mode, and how much do they spend?
-- Look for: does First Class attract bigger orders or a particular segment?
-- Try next: swap customer_segment for market, or join items to see categories.

SELECT
    shipping_mode,
    customer_segment,
    COUNT(*)                     AS orders,
    ROUND(AVG(order_sales), 0)   AS avg_order_value
FROM orders
GROUP BY shipping_mode, customer_segment
ORDER BY shipping_mode, orders DESC;
