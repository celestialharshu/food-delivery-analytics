# Power BI Dashboard — Setup Guide

Power BI Desktop files (`.pbix`) are binary and built interactively — they can't be generated as
code, so this guide walks you through building the dashboard yourself in ~30–45 minutes. Every
visual maps directly to a query in `sql/03_analysis_queries.sql`, so you're really just wiring up
what you've already built.

## 1. Connect Power BI to PostgreSQL

1. Open **Power BI Desktop** → `Get Data` → `More...` → search **PostgreSQL database**.
2. Server: `localhost` (or your DB host), Database: `food_delivery_db`.
3. Choose **Import** mode (DirectQuery also works but Import is faster for a portfolio project).
4. Enter your PostgreSQL username/password when prompted.
5. In the Navigator, select all 4 tables: `orders`, `customers`, `restaurants`, `delivery_partners`.

## 2. Model relationships

Power BI should auto-detect these from the foreign keys, but verify in **Model view**:

| From | To | Type |
|---|---|---|
| `orders.customer_id` | `customers.customer_id` | Many-to-one |
| `orders.restaurant_id` | `restaurants.restaurant_id` | Many-to-one |
| `orders.partner_id` | `delivery_partners.partner_id` | Many-to-one |

## 3. Key DAX measures to create

Right-click `orders` → **New Measure**, and add these (they're the DAX equivalents of the SQL KPIs):

```dax
Total Revenue = SUM(orders[final_amount])

Total Orders = COUNTROWS(orders)

Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

Late Delivery % = 
DIVIDE(
    CALCULATE(COUNTROWS(orders), orders[is_late] = TRUE),
    COUNTROWS(orders)
)

Repeat Customers = 
CALCULATE(
    DISTINCTCOUNT(orders[customer_id]),
    FILTER(
        VALUES(orders[customer_id]),
        CALCULATE(COUNTROWS(orders)) >= 2
    )
)

Repeat Purchase Rate % = DIVIDE([Repeat Customers], DISTINCTCOUNT(orders[customer_id]))

MoM Revenue Growth % = 
VAR CurrMonth = [Total Revenue]
VAR PrevMonth = CALCULATE([Total Revenue], DATEADD('Calendar'[Date], -1, MONTH))
RETURN DIVIDE(CurrMonth - PrevMonth, PrevMonth)
```

> Tip: Create a proper Date/Calendar table (`Model` → `New Table` → `Calendar = CALENDAR(MIN(orders[order_date]), MAX(orders[order_date]))`) and mark it as a Date Table so time-intelligence functions like `DATEADD` work correctly.

## 4. Suggested dashboard pages

**Page 1 — Executive Overview**
- KPI cards: Total Revenue, Total Orders, AOV, Repeat Purchase Rate
- Line chart: Monthly Revenue Trend
- Map or bar chart: Revenue by City
- Donut chart: Revenue by Food Category

**Page 2 — Customer Analytics**
- New vs Returning customers (stacked column, by month)
- CLV distribution (histogram) + Top 20 customers table
- Customer segment breakdown (from RFM query) as a treemap or bar chart

**Page 3 — Operations**
- Avg delivery time & Late Delivery % by city (combo chart)
- Delivery partner leaderboard (table, sortable by late % and rating)
- Peak ordering hours (column chart, 24-hour view)

**Page 4 — Business Insights**
- Discount band vs revenue/order volume (bar chart)
- Top restaurants by net revenue (table)
- City growth rate (bar chart, quarter-over-quarter)

## 5. Slicers to add on every page

`City`, `Food Category`, `Payment Method`, and a Date range slicer (from the Calendar table).

## 6. Publishing (making it visible to recruiters)

Power BI reports normally require a Power BI Pro/login to view, which is a dead end for a resume
link. Two better options — do both if you can:

1. **Power BI Service (real BI workflow)** — `Home` → `Publish` from Power BI Desktop, publish to
   your free workspace. This demonstrates you know the real end-to-end BI publishing flow; link it
   in your resume/portfolio as "Published dashboard (view requires Power BI login)".
2. **Public, no-login demo (recommended for recruiters)** — export key visuals as images/GIFs into
   your GitHub README (see `assets/`), or optionally rebuild the same 4 pages as a free, publicly
   hosted Streamlit app so anyone can open a link with zero setup. See `docs/DEPLOYMENT.md`
   Option C for exactly this.

Either way, **always include screenshots/GIFs of the dashboard in your README** — most recruiters
will look at the image before they'd ever open a live tool.
