-- Q6. Are customers whose order arrived late less likely to order again?
--
-- Design (to avoid two common traps):
--  * Use each customer's FIRST shipped order. Frequent buyers have many orders,
--    so using all orders would mostly measure "who buys often", not "what lateness does".
--  * Only count first orders placed at least 90 days before the data ends.
--    Otherwise a recent customer looks like they "never came back" simply because
--    the data stops (this is called right-censoring).
-- Outcome: placed ANY other order (shipped or not) within 90 days of the first order.

WITH first_orders AS (
    SELECT *
    FROM orders
    QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date, order_id) = 1
),
data_end AS (SELECT MAX(order_date) AS max_date FROM items),
eligible AS (
    SELECT f.*
    FROM first_orders f, data_end
    WHERE f.order_date <= data_end.max_date - INTERVAL 90 DAY
),
outcome AS (
    SELECT
        e.customer_id,
        e.is_late,
        e.shipping_mode,
        EXISTS (
            SELECT 1 FROM items i
            WHERE i.customer_id = e.customer_id
              AND i.order_id   <> e.order_id
              AND i.order_date >  e.order_date
              AND i.order_date <= e.order_date + INTERVAL 90 DAY
        ) AS repurchased_90d
    FROM eligible e
)
SELECT
    CASE WHEN is_late = 1 THEN 'Late' ELSE 'On time' END AS first_order,
    COUNT(*)                                             AS customers,
    SUM(CASE WHEN repurchased_90d THEN 1 ELSE 0 END)     AS repurchased,
    ROUND(100 * AVG(CASE WHEN repurchased_90d THEN 1 ELSE 0 END), 1) AS repurchase_90d_pct
FROM outcome
GROUP BY 1
ORDER BY 1;
