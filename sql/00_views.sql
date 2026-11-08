-- Shared views used by every question.
-- items  : the clean file, one row per order item
-- orders : one row per SHIPPED order (cancellations excluded).
--          Phase 2 verified that every item in an order shares the same shipping
--          mode, dates and late status, so ANY_VALUE() safely picks "the" value.

CREATE OR REPLACE VIEW items AS
SELECT * FROM 'data/processed/order_items.parquet';

CREATE OR REPLACE VIEW orders AS
SELECT
    order_id,
    ANY_VALUE(customer_id)       AS customer_id,
    ANY_VALUE(order_date)        AS order_date,
    ANY_VALUE(order_month)       AS order_month,
    ANY_VALUE(order_weekday)     AS order_weekday,
    ANY_VALUE(shipping_mode)     AS shipping_mode,
    ANY_VALUE(days_scheduled)    AS days_scheduled,
    ANY_VALUE(days_actual)       AS days_actual,
    ANY_VALUE(days_late)         AS days_late,
    ANY_VALUE(is_late)           AS is_late,
    ANY_VALUE(market)            AS market,
    ANY_VALUE(order_region)      AS order_region,
    ANY_VALUE(customer_segment)  AS customer_segment,
    ANY_VALUE(payment_type)      AS payment_type,
    SUM(item_sales_net)          AS order_sales,
    SUM(item_profit)             AS order_profit
FROM items
WHERE NOT is_canceled
GROUP BY order_id;
