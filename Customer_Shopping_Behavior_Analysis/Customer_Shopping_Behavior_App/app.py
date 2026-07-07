import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Customer Shopping Behavior Analysis",
    page_icon="🛍️",
    layout="wide",
)

# ── Load & clean data ───────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent.parent / "customer_shopping_behavior.csv"
    df = pd.read_csv(csv_path)

    # Fill missing Review Rating with category-wise median (same as notebook)
    df["Review Rating"] = df.groupby("Category")["Review Rating"].transform(
        lambda x: x.fillna(x.median())
    )

    # Rename to snake_case for easier handling internally
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"\(|\)", "", regex=True)
    )

    # Age group segmentation
    bins = [17, 25, 35, 50, 70]
    labels = ["Young Adult (18-25)", "Adult (26-35)", "Middle-aged (36-50)", "Senior (51-70)"]
    df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels)

    # Customer segment
    def segment(p):
        if p == 1:
            return "New"
        elif p <= 10:
            return "Returning"
        else:
            return "Loyal"

    df["customer_segment"] = df["previous_purchases"].apply(segment)

    return df


df = load_data()

# ── Sidebar filters ─────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

subscription_options = ["All"] + sorted(df["subscription_status"].unique().tolist())
gender_options = ["All"] + sorted(df["gender"].unique().tolist())
category_options = ["All"] + sorted(df["category"].unique().tolist())
shipping_options = ["All"] + sorted(df["shipping_type"].unique().tolist())

selected_subscription = st.sidebar.selectbox("Subscription Status", subscription_options)
selected_gender = st.sidebar.selectbox("Gender", gender_options)
selected_category = st.sidebar.multiselect("Category", sorted(df["category"].unique().tolist()), default=sorted(df["category"].unique().tolist()))
selected_shipping = st.sidebar.multiselect("Shipping Type", sorted(df["shipping_type"].unique().tolist()), default=sorted(df["shipping_type"].unique().tolist()))

# Apply filters
filtered = df.copy()
if selected_subscription != "All":
    filtered = filtered[filtered["subscription_status"] == selected_subscription]
if selected_gender != "All":
    filtered = filtered[filtered["gender"] == selected_gender]
if selected_category:
    filtered = filtered[filtered["category"].isin(selected_category)]
if selected_shipping:
    filtered = filtered[filtered["shipping_type"].isin(selected_shipping)]

# ── Title ───────────────────────────────────────────────────────────────────────
st.title("🛍️ Customer Shopping Behavior Analysis")
st.markdown("An end-to-end analysis of **3,900 customers** covering purchasing patterns, revenue, segmentation, and loyalty trends.")
st.markdown("---")

# ── KPI Cards ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Avg Purchase Amount", f"${filtered['purchase_amount_usd'].mean():.2f}")
col2.metric("⭐ Avg Review Rating", f"{filtered['review_rating'].mean():.2f} / 5.0")
col3.metric("👥 Total Customers", f"{len(filtered):,}")
col4.metric("📦 Subscription Rate", f"{(filtered['subscription_status'] == 'Yes').mean() * 100:.1f}%")

st.markdown("---")

# ── Tabs ────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🧍 Customer Segments", "🛒 Products & Revenue", "🔎 SQL Insights"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ══════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Revenue & Sales Overview")

    c1, c2 = st.columns(2)

    # Revenue by Category
    rev_cat = filtered.groupby("category")["purchase_amount_usd"].sum().reset_index()
    rev_cat.columns = ["Category", "Total Revenue (USD)"]
    fig1 = px.bar(rev_cat, x="Category", y="Total Revenue (USD)", color="Category",
                  title="Revenue by Category", text_auto=".2s")
    fig1.update_layout(showlegend=False)
    c1.plotly_chart(fig1, use_container_width=True)

    # Sales Volume by Category
    sales_cat = filtered["category"].value_counts().reset_index()
    sales_cat.columns = ["Category", "Number of Purchases"]
    fig2 = px.bar(sales_cat, x="Category", y="Number of Purchases", color="Category",
                  title="Sales Volume by Category", text_auto=True)
    fig2.update_layout(showlegend=False)
    c2.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    # Revenue by Age Group
    rev_age = filtered.groupby("age_group", observed=True)["purchase_amount_usd"].sum().reset_index()
    rev_age.columns = ["Age Group", "Total Revenue (USD)"]
    fig3 = px.bar(rev_age, x="Age Group", y="Total Revenue (USD)", color="Age Group",
                  title="Revenue by Age Group", text_auto=".2s")
    fig3.update_layout(showlegend=False)
    c3.plotly_chart(fig3, use_container_width=True)

    # Subscription status pie
    sub_counts = filtered["subscription_status"].value_counts().reset_index()
    sub_counts.columns = ["Status", "Count"]
    fig4 = px.pie(sub_counts, names="Status", values="Count",
                  title="% Customers by Subscription Status",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    c4.plotly_chart(fig4, use_container_width=True)

    c5, c6 = st.columns(2)

    # Revenue by Gender
    rev_gender = filtered.groupby("gender")["purchase_amount_usd"].sum().reset_index()
    rev_gender.columns = ["Gender", "Total Revenue (USD)"]
    fig5 = px.bar(rev_gender, x="Gender", y="Total Revenue (USD)", color="Gender",
                  title="Revenue by Gender", text_auto=".2s")
    fig5.update_layout(showlegend=False)
    c5.plotly_chart(fig5, use_container_width=True)

    # Purchase amount distribution
    fig6 = px.histogram(filtered, x="purchase_amount_usd", nbins=30,
                        title="Distribution of Purchase Amounts",
                        labels={"purchase_amount_usd": "Purchase Amount (USD)"},
                        color_discrete_sequence=["#636EFA"])
    c6.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 — Customer Segments
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Customer Segmentation")

    c1, c2 = st.columns(2)

    # Customer segment breakdown
    seg_counts = filtered["customer_segment"].value_counts().reset_index()
    seg_counts.columns = ["Segment", "Count"]
    fig7 = px.pie(seg_counts, names="Segment", values="Count",
                  title="Customer Segments (New / Returning / Loyal)",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    c1.plotly_chart(fig7, use_container_width=True)

    # Repeat buyers vs subscription
    repeat_sub = filtered[filtered["previous_purchases"] > 5].groupby("subscription_status")["customer_id"].count().reset_index()
    repeat_sub.columns = ["Subscription Status", "Repeat Buyers"]
    fig8 = px.bar(repeat_sub, x="Subscription Status", y="Repeat Buyers", color="Subscription Status",
                  title="Repeat Buyers (>5 Purchases) by Subscription Status", text_auto=True)
    fig8.update_layout(showlegend=False)
    c2.plotly_chart(fig8, use_container_width=True)

    c3, c4 = st.columns(2)

    # Avg spend: Subscribed vs Not
    sub_spend = filtered.groupby("subscription_status").agg(
        avg_spend=("purchase_amount_usd", "mean"),
        total_revenue=("purchase_amount_usd", "sum"),
        total_customers=("customer_id", "count")
    ).reset_index()
    fig9 = px.bar(sub_spend, x="subscription_status", y="avg_spend", color="subscription_status",
                  title="Avg Spend: Subscribed vs Non-Subscribed",
                  labels={"subscription_status": "Subscription Status", "avg_spend": "Avg Purchase (USD)"},
                  text_auto=".2f")
    fig9.update_layout(showlegend=False)
    c3.plotly_chart(fig9, use_container_width=True)

    # Payment method distribution
    pay_counts = filtered["payment_method"].value_counts().reset_index()
    pay_counts.columns = ["Payment Method", "Count"]
    fig10 = px.bar(pay_counts, x="Payment Method", y="Count", color="Payment Method",
                   title="Most Used Payment Methods", text_auto=True)
    fig10.update_layout(showlegend=False)
    c4.plotly_chart(fig10, use_container_width=True)

    c5, c6 = st.columns(2)

    # Purchase frequency
    freq_counts = filtered["frequency_of_purchases"].value_counts().reset_index()
    freq_counts.columns = ["Frequency", "Count"]
    fig11 = px.bar(freq_counts, x="Frequency", y="Count", color="Frequency",
                   title="Purchase Frequency Distribution", text_auto=True)
    fig11.update_layout(showlegend=False, xaxis_tickangle=-30)
    c5.plotly_chart(fig11, use_container_width=True)

    # Season-wise sales
    season_counts = filtered.groupby("season")["purchase_amount_usd"].sum().reset_index()
    season_counts.columns = ["Season", "Total Revenue (USD)"]
    fig12 = px.pie(season_counts, names="Season", values="Total Revenue (USD)",
                   title="Revenue by Season",
                   color_discrete_sequence=px.colors.qualitative.Safe)
    c6.plotly_chart(fig12, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 3 — Products & Revenue
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Product Performance")

    c1, c2 = st.columns(2)

    # Top 5 products by avg review rating
    top_rated = (
        filtered.groupby("item_purchased")["review_rating"]
        .mean()
        .reset_index()
        .sort_values("review_rating", ascending=False)
        .head(10)
    )
    top_rated.columns = ["Product", "Avg Rating"]
    fig13 = px.bar(top_rated, x="Avg Rating", y="Product", orientation="h",
                   title="Top 10 Products by Avg Review Rating",
                   color="Avg Rating", color_continuous_scale="Teal", text_auto=".2f")
    fig13.update_layout(yaxis={"categoryorder": "total ascending"})
    c1.plotly_chart(fig13, use_container_width=True)

    # Top 5 products by discount usage rate
    discount_rate = filtered.groupby("item_purchased").apply(
        lambda x: round(100.0 * (x["discount_applied"] == "Yes").sum() / len(x), 2)
    ).reset_index()
    discount_rate.columns = ["Product", "Discount Rate (%)"]
    discount_rate = discount_rate.sort_values("Discount Rate (%)", ascending=False).head(10)
    fig14 = px.bar(discount_rate, x="Discount Rate (%)", y="Product", orientation="h",
                   title="Top 10 Products by Discount Usage Rate (%)",
                   color="Discount Rate (%)", color_continuous_scale="Oranges", text_auto=".1f")
    fig14.update_layout(yaxis={"categoryorder": "total ascending"})
    c2.plotly_chart(fig14, use_container_width=True)

    # Top 3 products per category
    st.subheader("Top 3 Products per Category")
    item_counts = (
        filtered.groupby(["category", "item_purchased"])["customer_id"]
        .count()
        .reset_index()
    )
    item_counts.columns = ["Category", "Product", "Total Orders"]
    item_counts["Rank"] = item_counts.groupby("Category")["Total Orders"].rank(
        method="first", ascending=False
    )
    top3 = item_counts[item_counts["Rank"] <= 3].sort_values(["Category", "Rank"])

    fig15 = px.bar(top3, x="Total Orders", y="Product", color="Category",
                   facet_col="Category", orientation="h",
                   title="Top 3 Most Purchased Products per Category",
                   text_auto=True)
    fig15.update_layout(showlegend=False)
    st.plotly_chart(fig15, use_container_width=True)

    # Avg purchase: Standard vs Express shipping
    st.subheader("Shipping Type Analysis")
    ship_avg = filtered.groupby("shipping_type")["purchase_amount_usd"].mean().reset_index()
    ship_avg.columns = ["Shipping Type", "Avg Purchase (USD)"]
    fig16 = px.bar(ship_avg, x="Shipping Type", y="Avg Purchase (USD)", color="Shipping Type",
                   title="Avg Purchase Amount by Shipping Type", text_auto=".2f")
    fig16.update_layout(showlegend=False)
    st.plotly_chart(fig16, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 4 — SQL Insights
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("SQL Business Insights")
    st.markdown("Results from the 10 SQL queries — replicated using Pandas.")

    # Q1
    with st.expander("Q1 — Total Revenue by Gender"):
        q1 = filtered.groupby("gender")["purchase_amount_usd"].sum().reset_index()
        q1.columns = ["Gender", "Total Revenue (USD)"]
        st.dataframe(q1, use_container_width=True)

    # Q2
    with st.expander("Q2 — Discount Users Who Spent Above Average"):
        avg_purchase = filtered["purchase_amount_usd"].mean()
        q2 = filtered[(filtered["discount_applied"] == "Yes") & (filtered["purchase_amount_usd"] >= avg_purchase)][["customer_id", "purchase_amount_usd"]]
        q2.columns = ["Customer ID", "Purchase Amount (USD)"]
        st.write(f"Average purchase amount: **${avg_purchase:.2f}**")
        st.dataframe(q2.reset_index(drop=True), use_container_width=True)

    # Q3
    with st.expander("Q3 — Top 5 Products by Avg Review Rating"):
        q3 = (
            filtered.groupby("item_purchased")["review_rating"]
            .mean()
            .round(2)
            .reset_index()
            .sort_values("review_rating", ascending=False)
            .head(5)
        )
        q3.columns = ["Product", "Avg Review Rating"]
        st.dataframe(q3.reset_index(drop=True), use_container_width=True)

    # Q4
    with st.expander("Q4 — Avg Purchase: Standard vs Express Shipping"):
        q4 = (
            filtered[filtered["shipping_type"].isin(["Standard", "Express"])]
            .groupby("shipping_type")["purchase_amount_usd"]
            .mean()
            .round(2)
            .reset_index()
        )
        q4.columns = ["Shipping Type", "Avg Purchase (USD)"]
        st.dataframe(q4, use_container_width=True)

    # Q5
    with st.expander("Q5 — Do Subscribed Customers Spend More?"):
        q5 = filtered.groupby("subscription_status").agg(
            Total_Customers=("customer_id", "count"),
            Avg_Spend=("purchase_amount_usd", "mean"),
            Total_Revenue=("purchase_amount_usd", "sum")
        ).round(2).reset_index()
        q5.columns = ["Subscription Status", "Total Customers", "Avg Spend (USD)", "Total Revenue (USD)"]
        st.dataframe(q5, use_container_width=True)

    # Q6
    with st.expander("Q6 — Top 5 Products by Discount Usage Rate"):
        q6 = filtered.groupby("item_purchased").apply(
            lambda x: round(100.0 * (x["discount_applied"] == "Yes").sum() / len(x), 2)
        ).reset_index()
        q6.columns = ["Product", "Discount Rate (%)"]
        q6 = q6.sort_values("Discount Rate (%)", ascending=False).head(5).reset_index(drop=True)
        st.dataframe(q6, use_container_width=True)

    # Q7
    with st.expander("Q7 — Customer Segments (New / Returning / Loyal)"):
        q7 = filtered["customer_segment"].value_counts().reset_index()
        q7.columns = ["Customer Segment", "Number of Customers"]
        st.dataframe(q7, use_container_width=True)

    # Q8
    with st.expander("Q8 — Top 3 Products per Category"):
        q8 = (
            filtered.groupby(["category", "item_purchased"])["customer_id"]
            .count()
            .reset_index()
        )
        q8.columns = ["Category", "Product", "Total Orders"]
        q8["Rank"] = q8.groupby("Category")["Total Orders"].rank(method="first", ascending=False).astype(int)
        q8 = q8[q8["Rank"] <= 3].sort_values(["Category", "Rank"]).reset_index(drop=True)
        st.dataframe(q8, use_container_width=True)

    # Q9
    with st.expander("Q9 — Repeat Buyers (>5 Purchases) vs Subscription"):
        q9 = (
            filtered[filtered["previous_purchases"] > 5]
            .groupby("subscription_status")["customer_id"]
            .count()
            .reset_index()
        )
        q9.columns = ["Subscription Status", "Repeat Buyers"]
        st.dataframe(q9, use_container_width=True)

    # Q10
    with st.expander("Q10 — Revenue Contribution by Age Group"):
        q10 = (
            filtered.groupby("age_group", observed=True)["purchase_amount_usd"]
            .sum()
            .reset_index()
            .sort_values("purchase_amount_usd", ascending=False)
        )
        q10.columns = ["Age Group", "Total Revenue (USD)"]
        st.dataframe(q10.reset_index(drop=True), use_container_width=True)

# ── Raw Data ────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📋 View Raw Data"):
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
    st.caption(f"Showing {len(filtered):,} rows after filters")
