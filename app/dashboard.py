import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import importlib.util

DB_PATH = "data/financial_wellness.db"

st.set_page_config(
    page_title="Financial Wellness",
    page_icon="💳",
    layout="wide"
)

# ── Load shap explainer ───────────────────────────
@st.cache_resource
def load_explainer():
    spec = importlib.util.spec_from_file_location(
        "shap_explainer", "src/04_shap_explainer.py"
    )
    shap_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shap_mod)
    return shap_mod.explain_member

# ── Load LLM guidance ─────────────────────────────
@st.cache_resource
def load_guidance():
    spec = importlib.util.spec_from_file_location(
        "llm_guidance", "src/05_llm_guidance.py"
    )
    llm_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(llm_mod)
    return llm_mod.generate_guidance

# ── Load all data ─────────────────────────────────
@st.cache_data
def load_features():
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM member_features", conn)
    conn.close()
    df["member_id"] = df["member_id"].astype(str).str.strip()
    return df

@st.cache_data
def load_dq():
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM data_quality_log", conn)
    conn.close()
    return df

df = load_features()
dq = load_dq()

# ── Sidebar ───────────────────────────────────────
st.sidebar.title("💳 Financial Wellness")
st.sidebar.markdown("---")
st.sidebar.caption(f"Total Members: {df['member_id'].nunique():,}")
st.sidebar.caption(f"Total Records: {len(df):,}")

# ════════════════════════════════════════════════
# MEMBER LOOKUP — Main Page
# ════════════════════════════════════════════════
st.title("💳 Financial Wellness")
st.caption("Member Financial Health & Risk Analysis")

# ── Filters row ───────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    tier_filter = st.selectbox(
        "Filter by Risk Tier",
        ["All", "High", "Medium", "Low"]
    )

# Apply tier filter
if tier_filter == "All":
    filtered_df = df
else:
    filtered_df = df[df["risk_tier"] == tier_filter]

# Sort by risk score so highest risk appears first
filtered_df = filtered_df.sort_values(
    "risk_score", ascending=False
)

# Get all unique members after filter
all_members = filtered_df["member_id"].unique().tolist()

with col2:
    member_id = st.selectbox(
        f"Select Member ID ({len(all_members):,} members)",
        all_members
    )

with col3:
    month_list = df[
        df["member_id"] == member_id
    ]["month"].unique()
    month = st.selectbox(
        "Select Month",
        sorted(month_list, reverse=True)
    )

# ── Member data ───────────────────────────────────
member_row = df[
    (df["member_id"] == member_id) &
    (df["month"] == month)
]

if not member_row.empty:
    row   = member_row.iloc[0]
    score = row["risk_score"]
    tier  = row["risk_tier"]
    color = {
        "High":   "🔴",
        "Medium": "🟡",
        "Low":    "🟢"
    }.get(tier, "⚪")

    st.divider()

    # ── KPI row ───────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Score",   f"{score:.1f} / 100")
    col2.metric("Risk Tier",    f"{color} {tier}")
    col3.metric("Credit Util",  f"{row['credit_utilization']:.1%}")
    col4.metric("Savings Rate", f"{row['savings_rate']:.1%}")

    st.divider()

    # ── Metrics + Gauge ───────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Financial Metrics")
        metrics_data = {
            "Metric": [
                "Total Monthly Spend",
                "Credit Utilization",
                "Savings Rate",
                "Discretionary Ratio",
                "Spending Volatility",
                "MoM Spend Change",
                "Overdraft Frequency"
            ],
            "Value": [
                f"${row['total_spend']:,.2f}",
                f"{row['credit_utilization']:.1%}",
                f"{row['savings_rate']:.1%}",
                f"{row['discretionary_ratio']:.1%}",
                f"{row['spending_volatility']:.2f}",
                f"{row['mom_spend_change']:+.1%}",
                f"{row['overdraft_frequency']:.0f}"
            ],
            "Status": [
                "ℹ️",
                "🔴" if row["credit_utilization"] > 0.7
                     else "🟡" if row["credit_utilization"] > 0.4
                     else "🟢",
                "🔴" if row["savings_rate"] < 0.05
                     else "🟡" if row["savings_rate"] < 0.1
                     else "🟢",
                "🔴" if row["discretionary_ratio"] > 0.6
                     else "🟡" if row["discretionary_ratio"] > 0.4
                     else "🟢",
                "ℹ️",
                "🔴" if row["mom_spend_change"] > 0.2
                     else "🟡" if row["mom_spend_change"] > 0.1
                     else "🟢",
                "🔴" if row["overdraft_frequency"] > 3
                     else "🟡" if row["overdraft_frequency"] > 1
                     else "🟢"
            ]
        }
        st.dataframe(
            pd.DataFrame(metrics_data),
            hide_index=True,
            use_container_width=True
        )

    with col2:
        st.subheader("Risk Gauge")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Financial Stress Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": "#6366f1"},
                "steps": [
                    {"range": [0,  30], "color": "#dcfce7"},
                    {"range": [30, 60], "color": "#fef9c3"},
                    {"range": [60, 100],"color": "#fee2e2"}
                ],
                "threshold": {
                    "line":      {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value":     60
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # ── Spend History ─────────────────────────────
    st.divider()
    st.subheader("📈 Member Spend History")
    member_history = df[
        df["member_id"] == member_id
    ].sort_values("month")

    fig = px.line(
        member_history,
        x="month",
        y=["total_spend", "discretionary_spend",
           "essential_spend"],
        markers=True,
        labels={"value": "Amount ($)",
                "month": "Month",
                "variable": "Category"},
        color_discrete_map={
            "total_spend":         "#6366f1",
            "discretionary_spend": "#f59e0b",
            "essential_spend":     "#22c55e"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Risk Score History ────────────────────────
    st.subheader("📊 Risk Score History")
    fig2 = px.line(
        member_history,
        x="month",
        y="risk_score",
        markers=True,
        color_discrete_sequence=["#ef4444"],
        labels={"risk_score": "Risk Score",
                "month": "Month"}
    )
    fig2.add_hrect(y0=60, y1=100, fillcolor="red",
                   opacity=0.05,
                   annotation_text="High Risk Zone")
    fig2.add_hrect(y0=30, y1=60, fillcolor="orange",
                   opacity=0.05,
                   annotation_text="Medium Risk Zone")
    st.plotly_chart(fig2, use_container_width=True)

    # ── AI Guidance ───────────────────────────────
    st.divider()
    st.subheader("🤖 AI Financial Wellness Guidance")

    if st.button("Generate AI Guidance", type="primary"):
        with st.spinner("Analyzing member profile..."):
            try:
                explain_member    = load_explainer()
                generate_guidance = load_guidance()
                result   = explain_member(member_id, month)
                guidance = generate_guidance(result)
                st.success(guidance)

                st.subheader("Top Risk Drivers (SHAP)")
                shap_df = pd.DataFrame(
                    result["explanation"].items(),
                    columns=["Feature", "Impact"]
                ).sort_values("Impact",
                              key=abs,
                              ascending=True)
                fig = px.bar(
                    shap_df,
                    x="Impact",
                    y="Feature",
                    orientation="h",
                    color="Impact",
                    color_continuous_scale=[
                        "green", "white", "red"
                    ],
                    color_continuous_midpoint=0
                )
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error generating guidance: {e}")
                st.info(
                    "Make sure your API key is set in "
                    "src/05_llm_guidance.py"
                )