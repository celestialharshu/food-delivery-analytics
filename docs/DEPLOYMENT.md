# Deployment Guide

"Deploying" an analytics project means two different things, and a strong resume project does
both:

1. **The database layer** — PostgreSQL needs to be running somewhere your SQL queries and Power BI
   can hit it.
2. **A shareable artifact** — something a recruiter can open with **one click, no login, no
   install** to see the work is real.

Below are three options, from "just run it locally" to "put a live link on my resume."

---

## Option A — Local setup (fastest, good for development)

**Tech:** PostgreSQL (local install) + Power BI Desktop (Windows) or pgAdmin

```bash
# 1. Install PostgreSQL (skip if already installed)
#    macOS:   brew install postgresql@16
#    Ubuntu:  sudo apt install postgresql postgresql-contrib
#    Windows: https://www.postgresql.org/download/windows/

# 2. Create the database
createdb food_delivery_db

# 3. Generate the synthetic dataset
cd food-delivery-analytics
pip install -r requirements.txt
python src/generate_data.py --orders 100000

# 4. Clean it
python src/data_cleaning.py

# 5. Build schema + load data
psql -U postgres -d food_delivery_db -f sql/01_schema.sql
psql -U postgres -d food_delivery_db -f sql/02_load_data.sql

# 6. Run the analysis queries
psql -U postgres -d food_delivery_db -f sql/03_analysis_queries.sql

# 7. Open Power BI Desktop → connect to food_delivery_db (see powerbi/POWERBI_GUIDE.md)
```

This is enough to demo the project live in an interview from your own laptop.

---

## Option B — Docker (recommended: reproducible, looks great on a resume)

Being able to say *"fully containerized with Docker"* is itself a resume line. This spins up
PostgreSQL in a container and auto-loads your data on first boot.

**`docker-compose.yml`** (already included in the project root):

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:16
    container_name: food_delivery_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: food_delivery_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql/01_schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
volumes:
  pgdata:
```

```bash
docker compose up -d          # starts PostgreSQL, auto-runs 01_schema.sql on first boot
python src/generate_data.py --orders 100000
python src/data_cleaning.py
psql -h localhost -U postgres -d food_delivery_db -f sql/02_load_data.sql
```

Power BI connects to `localhost:5432` exactly as in Option A.

**Cloud variant:** push the same Postgres container to a free-tier managed host —
[Supabase](https://supabase.com), [Railway](https://railway.app), or
[Render](https://render.com/docs/deploy-postgresql) all offer free PostgreSQL instances. Point
Power BI / psql at the hosted connection string instead of `localhost`. This means the database is
live 24/7, not just on your machine — worth doing if you want to demo this in a live interview
without setup.

---

## Option C — A public, no-login web dashboard (best single link for your resume)

Power BI reports need a Power BI account to view, which is friction for a recruiter. The highest
leverage thing you can do is rebuild the 4 dashboard pages as a lightweight **Streamlit** app and
deploy it for free — this gives you one URL that opens instantly for anyone.

```bash
pip install streamlit plotly sqlalchemy psycopg2-binary
```

A starter `app.py` is included at the project root — it reads the same cleaned CSVs (or connects to
your Postgres DB) and renders the Executive Overview, Customer, Operations, and Business pages as
interactive Plotly charts.

**Deploy for free** on any of:
- **[Streamlit Community Cloud](https://streamlit.io/cloud)** — connect your GitHub repo, pick
  `app.py`, click deploy. Free, gets you a public `*.streamlit.app` URL in ~2 minutes.
- **[Render](https://render.com)** — free web service tier, deploy from GitHub.
- **[Railway](https://railway.app)** — similar, also has a free Postgres add-on so the whole stack
  (DB + app) lives in one place.

Put this URL directly in your resume/LinkedIn next to the project title. This is what actually
gets clicked.

---

## Recommended combo for a resume project

1. **GitHub repo** (this whole folder) — shows the code, SQL, and process.
2. **Docker Compose** for the database — shows you understand real deployment, not just scripts.
3. **Streamlit Cloud link** — the one-click, no-login demo recruiters will actually open.
4. **Power BI Desktop screenshots/GIFs in the README** — shows you can use the specific enterprise
   BI tool the job description probably asks for.

That combination covers "I can build it," "I can deploy it," and "I can show it" — the three things
a hiring manager is actually checking for.
