"""
data_cleaning.py
------------------
Cleans the raw generated CSVs and writes analysis-ready files to
data/processed/. Mirrors the kind of cleaning you'd do on a real,
messy delivery dataset (nulls, bad sentinel values, duplicates,
outliers, type casting).

Run:
    python src/data_cleaning.py
"""

import os
import pandas as pd
import numpy as np

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    df["order_timestamp"] = pd.to_datetime(df["order_timestamp"])

    # Fix bad sentinel values (-1) in actual_delivery_min -> impute with category median
    bad_mask = df["actual_delivery_min"] < 0
    print(f"  Fixing {bad_mask.sum()} rows with invalid actual_delivery_min (-1 sentinel)")
    median_by_cat = df.loc[~bad_mask].groupby("food_category")["actual_delivery_min"].transform("median")
    df.loc[bad_mask, "actual_delivery_min"] = df.loc[bad_mask, "food_category"].map(
        df.loc[~bad_mask].groupby("food_category")["actual_delivery_min"].median()
    )

    # Fix missing ratings -> impute with restaurant-level average, fallback global average
    null_ratings = df["rating"].isna().sum()
    print(f"  Imputing {null_ratings} missing ratings")
    rest_avg = df.groupby("restaurant_id")["rating"].transform("mean")
    df["rating"] = df["rating"].fillna(rest_avg)
    df["rating"] = df["rating"].fillna(df["rating"].mean())
    df["rating"] = df["rating"].round(1)

    # Remove exact duplicate orders, if any
    before = len(df)
    df = df.drop_duplicates(subset="order_id")
    print(f"  Removed {before - len(df)} duplicate order_id rows")

    # Recompute is_late flag consistently after cleaning
    df["is_late"] = df["actual_delivery_min"] > df["promised_delivery_min"]

    # Derived time features used across the SQL/BI layer
    df["order_date"] = df["order_timestamp"].dt.date
    df["order_hour"] = df["order_timestamp"].dt.hour
    df["order_month"] = df["order_timestamp"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["order_timestamp"].dt.day_name()

    return df


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df = df.drop_duplicates(subset="customer_id")
    return df


def clean_restaurants(restaurants: pd.DataFrame) -> pd.DataFrame:
    df = restaurants.copy()
    df["onboarded_date"] = pd.to_datetime(df["onboarded_date"])
    df = df.drop_duplicates(subset="restaurant_id")
    return df


def clean_partners(partners: pd.DataFrame) -> pd.DataFrame:
    df = partners.copy()
    df["joined_date"] = pd.to_datetime(df["joined_date"])
    df = df.drop_duplicates(subset="partner_id")
    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("Loading raw files...")
    orders = pd.read_csv(f"{RAW_DIR}/orders.csv")
    customers = pd.read_csv(f"{RAW_DIR}/customers.csv")
    restaurants = pd.read_csv(f"{RAW_DIR}/restaurants.csv")
    partners = pd.read_csv(f"{RAW_DIR}/delivery_partners.csv")

    print("\nCleaning orders...")
    orders_clean = clean_orders(orders)

    print("\nCleaning customers/restaurants/partners...")
    customers_clean = clean_customers(customers)
    restaurants_clean = clean_restaurants(restaurants)
    partners_clean = clean_partners(partners)

    orders_clean.to_csv(f"{PROCESSED_DIR}/orders_clean.csv", index=False)
    customers_clean.to_csv(f"{PROCESSED_DIR}/customers_clean.csv", index=False)
    restaurants_clean.to_csv(f"{PROCESSED_DIR}/restaurants_clean.csv", index=False)
    partners_clean.to_csv(f"{PROCESSED_DIR}/delivery_partners_clean.csv", index=False)

    print("\nDone. Cleaned files written to", PROCESSED_DIR)
    print(orders_clean.info())


if __name__ == "__main__":
    main()
