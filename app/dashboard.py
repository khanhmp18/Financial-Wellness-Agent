import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import importlib.util
import os
if not os.path.exists("data/financial_wellness.db"):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_app", "app/gen_app.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.generate_database()

DB_PATH = "data/financial_wellness.db"

st.set_page_config(
    page_title="Financial Wellness",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0F172A !important;
    color: #E8E6E1 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 20% 0%, rgba(16,185,129,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(6,182,212,0.10) 0%, transparent 60%),
        #0F172A !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
#MainMenu, footer, header { visibility: hidden !important; }
.block-container { padding: 2rem 3rem !important; max-width: 1400px !important; }

h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

.nav-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.2rem 0 2.5rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2.5rem;
}
.nav-logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem; font-weight: 700; color: #E8E6E1;
}
.nav-logo span { color: #10B981; }

.kpi-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 2rem;
}
.kpi-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px; padding: 1.4rem 1.6rem;
    position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}
.kpi-label {
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: rgba(232,230,225,0.4); margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 700; color: #E8E6E1; line-height: 1;
}
.kpi-sub { font-size: 0.75rem; color: rgba(232,230,225,0.35); margin-top: 0.3rem; }

.member-header {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    display: flex; align-items: center; justify-content: space-between;
}
.member-id-display {
    font-family: 'DM Mono', monospace; font-size: 0.85rem;
    color: rgba(232,230,225,0.4); margin-bottom: 0.3rem;
}
.member-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem; font-weight: 600; color: #E8E6E1;
}
.risk-badge {
    display: inline-flex; align-items: center; gap: 0.5rem;
    padding: 0.6rem 1.4rem; border-radius: 100px;
    font-size: 0.85rem; font-weight: 500;
    font-family: 'DM Mono', monospace; letter-spacing: 0.05em;
}
.risk-high { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.35); color: #F87171; }
.risk-medium { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.35); color: #FBB432; }
.risk-low { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.35); color: #34D399; }

.section-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.2rem; font-weight: 600; color: #E8E6E1;
    margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem;
}
.section-title::after {
    content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.07);
}

.panel {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px; padding: 1.8rem;
}

.metric-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.85rem 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.metric-row:last-child { border-bottom: none; }
.metric-name { font-size: 0.82rem; color: rgba(232,230,225,0.5); }
.metric-value { font-family: 'DM Mono', monospace; font-size: 0.9rem; color: #E8E6E1; font-weight: 500; }
.metric-status {
    width: 8px; height: 8px; border-radius: 50%;
    margin-left: 0.6rem; display: inline-block;
}

.guidance-box {
    background: linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,182,212,0.04));
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 20px; padding: 2rem 2.5rem;
    margin-top: 1rem; position: relative; overflow: hidden;
}
.guidance-box::before {
    content: '"'; position: absolute; top: -1rem; left: 1.5rem;
    font-family: 'Playfair Display', serif; font-size: 8rem;
    color: rgba(16,185,129,0.1); line-height: 1;
}
.guidance-label {
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: #10B981; margin-bottom: 1rem;
}
.guidance-text {
    font-size: 0.92rem; line-height: 1.8;
    color: rgba(232,230,225,0.8); position: relative; z-index: 1;
}

.stButton > button {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: #080C14 !important; border: none !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 0.88rem !important;
    padding: 0.75rem 2rem !important; width: 100% !important;
}
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important; color: #E8E6E1 !important;
}
[data-testid="stSelectbox"] label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: rgba(232,230,225,0.35) !important;
}
hr { border-color: rgba(255,255,255,0.06) !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Loaders ───────────────────────────────────────
@st.cache_resource
def load_explainer():
    spec = importlib.util.spec_from_file_location(
        "shap_explainer", "src/04_shap_explainer.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.explain_member

@st.cache_resource
def load_guidance():
    spec = importlib.util.spec_from_file_location(
        "llm_guidance", "src/05_llm_guidance.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_guidance

@st.cache_data
def load_features():
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM member_features", conn)
    conn.close()
    df["member_id"] = df["member_id"].astype(str).str.strip()
    return df

df = load_features()

total     = df["member_id"].nunique()
high      = int((df["risk_tier"] == "High").sum())
medium    = int((df["risk_tier"] == "Medium").sum())
avg_score = round(df["risk_score"].mean(), 1)

# ── Nav ───────────────────────────────────────────
st.markdown("""
<div class="nav-bar">
    <div class="nav-logo">Fin<span>Well</span></div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:4rem 2rem 3rem;">
    <div style="display:inline-block;font-family:'DM Mono',monospace;
         font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;
         color:#10B981;margin-bottom:1.5rem;">
        ✦ Financial Wellness Platform
    </div>
    <h1 style="font-family:'Playfair Display',serif;font-size:3.5rem;
         font-weight:700;line-height:1.1;margin-bottom:1rem;
         letter-spacing:-0.02em;color:#E8E6E1;">
        Member Risk <em style="font-style:italic;color:#10B981;">Intelligence</em><br>Dashboard
    </h1>
    <p style="color:rgba(232,230,225,0.45);font-size:1rem;
         max-width:500px;margin:0 auto;line-height:1.7;">
        AI-powered financial stress detection with personalized
        wellness guidance for every member.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;justify-content:center;gap:4rem;
     padding:2rem 0;border-top:1px solid rgba(255,255,255,0.05);
     border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:3rem;">
    <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif;font-size:2.2rem;
             font-weight:700;color:#E8E6E1;">{total:,}</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
             letter-spacing:0.1em;text-transform:uppercase;
             color:rgba(232,230,225,0.3);margin-top:0.3rem;">Total Members</div>
    </div>
    <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif;font-size:2.2rem;
             font-weight:700;color:#F87171;">{high:,}</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
             letter-spacing:0.1em;text-transform:uppercase;
             color:rgba(232,230,225,0.3);margin-top:0.3rem;">High Risk</div>
    </div>
    <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif;font-size:2.2rem;
             font-weight:700;color:#FBB432;">{medium:,}</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
             letter-spacing:0.1em;text-transform:uppercase;
             color:rgba(232,230,225,0.3);margin-top:0.3rem;">Medium Risk</div>
    </div>
    <div style="text-align:center;">
        <div style="font-family:'Playfair Display',serif;font-size:2.2rem;
             font-weight:700;color:#34D399;">{avg_score}</div>
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
             letter-spacing:0.1em;text-transform:uppercase;
             color:rgba(232,230,225,0.3);margin-top:0.3rem;">Avg Risk Score</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    tier_filter = st.selectbox("Filter by Risk Tier",
                               ["All", "High", "Medium", "Low"])

filtered_df = df if tier_filter == "All" \
    else df[df["risk_tier"] == tier_filter]
filtered_df = filtered_df.sort_values("risk_score", ascending=False)
all_members = filtered_df["member_id"].unique().tolist()

with col2:
    member_id = st.selectbox(
        f"Member ID — {len(all_members):,} members", all_members
    )

with col3:
    month_list = df[df["member_id"] == member_id]["month"].unique()
    month = st.selectbox("Period", sorted(month_list, reverse=True))

# ── Member data ───────────────────────────────────
member_row = df[
    (df["member_id"] == member_id) &
    (df["month"] == month)
]

if member_row.empty:
    st.warning("No data found.")
    st.stop()

row   = member_row.iloc[0]
score = row["risk_score"]
tier  = str(row["risk_tier"])

risk_class = {"High": "risk-high", "Medium": "risk-medium",
              "Low": "risk-low"}.get(tier, "risk-low")

# ── Member header ─────────────────────────────────
st.markdown(f"""
<div class="member-header">
    <div>
        <div class="member-id-display">MEMBER ID: {member_id}</div>
        <div class="member-name">Financial Profile — {month}</div>
    </div>
    <div style="text-align:right;">
        <div class="risk-badge {risk_class}">● {tier} Risk</div>
        <div style="margin-top:0.5rem;font-family:'DM Mono',monospace;
             font-size:0.75rem;color:rgba(232,230,225,0.3);">
            STRESS SCORE: {score:.1f} / 100
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── KPI row ───────────────────────────────────────
gauge_color = ("#EF4444" if score > 60
               else "#F59E0B" if score > 30
               else "#10B981")

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card" style="--accent:#6366F1;">
        <div class="kpi-label">Risk Score</div>
        <div class="kpi-value" style="color:{gauge_color};">{score:.1f}</div>
        <div class="kpi-sub">out of 100</div>
    </div>
    <div class="kpi-card" style="--accent:#EF4444;">
        <div class="kpi-label">Credit Utilization</div>
        <div class="kpi-value" style="color:{'#F87171' if row['credit_utilization']>0.7 else '#34D399'};">
            {row['credit_utilization']:.1%}
        </div>
        <div class="kpi-sub">of credit limit</div>
    </div>
    <div class="kpi-card" style="--accent:#10B981;">
        <div class="kpi-label">Savings Rate</div>
        <div class="kpi-value" style="color:{'#F87171' if row['savings_rate']<0.05 else '#34D399'};">
            {row['savings_rate']:.1%}
        </div>
        <div class="kpi-sub">of income saved</div>
    </div>
    <div class="kpi-card" style="--accent:#F59E0B;">
        <div class="kpi-label">Monthly Spend</div>
        <div class="kpi-value">${row['total_spend']:,.0f}</div>
        <div class="kpi-sub">total this period</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Metrics + Gauge ───────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    def dot(red, yellow):
        if red:    return "#EF4444", "box-shadow:0 0 6px #EF444466"
        if yellow: return "#F59E0B", "box-shadow:0 0 6px #F59E0B66"
        return "#10B981", "box-shadow:0 0 6px #10B98166"

    metrics = [
        ("Total Monthly Spend",
         f"${row['total_spend']:,.2f}", False, False),
        ("Credit Utilization",
         f"{row['credit_utilization']:.1%}",
         row["credit_utilization"] > 0.7,
         row["credit_utilization"] > 0.4),
        ("Savings Rate",
         f"{row['savings_rate']:.1%}",
         row["savings_rate"] < 0.05,
         row["savings_rate"] < 0.1),
        ("Discretionary Ratio",
         f"{row['discretionary_ratio']:.1%}",
         row["discretionary_ratio"] > 0.6,
         row["discretionary_ratio"] > 0.4),
        ("Spending Volatility",
         f"{row['spending_volatility']:.2f}", False, False),
        ("MoM Spend Change",
         f"{row['mom_spend_change']:+.1%}",
         row["mom_spend_change"] > 0.2,
         row["mom_spend_change"] > 0.1),
        ("Overdraft Frequency",
         f"{row['overdraft_frequency']:.0f}x",
         row["overdraft_frequency"] > 3,
         row["overdraft_frequency"] > 1),
    ]

    panel_html = '<div class="panel"><div class="section-title">Key Metrics</div>'
    for name, value, r, y in metrics:
        c, shadow = dot(r, y)
        panel_html += (
            '<div class="metric-row">'
            f'<span class="metric-name">{name}</span>'
            '<span style="display:flex;align-items:center;">'
            f'<span class="metric-value">{value}</span>'
            f'<span class="metric-status" style="background:{c};{shadow};"></span>'
            '</span></div>'
        )
    panel_html += '</div>'
    st.markdown(panel_html, unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Stress Score</div>',
                unsafe_allow_html=True)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 48, "family": "Playfair Display",
                         "color": gauge_color}},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0,
                     "tickfont": {"color": "rgba(232,230,225,0.2)",
                                  "size": 10}},
            "bar":  {"color": gauge_color, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "rgba(16,185,129,0.08)"},
                {"range": [30, 60], "color": "rgba(245,158,11,0.08)"},
                {"range": [60, 100],"color": "rgba(239,68,68,0.08)"}
            ],
            "threshold": {"line": {"color": gauge_color, "width": 2},
                          "thickness": 0.8, "value": score}
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
        margin=dict(t=20, b=0, l=20, r=20),
        font={"color": "#E8E6E1"}
    )
    st.plotly_chart(fig_gauge, use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown(f"""
    <div style="margin-top:0.5rem;">
        <div style="display:flex;justify-content:space-between;
             font-family:'DM Mono',monospace;font-size:0.65rem;
             color:rgba(232,230,225,0.3);margin-bottom:0.5rem;">
            <span>0</span><span>LOW</span>
            <span>MEDIUM</span><span>HIGH</span><span>100</span>
        </div>
        <div style="height:6px;background:rgba(255,255,255,0.05);
             border-radius:100px;overflow:hidden;">
            <div style="height:100%;width:{score}%;
                 background:linear-gradient(90deg,#10B981,{gauge_color});
                 border-radius:100px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Spend History ─────────────────────────────────
st.divider()
st.markdown('<div class="section-title">📈 Spend History</div>',
            unsafe_allow_html=True)

member_history = df[df["member_id"] == member_id].sort_values("month")

fig_spend = go.Figure()
fig_spend.add_trace(go.Scatter(
    x=member_history["month"], y=member_history["total_spend"],
    name="Total Spend", line=dict(color="#6366F1", width=2),
    fill="tozeroy", fillcolor="rgba(99,102,241,0.06)",
    hovertemplate="$%{y:,.0f}<extra>Total</extra>"
))
fig_spend.add_trace(go.Scatter(
    x=member_history["month"], y=member_history["discretionary_spend"],
    name="Discretionary", line=dict(color="#F59E0B", width=2, dash="dot"),
    hovertemplate="$%{y:,.0f}<extra>Discretionary</extra>"
))
fig_spend.add_trace(go.Scatter(
    x=member_history["month"], y=member_history["essential_spend"],
    name="Essential", line=dict(color="#10B981", width=2, dash="dot"),
    hovertemplate="$%{y:,.0f}<extra>Essential</extra>"
))
fig_spend.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=240, margin=dict(t=10, b=30, l=10, r=10),
    font={"color": "rgba(232,230,225,0.5)", "family": "DM Sans"},
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
                font={"size": 11, "color": "rgba(232,230,225,0.5)"},
                bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, showline=False, tickfont={"size": 10}),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
               showline=False, tickprefix="$", tickfont={"size": 10}),
    hovermode="x unified"
)
st.plotly_chart(fig_spend, use_container_width=True,
                config={"displayModeBar": False})

# ── Risk Score Trend ──────────────────────────────
st.markdown('<div class="section-title">📊 Risk Score Trend</div>',
            unsafe_allow_html=True)

fig_risk = go.Figure()
fig_risk.add_hrect(y0=60, y1=100, fillcolor="rgba(239,68,68,0.04)",
                   line_width=0, annotation_text="HIGH",
                   annotation_font_size=9,
                   annotation_font_color="rgba(239,68,68,0.3)")
fig_risk.add_hrect(y0=30, y1=60, fillcolor="rgba(245,158,11,0.04)",
                   line_width=0)
fig_risk.add_trace(go.Scatter(
    x=member_history["month"], y=member_history["risk_score"],
    mode="lines+markers", line=dict(color="#EF4444", width=2.5),
    marker=dict(size=6, color="#EF4444",
                line=dict(color="#0F172A", width=2)),
    fill="tozeroy", fillcolor="rgba(239,68,68,0.05)",
    hovertemplate="%{y:.1f}/100<extra>Risk Score</extra>"
))
fig_risk.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=200, margin=dict(t=10, b=30, l=10, r=10),
    font={"color": "rgba(232,230,225,0.5)", "family": "DM Sans"},
    showlegend=False,
    xaxis=dict(showgrid=False, showline=False, tickfont={"size": 10}),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
               showline=False, range=[0, 105], tickfont={"size": 10}),
    hovermode="x unified"
)
st.plotly_chart(fig_risk, use_container_width=True,
                config={"displayModeBar": False})

# ── AI Guidance ───────────────────────────────────
st.divider()
st.markdown('<div class="section-title">🤖 AI Financial Wellness Guidance</div>',
            unsafe_allow_html=True)

if st.button("✦  Generate Personalized Guidance"):
    with st.spinner("Analyzing financial profile..."):
        try:
            explain_member    = load_explainer()
            generate_guidance = load_guidance()
            result   = explain_member(member_id, month)
            guidance = generate_guidance(result)

            st.markdown(f"""
            <div class="guidance-box">
                <div class="guidance-label">✦ AI Financial Wellness Analysis</div>
                <div class="guidance-text">
                    {guidance.replace(chr(10), '<br><br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">Risk Drivers (SHAP)</div>',
                        unsafe_allow_html=True)

            shap_df = pd.DataFrame(
                result["explanation"].items(),
                columns=["Feature", "Impact"]
            ).sort_values("Impact", key=abs, ascending=True)

            colors = ["#10B981" if v < 0 else "#EF4444"
                      for v in shap_df["Impact"]]

            fig_shap = go.Figure(go.Bar(
                x=shap_df["Impact"], y=shap_df["Feature"],
                orientation="h", marker_color=colors,
                marker_line_width=0,
                hovertemplate="%{x:+.1f} pts<extra>%{y}</extra>"
            ))
            fig_shap.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                font={"color": "rgba(232,230,225,0.5)",
                      "family": "DM Sans", "size": 11},
                xaxis=dict(showgrid=True,
                           gridcolor="rgba(255,255,255,0.04)",
                           zeroline=True,
                           zerolinecolor="rgba(255,255,255,0.1)",
                           zerolinewidth=1, tickfont={"size": 10}),
                yaxis=dict(showgrid=False, tickfont={"size": 10})
            )
            st.plotly_chart(fig_shap, use_container_width=True,
                            config={"displayModeBar": False})

        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Make sure your API key is set in src/05_llm_guidance.py")

# ── Footer ────────────────────────────────────────
st.markdown("""
<div style="margin-top:4rem;padding-top:1.5rem;
     border-top:1px solid rgba(255,255,255,0.05);
     display:flex;justify-content:space-between;align-items:center;">
    <span style="font-family:'Playfair Display',serif;font-size:1rem;
          color:rgba(232,230,225,0.2);">FinWell</span>
    <span style="font-family:'DM Mono',monospace;font-size:0.65rem;
          color:rgba(232,230,225,0.15);letter-spacing:0.1em;">
        FINANCIAL WELLNESS ANALYTICS PLATFORM
    </span>
</div>
""", unsafe_allow_html=True)