"""
generate_data.py
-----------------
Generates a realistic, internally-consistent synthetic dataset for the
Food Delivery Business Analytics project (no external APIs / no internet
required — pure Python + NumPy + Pandas).

Outputs (data/raw/):
    customers.csv
    restaurants.csv
    delivery_partners.csv
    orders.csv

Run:
    python src/generate_data.py --orders 100000
"""

import argparse
import random
import string
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

# ----------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------

CITIES = [
    ("Mumbai", 0.22), ("Delhi", 0.20), ("Bengaluru", 0.16),
    ("Hyderabad", 0.11), ("Pune", 0.10), ("Chennai", 0.09),
    ("Kolkata", 0.07), ("Ahmedabad", 0.05),
]
CITY_NAMES = [c[0] for c in CITIES]
CITY_WEIGHTS = [c[1] for c in CITIES]

FOOD_CATEGORIES = [
    "North Indian", "South Indian", "Chinese", "Italian", "Fast Food",
    "Desserts", "Beverages", "Biryani", "Healthy Food", "Bakery",
]

PAYMENT_METHODS = [("UPI", 0.52), ("Card", 0.23), ("Cash on Delivery", 0.18), ("Wallet", 0.07)]
PAYMENT_NAMES = [p[0] for p in PAYMENT_METHODS]
PAYMENT_WEIGHTS = [p[1] for p in PAYMENT_METHODS]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
               "Ananya", "Diya", "Isha", "Kavya", "Myra", "Saanvi", "Anika", "Riya",
               "Rohan", "Karan", "Neha", "Priya", "Amit", "Sneha", "Rahul", "Pooja"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Iyer", "Nair", "Reddy", "Mehta", "Singh",
              "Patel", "Das", "Rao", "Kapoor", "Joshi", "Chatterjee", "Malhotra", "Bose"]

RESTAURANT_ADJ = ["Spice", "Royal", "Urban", "The Grand", "Tasty", "Golden", "Fresh",
                   "Curry", "Flavour", "Punjab", "South", "Delhi", "Biryani", "Green",
                   "Cloud", "Metro"]
RESTAURANT_NOUN = ["Kitchen", "House", "Bistro", "Junction", "Corner", "Hub", "Point",
                    "Diner", "Cafe", "Express", "Tadka", "Bites", "Bowl", "Table"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_id(prefix, n, width=6):
    return [f"{prefix}{str(i).zfill(width)}" for i in range(1, n + 1)]


# ----------------------------------------------------------------------
# 1. Customers
# ----------------------------------------------------------------------

def generate_customers(n_customers):
    signup_start = datetime(2023, 1, 1)
    signup_end = datetime(2025, 6, 30)
    signup_days = (signup_end - signup_start).days

    customers = pd.DataFrame({
        "customer_id": random_id("CUST", n_customers),
        "customer_name": [random_name() for _ in range(n_customers)],
        "city": np.random.choice(CITY_NAMES, size=n_customers, p=CITY_WEIGHTS),
        "signup_date": [
            signup_start + timedelta(days=int(np.random.randint(0, signup_days)))
            for _ in range(n_customers)
        ],
        "age": np.random.randint(18, 55, size=n_customers),
        "gender": np.random.choice(["Male", "Female", "Other"], size=n_customers, p=[0.54, 0.44, 0.02]),
    })
    return customers


# ----------------------------------------------------------------------
# 2. Restaurants
# ----------------------------------------------------------------------

def generate_restaurants(n_restaurants):
    restaurants = pd.DataFrame({
        "restaurant_id": random_id("REST", n_restaurants),
        "restaurant_name": [
            f"{random.choice(RESTAURANT_ADJ)} {random.choice(RESTAURANT_NOUN)}"
            for _ in range(n_restaurants)
        ],
        "city": np.random.choice(CITY_NAMES, size=n_restaurants, p=CITY_WEIGHTS),
        "primary_category": np.random.choice(FOOD_CATEGORIES, size=n_restaurants),
        "avg_prep_time_min": np.random.randint(10, 40, size=n_restaurants),
        "onboarded_date": [
            datetime(2022, 1, 1) + timedelta(days=int(np.random.randint(0, 900)))
            for _ in range(n_restaurants)
        ],
    })
    return restaurants


# ----------------------------------------------------------------------
# 3. Delivery partners
# ----------------------------------------------------------------------

def generate_delivery_partners(n_partners):
    partners = pd.DataFrame({
        "partner_id": random_id("DP", n_partners),
        "partner_name": [random_name() for _ in range(n_partners)],
        "city": np.random.choice(CITY_NAMES, size=n_partners, p=CITY_WEIGHTS),
        "vehicle_type": np.random.choice(["Bike", "Scooter", "Bicycle"], size=n_partners, p=[0.65, 0.30, 0.05]),
        "joined_date": [
            datetime(2022, 1, 1) + timedelta(days=int(np.random.randint(0, 900)))
            for _ in range(n_partners)
        ],
    })
    return partners


# ----------------------------------------------------------------------
# 4. Orders (the fact table)
# ----------------------------------------------------------------------

def generate_orders(n_orders, customers, restaurants, partners):
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31, 23, 59, 59)
    total_seconds = int((end_date - start_date).total_seconds())

    # Skew customers so ~30% of customers generate ~70% of orders (repeat-purchase realism)
    cust_weights = np.random.pareto(a=1.6, size=len(customers)) + 0.1
    cust_weights = cust_weights / cust_weights.sum()

    order_customer_idx = np.random.choice(len(customers), size=n_orders, p=cust_weights)
    order_customers = customers.iloc[order_customer_idx].reset_index(drop=True)

    # Match restaurant city to customer city (mostly)
    rest_by_city = {c: restaurants[restaurants.city == c] for c in CITY_NAMES}
    partner_by_city = {c: partners[partners.city == c] for c in CITY_NAMES}

    restaurant_ids, restaurant_cats, prep_times = [], [], []
    partner_ids = []
    for city in order_customers["city"]:
        r_pool = rest_by_city[city] if len(rest_by_city[city]) else restaurants
        r_row = r_pool.sample(1).iloc[0]
        restaurant_ids.append(r_row.restaurant_id)
        restaurant_cats.append(r_row.primary_category)
        prep_times.append(r_row.avg_prep_time_min)

        p_pool = partner_by_city[city] if len(partner_by_city[city]) else partners
        partner_ids.append(p_pool.sample(1).iloc[0].partner_id)

    # Order timestamps — bias towards lunch (12-14) and dinner (19-22) hours
    hour_weights = np.array([1, 1, 1, 1, 1, 1, 2, 3, 4, 4, 5, 6,
                              9, 8, 5, 4, 4, 5, 7, 10, 9, 7, 4, 2], dtype=float)
    hour_weights = hour_weights / hour_weights.sum()

    offsets = np.random.randint(0, total_seconds, size=n_orders)
    order_ts = [start_date + timedelta(seconds=int(o)) for o in offsets]
    hours = np.random.choice(24, size=n_orders, p=hour_weights)
    order_timestamps = [
        ts.replace(hour=int(h), minute=int(np.random.randint(0, 60)), second=int(np.random.randint(0, 60)))
        for ts, h in zip(order_ts, hours)
    ]

    # Order value: base price by category + noise
    category_base_price = {
        "North Indian": 420, "South Indian": 260, "Chinese": 340, "Italian": 480,
        "Fast Food": 250, "Desserts": 220, "Beverages": 150, "Biryani": 360,
        "Healthy Food": 380, "Bakery": 240,
    }
    base_prices = np.array([category_base_price[c] for c in restaurant_cats])
    order_value = np.round(np.abs(np.random.normal(loc=base_prices, scale=base_prices * 0.35)) + 60, 2)
    order_value = np.clip(order_value, 99, 4000)

    # Discounts: ~40% of orders have a discount code applied
    has_discount = np.random.rand(n_orders) < 0.40
    discount_pct = np.where(has_discount, np.random.choice([10, 15, 20, 25, 30], size=n_orders), 0)
    discount_amount = np.round(order_value * discount_pct / 100, 2)
    final_amount = np.round(order_value - discount_amount, 2)

    # Delivery time: prep_time + travel_time + noise, with ~12% "late" orders
    travel_time = np.random.normal(loc=18, scale=6, size=n_orders)
    delivery_time_min = np.round(np.array(prep_times) + np.clip(travel_time, 5, 60), 1)
    promised_time_min = np.round(np.array(prep_times) + 20, 1)
    is_late = delivery_time_min > promised_time_min

    # Ratings: correlated with lateness (late orders rated lower)
    base_rating = np.random.normal(loc=4.3, scale=0.6, size=n_orders)
    rating = np.where(is_late, base_rating - np.random.uniform(0.5, 1.5, n_orders), base_rating)
    rating = np.clip(np.round(rating * 2) / 2, 1.0, 5.0)  # round to nearest 0.5

    orders = pd.DataFrame({
        "order_id": random_id("ORD", n_orders, width=7),
        "customer_id": order_customers["customer_id"].values,
        "city": order_customers["city"].values,
        "restaurant_id": restaurant_ids,
        "food_category": restaurant_cats,
        "partner_id": partner_ids,
        "order_timestamp": order_timestamps,
        "order_value": order_value,
        "discount_pct": discount_pct,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "payment_method": np.random.choice(PAYMENT_NAMES, size=n_orders, p=PAYMENT_WEIGHTS),
        "promised_delivery_min": promised_time_min,
        "actual_delivery_min": delivery_time_min,
        "is_late": is_late,
        "rating": rating,
    })

    orders = orders.sort_values("order_timestamp").reset_index(drop=True)
    return orders


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--customers", type=int, default=12_000)
    parser.add_argument("--restaurants", type=int, default=600)
    parser.add_argument("--partners", type=int, default=1_500)
    parser.add_argument("--outdir", type=str, default="data/raw")
    args = parser.parse_args()

    print(f"Generating {args.customers} customers...")
    customers = generate_customers(args.customers)

    print(f"Generating {args.restaurants} restaurants...")
    restaurants = generate_restaurants(args.restaurants)

    print(f"Generating {args.partners} delivery partners...")
    partners = generate_delivery_partners(args.partners)

    print(f"Generating {args.orders} orders...")
    orders = generate_orders(args.orders, customers, restaurants, partners)

    # Inject a small amount of realistic messiness for the cleaning step to fix
    dirty_idx = np.random.choice(len(orders), size=int(len(orders) * 0.01), replace=False)
    orders.loc[dirty_idx[: len(dirty_idx) // 2], "rating"] = np.nan
    orders.loc[dirty_idx[len(dirty_idx) // 2:], "actual_delivery_min"] = -1  # bad sentinel value

    import os
    os.makedirs(args.outdir, exist_ok=True)
    customers.to_csv(f"{args.outdir}/customers.csv", index=False)
    restaurants.to_csv(f"{args.outdir}/restaurants.csv", index=False)
    partners.to_csv(f"{args.outdir}/delivery_partners.csv", index=False)
    orders.to_csv(f"{args.outdir}/orders.csv", index=False)

    print("\nDone. Files written to", args.outdir)
    print(f"  customers.csv          {len(customers):,} rows")
    print(f"  restaurants.csv        {len(restaurants):,} rows")
    print(f"  delivery_partners.csv  {len(partners):,} rows")
    print(f"  orders.csv             {len(orders):,} rows")


if __name__ == "__main__":
    main()
