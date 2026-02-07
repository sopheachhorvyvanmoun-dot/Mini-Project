import re
import pandas as pd
import streamlit as st

import db
from db import init_db, insert_order, fetch_latest
from datetime import timedelta

st.set_page_config(page_title="Form → Postgres", page_icon="🧾")

init_db()

# Cloud concept: Idempotency - safe to run multiple times
try:
    db.init_db()
except Exception as e:
    st.error("Database initialization failed.")
    st.exception(e)
    st.stop()


st.title("🧾 Form → Neon Postgres")

with st.form("submission_form", clear_on_submit=True):

    customer_id = st.text_input("Customer ID", placeholder=("e.g., C0001"))
    order_date = st.date_input("Order Date")

    status = st.selectbox(
        "Status",
        ["Paid", "Shipped", "Received", "Refunded", "Canceled", "N/A"]
    )

    channel = st.selectbox(
        "Channel",
        ["Partner", "Social", "Website", "Walkin", "App"]
    )

    total_amount = st.text_input("Total Amount (USD)")
    discount_pct = st.text_input("Discount (%)")

    payment_method = st.selectbox(
        "Payment Method",
        ["Card", "Cash", "Bank Transfer", "E-Wallet"]
    )

    region = st.selectbox("Region", ["PP", "KD", "SR", "BB", "KC", "PS", "PV", "SV", "KP", "KK", "ST"])

    submitted = st.form_submit_button("Save Order")

# ---------- Validation ----------
if submitted:

    errors = []

    customer_id = customer_id.strip().upper()

    if not customer_id:
        errors.append("Customer ID required.")

    ship_date = order_date + timedelta(days=7)

    try:
        total_amount_val = float(total_amount)
        if total_amount_val <= 0:
            errors.append("Amount must be > 0")
    except:
        errors.append("Invalid amount")

    try:
        discount_val = float(discount_pct) if discount_pct else 0
        if not (0 <= discount_val <= 100):
            errors.append("Discount must be 0–100")
    except:
        errors.append("Invalid discount")

    if errors:
        for e in errors:
            st.error(e)

    else:
        new_id = insert_order(
            customer_id,
            order_date,
            ship_date,
            status,
            channel,
            total_amount_val,
            discount_val,
            payment_method,
            region
        )

        st.success(
            f"Saved! Order ID = {new_id} | Ship Date = {ship_date}"
        )

# ---------- Display ----------
st.divider()
st.subheader("Latest Orders")

rows = fetch_latest()

if rows:
    st.dataframe(pd.DataFrame(rows))
else:
    st.info("No data yet")
