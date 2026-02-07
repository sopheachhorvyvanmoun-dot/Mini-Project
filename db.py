import os
import psycopg2
import psycopg2.extras

def get_db_url():
    # Cloud concept: Configuration outside code (Secrets)
    # 1) Local/server environment variable
    url = os.environ.get("NEON_DB")
    if url:
        return url

    # 2) Streamlit Cloud Secrets
    try:
        import streamlit as st
        url = st.secrets.get("NEON_DB")
        if url:
            return url
    except Exception:
        pass

    return None

DB_URL = get_db_url()
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS orders (
  order_id SERIAL PRIMARY KEY,
  customer_id TEXT NOT NULL,
  order_date DATE NOT NULL DEFAULT CURRENT_DATE,
  ship_date DATE NOT NULL,
  status TEXT NOT NULL,
  channel TEXT NOT NULL,
  total_amount_usd NUMERIC NOT NULL,
  discount_pct NUMERIC DEFAULT 0,
  payment_method TEXT NOT NULL,
  region TEXT NOT NULL
);
"""

INSERT_SQL = """
INSERT INTO orders
(customer_id, order_date, ship_date, status, channel,
 total_amount_usd, discount_pct, payment_method, region)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
RETURNING order_id;
"""

SELECT_LATEST_SQL = """
SELECT *
FROM orders
ORDER BY order_id DESC
LIMIT %s;
"""

def get_conn():
    if not DB_URL:
        raise ValueError("NEON_DB is not set.")
    return psycopg2.connect(DB_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()

def insert_order(customer_id, order_date, ship_date,
                 status, channel, total_amount_usd,
                 discount_pct, payment_method, region):

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                INSERT_SQL,
                (customer_id, order_date, ship_date, status,
                 channel, total_amount_usd, discount_pct,
                 payment_method, region)
            )
            return cur.fetchone()[0]

def fetch_latest(limit=50):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SELECT_LATEST_SQL, (limit,))
            return cur.fetchall()
