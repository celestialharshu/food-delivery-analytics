-- ============================================================
-- 03_analysis_queries.sql
-- Food Delivery Business Analytics — Core KPI Queries
-- Organized by: Revenue | Customer | Operations | Business
-- These queries power both direct reporting and the Power BI dashboard.
-- ============================================================


-- ============================================================
-- SECTION 1: REVENUE ANALYTICS
-- ============================================================

-- 1.1 Monthly revenue trend
SELECT
    order_month,
    COUNT(order_id)                AS total_orders,
    ROUND(SUM(final_amount), 2)    AS total_revenue,
    ROUND(AVG(final_amount), 2)    AS avg_order_value
FROM orders
GROUP BY order_month
ORDER BY order_month;

-- 1.2 Average Order Value (AOV) overall and by city
SELECT
    city,
    COUNT(order_id)             AS total_orders,
    ROUND(AVG(final_amount), 2) AS avg_order_value,
    ROUND(SUM(final_amount), 2) AS total_revenue
FROM orders
GROUP BY city
ORDER BY total_revenue DESC;

-- 1.3 Revenue by restaurant (top 20)
SELECT
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    COUNT(o.order_id)              AS total_orders,
    ROUND(SUM(o.final_amount), 2)  AS total_revenue,
    ROUND(AVG(o.rating), 2)        AS avg_rating
FROM orders o
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
GROUP BY r.restaurant_id, r.restaurant_name, r.city
ORDER BY total_revenue DESC
LIMIT 20;

-- 1.4 Revenue by food category
SELECT
    food_category,
    COUNT(order_id)                          AS total_orders,
    ROUND(SUM(final_amount), 2)              AS total_revenue,
    ROUND(100.0 * SUM(final_amount) / SUM(SUM(final_amount)) OVER (), 2) AS pct_of_total_revenue
FROM orders
GROUP BY food_category
ORDER BY total_revenue DESC;

-- 1.5 Month-over-month revenue growth %
WITH monthly AS (
    SELECT order_month, SUM(final_amount) AS revenue
    FROM orders
    GROUP BY order_month
)
SELECT
    order_month,
    revenue,
    LAG(revenue) OVER (ORDER BY order_month)                                    AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
          / NULLIF(LAG(revenue) OVER (ORDER BY order_month), 0), 2)             AS mom_growth_pct
FROM monthly
ORDER BY order_month;


-- ============================================================
-- SECTION 2: CUSTOMER ANALYTICS
-- ============================================================

-- 2.1 New vs Returning customers per month
WITH first_orders AS (
    SELECT customer_id, MIN(order_month) AS first_order_month
    FROM orders
    GROUP BY customer_id
)
SELECT
    o.order_month,
    COUNT(DISTINCT CASE WHEN o.order_month = f.first_order_month THEN o.customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN o.order_month <> f.first_order_month THEN o.customer_id END) AS returning_customers
FROM orders o
JOIN first_orders f ON o.customer_id = f.customer_id
GROUP BY o.order_month
ORDER BY o.order_month;

-- 2.2 Customer retention rate (month-over-month cohort retention, simplified)
WITH monthly_customers AS (
    SELECT DISTINCT customer_id, order_month
    FROM orders
),
retention AS (
    SELECT
        curr.order_month,
        COUNT(DISTINCT curr.customer_id) AS active_customers,
        COUNT(DISTINCT prev.customer_id) AS retained_from_prev_month
    FROM monthly_customers curr
    LEFT JOIN monthly_customers prev
        ON curr.customer_id = prev.customer_id
        AND prev.order_month = TO_CHAR(TO_DATE(curr.order_month, 'YYYY-MM') - INTERVAL '1 month', 'YYYY-MM')
    GROUP BY curr.order_month
)
SELECT
    order_month,
    active_customers,
    retained_from_prev_month,
    ROUND(100.0 * retained_from_prev_month / NULLIF(active_customers, 0), 2) AS retention_rate_pct
FROM retention
ORDER BY order_month;

-- 2.3 Customer Lifetime Value (CLV) — top 20 highest-value customers
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    COUNT(o.order_id)               AS total_orders,
    ROUND(SUM(o.final_amount), 2)   AS lifetime_value,
    ROUND(AVG(o.final_amount), 2)   AS avg_order_value,
    MIN(o.order_date)               AS first_order,
    MAX(o.order_date)               AS last_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.city
ORDER BY lifetime_value DESC
LIMIT 20;

-- 2.4 Repeat purchase rate (customers with 2+ orders / all ordering customers)
WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS num_orders
    FROM orders
    GROUP BY customer_id
)
SELECT
    COUNT(*) FILTER (WHERE num_orders >= 2)                          AS repeat_customers,
    COUNT(*)                                                         AS total_ordering_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE num_orders >= 2) / COUNT(*), 2) AS repeat_purchase_rate_pct
FROM order_counts;

-- 2.5 Customer segmentation (RFM-style: Recency, Frequency, Monetary)
WITH rfm_base AS (
    SELECT
        customer_id,
        MAX(order_date)                       AS last_order_date,
        COUNT(order_id)                       AS frequency,
        SUM(final_amount)                     AS monetary
    FROM orders
    GROUP BY customer_id
),
rfm_scored AS (
    SELECT
        customer_id,
        (CURRENT_DATE - last_order_date)      AS recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY (CURRENT_DATE - last_order_date) DESC) AS recency_score,   -- 4 = most recent
        NTILE(4) OVER (ORDER BY frequency ASC)                          AS frequency_score,
        NTILE(4) OVER (ORDER BY monetary ASC)                           AS monetary_score
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    CASE
        WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'Champions'
        WHEN frequency_score >= 3 AND monetary_score >= 3                        THEN 'Loyal Customers'
        WHEN recency_score >= 3 AND frequency_score <= 2                         THEN 'New / Promising'
        WHEN recency_score <= 2 AND frequency_score >= 3                         THEN 'At Risk'
        ELSE 'Needs Attention'
    END AS customer_segment
FROM rfm_scored
ORDER BY monetary DESC;


-- ============================================================
-- SECTION 3: OPERATIONS ANALYTICS
-- ============================================================

-- 3.1 Average delivery time overall and by city
SELECT
    city,
    ROUND(AVG(actual_delivery_min), 1)   AS avg_delivery_time_min,
    ROUND(AVG(promised_delivery_min), 1) AS avg_promised_time_min
FROM orders
GROUP BY city
ORDER BY avg_delivery_time_min DESC;

-- 3.2 Late-delivery percentage overall and by city
SELECT
    city,
    COUNT(*)                                                    AS total_orders,
    COUNT(*) FILTER (WHERE is_late)                              AS late_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_late) / COUNT(*), 2) AS late_pct
FROM orders
GROUP BY city
ORDER BY late_pct DESC;

-- 3.3 Delivery partner performance (top and bottom performers)
SELECT
    dp.partner_id,
    dp.partner_name,
    dp.city,
    COUNT(o.order_id)                                              AS total_deliveries,
    ROUND(AVG(o.actual_delivery_min), 1)                           AS avg_delivery_time_min,
    ROUND(100.0 * COUNT(*) FILTER (WHERE o.is_late) / COUNT(*), 2) AS late_pct,
    ROUND(AVG(o.rating), 2)                                        AS avg_rating
FROM delivery_partners dp
JOIN orders o ON dp.partner_id = o.partner_id
GROUP BY dp.partner_id, dp.partner_name, dp.city
HAVING COUNT(o.order_id) >= 10
ORDER BY late_pct ASC, avg_rating DESC
LIMIT 20;

-- 3.4 Peak ordering hours
SELECT
    order_hour,
    COUNT(order_id)              AS total_orders,
    ROUND(SUM(final_amount), 2)  AS revenue
FROM orders
GROUP BY order_hour
ORDER BY order_hour;

-- 3.5 Restaurant preparation time vs rating (does slow prep hurt ratings?)
SELECT
    r.restaurant_id,
    r.restaurant_name,
    r.avg_prep_time_min,
    ROUND(AVG(o.rating), 2)  AS avg_customer_rating,
    COUNT(o.order_id)        AS total_orders
FROM restaurants r
JOIN orders o ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.restaurant_name, r.avg_prep_time_min
HAVING COUNT(o.order_id) >= 10
ORDER BY r.avg_prep_time_min DESC;


-- ============================================================
-- SECTION 4: BUSINESS / STRATEGIC ANALYTICS
-- ============================================================

-- 4.1 Effect of discounts on revenue and order volume
SELECT
    CASE WHEN discount_pct = 0 THEN 'No Discount' ELSE CONCAT(discount_pct, '% Discount') END AS discount_band,
    COUNT(order_id)                 AS total_orders,
    ROUND(AVG(order_value), 2)      AS avg_gross_order_value,
    ROUND(AVG(final_amount), 2)     AS avg_net_order_value,
    ROUND(SUM(final_amount), 2)     AS total_net_revenue,
    ROUND(SUM(discount_amount), 2)  AS total_discount_given
FROM orders
GROUP BY discount_band
ORDER BY total_orders DESC;

-- 4.2 Most profitable restaurants (proxy: net revenue after discount, order volume, rating)
SELECT
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    COUNT(o.order_id)               AS total_orders,
    ROUND(SUM(o.final_amount), 2)   AS net_revenue,
    ROUND(SUM(o.discount_amount), 2) AS discount_given,
    ROUND(AVG(o.rating), 2)         AS avg_rating
FROM restaurants r
JOIN orders o ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.restaurant_name, r.city
ORDER BY net_revenue DESC
LIMIT 15;

-- 4.3 Highest-growth cities (comparing first vs last quarter available in the data)
WITH quarters AS (
    SELECT
        city,
        TO_CHAR(order_timestamp, 'YYYY-Q') AS quarter,
        SUM(final_amount)                  AS revenue
    FROM orders
    GROUP BY city, TO_CHAR(order_timestamp, 'YYYY-Q')
),
bounds AS (
    SELECT MIN(quarter) AS first_q, MAX(quarter) AS last_q FROM quarters
)
SELECT
    q1.city,
    q1.revenue  AS first_quarter_revenue,
    q2.revenue  AS last_quarter_revenue,
    ROUND(100.0 * (q2.revenue - q1.revenue) / NULLIF(q1.revenue, 0), 2) AS growth_pct
FROM quarters q1
JOIN bounds b ON q1.quarter = b.first_q
JOIN quarters q2 ON q2.city = q1.city AND q2.quarter = b.last_q
ORDER BY growth_pct DESC;

-- 4.4 Most valuable customer segments (ties into RFM segmentation, 2.5)
-- Run 2.5 as a CTE and aggregate:
WITH rfm_base AS (
    SELECT customer_id, MAX(order_date) AS last_order_date, COUNT(order_id) AS frequency, SUM(final_amount) AS monetary
    FROM orders GROUP BY customer_id
),
rfm_scored AS (
    SELECT customer_id, (CURRENT_DATE - last_order_date) AS recency_days, frequency, monetary,
        NTILE(4) OVER (ORDER BY (CURRENT_DATE - last_order_date) DESC) AS recency_score,
        NTILE(4) OVER (ORDER BY frequency ASC)                          AS frequency_score,
        NTILE(4) OVER (ORDER BY monetary ASC)                           AS monetary_score
    FROM rfm_base
),
segmented AS (
    SELECT *,
        CASE
            WHEN recency_score >= 3 AND frequency_score >= 3 AND monetary_score >= 3 THEN 'Champions'
            WHEN frequency_score >= 3 AND monetary_score >= 3                        THEN 'Loyal Customers'
            WHEN recency_score >= 3 AND frequency_score <= 2                         THEN 'New / Promising'
            WHEN recency_score <= 2 AND frequency_score >= 3                         THEN 'At Risk'
            ELSE 'Needs Attention'
        END AS customer_segment
    FROM rfm_scored
)
SELECT
    customer_segment,
    COUNT(*)                    AS num_customers,
    ROUND(SUM(monetary), 2)     AS total_revenue,
    ROUND(AVG(monetary), 2)     AS avg_lifetime_value
FROM segmented
GROUP BY customer_segment
ORDER BY total_revenue DESC;
