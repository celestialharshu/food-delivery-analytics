-- ============================================================
-- 02_load_data.sql
-- Loads the cleaned CSVs (data/processed/) into PostgreSQL.
--
-- Run from the psql shell connected to your database, e.g.:
--   psql -U postgres -d food_delivery_db -f sql/02_load_data.sql
--
-- IMPORTANT: \copy runs from the CLIENT machine (no server-side file
-- permissions needed), so run psql from the project's root folder so
-- these relative paths resolve correctly.
-- ============================================================

\copy customers FROM 'data/processed/customers_clean.csv' WITH (FORMAT csv, HEADER true);

\copy restaurants FROM 'data/processed/restaurants_clean.csv' WITH (FORMAT csv, HEADER true);

\copy delivery_partners FROM 'data/processed/delivery_partners_clean.csv' WITH (FORMAT csv, HEADER true);

\copy orders (order_id, customer_id, city, restaurant_id, food_category, partner_id, order_timestamp, order_value, discount_pct, discount_amount, final_amount, payment_method, promised_delivery_min, actual_delivery_min, is_late, rating, order_date, order_hour, order_month, day_of_week) FROM 'data/processed/orders_clean.csv' WITH (FORMAT csv, HEADER true);

-- Sanity checks
SELECT 'customers' AS table_name, COUNT(*) FROM customers
UNION ALL SELECT 'restaurants', COUNT(*) FROM restaurants
UNION ALL SELECT 'delivery_partners', COUNT(*) FROM delivery_partners
UNION ALL SELECT 'orders', COUNT(*) FROM orders;
