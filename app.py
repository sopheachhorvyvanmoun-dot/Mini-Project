import re
import pandas as pd
import streamlit as st
from db import init_db, insert_order, fetch_latest
from datetime import timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Orders → Postgres", page_icon="🛒")

init_db()

st.title("🛒 Orders → Neon Postgres")
st.caption("Sumit your order. Data will be saved to Postgres and shown below.")

with st.form("submission_form", clear_on_submit=True):

    customer_id = st.text_input("Customer ID", placeholder=("e.g., C0001"))
    order_date = st.date_input("Order Date")

    status = st.selectbox(
        "Status",
        ["Pending", "Processing", "Shipped", "Received", "Refunded", "Canceled", "N/A"]
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
st.subheader("🛒 Latest Orders")

rows = fetch_latest()

if rows:

    df = pd.DataFrame(rows)

    # Ensure date column is datetime
    df["order_date"] = pd.to_datetime(df["order_date"])

    # --- Aggregations ---
    revenue_by_day = (
        df.groupby("order_date")["total_amount_usd"]
        .sum()
        .reset_index()
        .rename(columns={"total_amount_usd": "revenue"})
    )

    orders_by_day = (
        df.groupby("order_date")["order_id"]
        .count()
        .reset_index()
    )

    # --- Create Side-by-Side Charts ---
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Revenue by day (from latest 200 orders)",
            "Orders by day (from latest 200 orders)"
        )
    )

    # Revenue scatter (like screenshot)
    fig.add_trace(
        go.Scatter(
            x=revenue_by_day["order_date"],
            y=revenue_by_day["revenue"],
            mode="markers",
            marker=dict(size=12),
            name="Revenue"
        ),
        row=1, col=1
    )

    # Orders bar
    fig.add_trace(
        go.Bar(
            x=orders_by_day["order_date"],
            y=orders_by_day["order_id"],
            name="Orders"
        ),
        row=1, col=2
    )

    fig.update_layout(
        template="plotly_dark",
        height=450,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Show Table ---
    st.dataframe(df)

else:
    st.info("No data yet")
