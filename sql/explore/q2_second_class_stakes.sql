-- Q2 (Second Class): How much business rides on Second Class?
-- Look for: its share of orders, sales and profit. That's what's at risk
-- if you merge or discount it.
-- Note: the data has NO shipping-fee column, so we can't see what customers
-- pay for Second Class itself. Say this in your reasoning.

SELECT
    shipping_mode,
    COUNT(*)                                                    AS orders,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS pct_orders,
    ROUND(100 * SUM(order_sales) / SUM(SUM(order_sales)) OVER (), 1)  AS pct_sales,
    ROUND(100 * SUM(order_profit) / SUM(SUM(order_profit)) OVER (), 1) AS pct_profit
FROM orders
GROUP BY shipping_mode
ORDER BY orders DESC;
