"""
app.py
-------
Public, no-login web dashboard for the Food Delivery Business Analytics
project. Deploy this on Streamlit Community Cloud (or Render/Railway) so
recruiters can open one link and see the analysis live.

Data source priority:
    1. DATABASE_URL env var (PostgreSQL) — used if set, e.g. on Railway/Render.
    2. Local cleaned CSVs in data/processed/ — used for local runs and for
       Streamlit Cloud when you don't want to expose a DB connection string.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Food Delivery Business Analytics", layout="wide", page_icon="")

DATABASE_URL = os.environ.get("DATABASE_URL")


@st.cache_data
def load_data():
    if DATABASE_URL:
        from sqlalchemy import create_engine
        engine = create_engine(DATABASE_URL)
        orders = pd.read_sql("SELECT * FROM orders", engine, parse_dates=["order_timestamp"])
        customers = pd.read_sql("SELECT * FROM customers", engine, parse_dates=["signup_date"])
        restaurants = pd.read_sql("SELECT * FROM restaurants", engine)
    else:
        orders = pd.read_csv("data/processed/orders_clean.csv", parse_dates=["order_timestamp"])
        customers = pd.read_csv("data/processed/customers_clean.csv", parse_dates=["signup_date"])
        restaurants = pd.read_csv("data/processed/restaurants_clean.csv")
    return orders, customers, restaurants


orders, customers, restaurants = load_data()

# ----------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------
st.sidebar.title("Filters")
cities = st.sidebar.multiselect("City", sorted(orders["city"].unique()), default=None)
categories = st.sidebar.multiselect("Food Category", sorted(orders["food_category"].unique()), default=None)

filtered = orders.copy()
if cities:
    filtered = filtered[filtered["city"].isin(cities)]
if categories:
    filtered = filtered[filtered["food_category"].isin(categories)]

st.title("Food Delivery Business Analytics Dashboard")
st.caption("Python (Pandas/NumPy) → PostgreSQL → this dashboard. Source: github.com/<your-username>/food-delivery-analytics")

tab1, tab2, tab3, tab4 = st.tabs(["Executive Overview", "Customers", "Operations", "Business Insights"])

# ----------------------------------------------------------------------
# Tab 1: Executive Overview
# ----------------------------------------------------------------------
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₹{filtered['final_amount'].sum():,.0f}")
    col2.metric("Total Orders", f"{len(filtered):,}")
    col3.metric("Avg Order Value", f"₹{filtered['final_amount'].mean():,.0f}")
    repeat_rate = (filtered.groupby("customer_id").size() >= 2).mean() * 100
    col4.metric("Repeat Purchase Rate", f"{repeat_rate:.1f}%")

    c1, c2 = st.columns(2)
    with c1:
        monthly = filtered.groupby("order_month")["final_amount"].sum().reset_index()
        fig = px.line(monthly, x="order_month", y="final_amount", markers=True, title="Monthly Revenue Trend")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        cat_rev = filtered.groupby("food_category")["final_amount"].sum().reset_index()
        fig = px.pie(cat_rev, names="food_category", values="final_amount", title="Revenue by Food Category", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    city_rev = filtered.groupby("city")["final_amount"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(city_rev, x="city", y="final_amount", title="Revenue by City", color="final_amount", color_continuous_scale="Reds")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# Tab 2: Customers
# ----------------------------------------------------------------------
with tab2:
    order_counts = filtered.groupby("customer_id").size().reset_index(name="num_orders")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(order_counts, x="num_orders", nbins=30, title="Orders per Customer")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        clv = filtered.groupby("customer_id")["final_amount"].sum().reset_index(name="lifetime_value")
        fig = px.histogram(clv, x="lifetime_value", nbins=40, title="Customer Lifetime Value Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 20 Customers by Lifetime Value")
    top_customers = (
        filtered.groupby("customer_id")["final_amount"]
        .agg(total_orders="count", lifetime_value="sum")
        .sort_values("lifetime_value", ascending=False)
        .head(20)
        .reset_index()
        .merge(customers[["customer_id", "customer_name", "city"]], on="customer_id", how="left")
    )
    st.dataframe(top_customers, use_container_width=True)

# ----------------------------------------------------------------------
# Tab 3: Operations
# ----------------------------------------------------------------------
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        late_city = (filtered.groupby("city")["is_late"].mean() * 100).sort_values(ascending=False).reset_index(name="late_pct")
        fig = px.bar(late_city, x="city", y="late_pct", title="Late Delivery % by City", color="late_pct", color_continuous_scale="Oranges")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        hourly = filtered.groupby("order_hour").size().reset_index(name="orders")
        fig = px.bar(hourly, x="order_hour", y="orders", title="Peak Ordering Hours")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Delivery Time vs Rating")
    sample = filtered.sample(min(3000, len(filtered)), random_state=1)
    fig = px.scatter(sample, x="actual_delivery_min", y="rating", opacity=0.3, trendline="ols" if len(sample) < 5000 else None)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# Tab 4: Business Insights
# ----------------------------------------------------------------------
with tab4:
    filtered_disc = filtered.copy()
    filtered_disc["discount_band"] = filtered_disc["discount_pct"].apply(
        lambda x: "No Discount" if x == 0 else f"{x}% Discount"
    )
    disc_summary = filtered_disc.groupby("discount_band").agg(
        total_orders=("order_id", "count"),
        avg_order_value=("final_amount", "mean"),
        total_revenue=("final_amount", "sum"),
    ).reset_index()
    fig = px.bar(disc_summary, x="discount_band", y="total_revenue", title="Revenue by Discount Band")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 15 Restaurants by Net Revenue")
    top_rest = (
        filtered.groupby("restaurant_id")
        .agg(total_orders=("order_id", "count"), net_revenue=("final_amount", "sum"), avg_rating=("rating", "mean"))
        .sort_values("net_revenue", ascending=False)
        .head(15)
        .reset_index()
        .merge(restaurants[["restaurant_id", "restaurant_name", "city"]], on="restaurant_id", how="left")
    )
    st.dataframe(top_rest, use_container_width=True)

st.markdown("---")
st.caption("Built with Python, Pandas, PostgreSQL & Streamlit · Full SQL/Power BI version in the repo")
