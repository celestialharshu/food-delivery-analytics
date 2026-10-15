-- ============================================================
-- 01_schema.sql
-- Food Delivery Business Analytics — PostgreSQL Schema
-- ============================================================

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS restaurants CASCADE;
DROP TABLE IF EXISTS delivery_partners CASCADE;

CREATE TABLE customers (
    customer_id     VARCHAR(15) PRIMARY KEY,
    customer_name   VARCHAR(100) NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    signup_date     DATE         NOT NULL,
    age             SMALLINT,
    gender          VARCHAR(10)
);

CREATE TABLE restaurants (
    restaurant_id       VARCHAR(15) PRIMARY KEY,
    restaurant_name     VARCHAR(150) NOT NULL,
    city                VARCHAR(50)  NOT NULL,
    primary_category    VARCHAR(50)  NOT NULL,
    avg_prep_time_min   SMALLINT,
    onboarded_date      DATE
);

CREATE TABLE delivery_partners (
    partner_id      VARCHAR(15) PRIMARY KEY,
    partner_name    VARCHAR(100) NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    vehicle_type    VARCHAR(20),
    joined_date     DATE
);

CREATE TABLE orders (
    order_id                VARCHAR(15) PRIMARY KEY,
    customer_id             VARCHAR(15) REFERENCES customers(customer_id),
    city                    VARCHAR(50) NOT NULL,
    restaurant_id           VARCHAR(15) REFERENCES restaurants(restaurant_id),
    food_category           VARCHAR(50) NOT NULL,
    partner_id              VARCHAR(15) REFERENCES delivery_partners(partner_id),
    order_timestamp         TIMESTAMP   NOT NULL,
    order_value             NUMERIC(10,2) NOT NULL,
    discount_pct            SMALLINT DEFAULT 0,
    discount_amount         NUMERIC(10,2) DEFAULT 0,
    final_amount            NUMERIC(10,2) NOT NULL,
    payment_method          VARCHAR(30),
    promised_delivery_min   NUMERIC(6,1),
    actual_delivery_min     NUMERIC(6,1),
    is_late                 BOOLEAN,
    rating                  NUMERIC(2,1),
    order_date              DATE,
    order_hour              SMALLINT,
    order_month             VARCHAR(7),
    day_of_week             VARCHAR(10)
);

-- Indexes to speed up the analytical queries in 03_analysis_queries.sql
CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_restaurant ON orders(restaurant_id);
CREATE INDEX idx_orders_partner    ON orders(partner_id);
CREATE INDEX idx_orders_timestamp  ON orders(order_timestamp);
CREATE INDEX idx_orders_city       ON orders(city);
CREATE INDEX idx_orders_month      ON orders(order_month);
