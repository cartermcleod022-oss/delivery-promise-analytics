-- Bonus (challenge the analysis): Is a mode's late rate the same everywhere?
-- If one region's Standard Class were much worse, that would be an
-- operations problem the promise fix wouldn't solve.
-- Look for: how far each region strays from its mode's overall rate.

SELECT
    order_region,
    ROUND(100 * AVG(CASE WHEN shipping_mode = 'Standard Class' THEN is_late END), 1) AS standard_late_pct,
    ROUND(100 * AVG(CASE WHEN shipping_mode = 'Second Class'   THEN is_late END), 1) AS second_late_pct,
    ROUND(100 * AVG(CASE WHEN shipping_mode = 'First Class'    THEN is_late END), 1) AS first_late_pct,
    COUNT(*) AS orders
FROM orders
GROUP BY order_region
ORDER BY standard_late_pct DESC;
