-- Q3 (Standard promise): What happens under each way of showing the promise?
-- For each candidate promise: % on time, and how many days EARLY the average
-- on-time package arrives (promising too much slack has a cost too: it may
-- scare customers off at checkout).
-- Change the mode name to explore the others.

SELECT
    p.promise_days,
    ROUND(100 * AVG(CASE WHEN o.days_actual <= p.promise_days THEN 1 ELSE 0 END), 1) AS otd_pct,
    ROUND(AVG(CASE WHEN o.days_actual <= p.promise_days
                   THEN p.promise_days - o.days_actual END), 2)                    AS avg_days_early_when_on_time
FROM orders o
CROSS JOIN range(2, 7) p(promise_days)
WHERE o.shipping_mode = 'Standard Class'
GROUP BY p.promise_days
ORDER BY p.promise_days;
