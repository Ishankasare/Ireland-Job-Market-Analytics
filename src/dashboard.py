# ============================================================
# Ireland Job Market Analytics — Streamlit Dashboard
# ============================================================
# Author:      [Your Name]
# Run with:    streamlit run src/dashboard.py
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Ireland Job Market Analytics",
    page_icon="🇮🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }
    .main { background-color: #0f1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border: 1px solid #2e3250;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4f8ef7;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8892b0;
        margin-top: 4px;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e6f1ff;
        border-left: 4px solid #4f8ef7;
        padding-left: 12px;
        margin: 24px 0 16px 0;
    }
    .insight-box {
        background: #1a1d2e;
        border-left: 3px solid #4f8ef7;
        border-radius: 8px;
        padding: 16px 20px;
        color: #ccd6f6;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Data loading ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    db_path = "data/jobs.db"
    if not os.path.exists(db_path):
        # Load from latest CSV if DB not available
        csv_files = sorted([
            f for f in os.listdir("data/processed") if f.endswith(".csv")
        ], reverse=True)
        if csv_files:
            return pd.read_csv(f"data/processed/{csv_files[0]}")
        else:
            return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM jobs", conn)
    conn.close()
    return df


df = load_data()

if df.empty:
    st.error("No data found. Run `python src/scraper.py` first to collect job data.")
    st.stop()


# ── Sidebar filters ──────────────────────────────────────────
st.sidebar.image("https://img.shields.io/badge/Ireland-Job%20Market-4f8ef7?style=for-the-badge", use_column_width=True)
st.sidebar.markdown("## Filters")

job_types = ["All"] + sorted(df["job_type"].dropna().unique().tolist())
selected_type = st.sidebar.selectbox("Job Type", job_types)

sources = ["All"] + sorted(df["source"].dropna().unique().tolist())
selected_source = st.sidebar.selectbox("Source", sources)

seniorities = ["All"] + sorted(df["seniority"].dropna().unique().tolist())
selected_seniority = st.sidebar.selectbox("Seniority", seniorities)

# Apply filters
filtered = df.copy()
if selected_type != "All":
    filtered = filtered[filtered["job_type"] == selected_type]
if selected_source != "All":
    filtered = filtered[filtered["source"] == selected_source]
if selected_seniority != "All":
    filtered = filtered[filtered["seniority"] == selected_seniority]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(filtered):,}** listings match your filters")
st.sidebar.markdown(f"Last updated: {df['scraped_at'].max()[:10] if 'scraped_at' in df.columns else 'N/A'}")


# ── Header ───────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#e6f1ff; font-size:2.2rem; font-weight:700; margin-bottom:4px;'>
    🇮🇪 Ireland Data Job Market Analytics
</h1>
<p style='color:#8892b0; font-size:1rem; margin-bottom:32px;'>
    Real-time scraping of Data Analyst, Data Science & Internship roles from Indeed.ie and Jobs.ie
</p>
""", unsafe_allow_html=True)


# ── KPI Row ──────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

metrics = [
    (col1, len(filtered), "Total Listings"),
    (col2, filtered["company"].nunique(), "Unique Companies"),
    (col3, len(filtered[filtered["job_type"] == "Internship / Graduate"]), "Internship Roles"),
    (col4, len(filtered[filtered["salary_clean"] != "Not specified"]), "Roles with Salary"),
    (col5, filtered["source"].nunique(), "Sources Scraped"),
]

for col, value, label in metrics:
    with col:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{value:,}</div>
            <div class='metric-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Row 1: Job Type + Seniority ──────────────────────────────
st.markdown("<div class='section-header'>Role Breakdown</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    job_type_counts = filtered["job_type"].value_counts().reset_index()
    job_type_counts.columns = ["Job Type", "Count"]
    fig = px.bar(
        job_type_counts, x="Count", y="Job Type", orientation="h",
        color="Count", color_continuous_scale="Blues",
        title="Listings by Job Type"
    )
    fig.update_layout(
        plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
        font_color="#ccd6f6", showlegend=False,
        coloraxis_showscale=False, height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    seniority_counts = filtered["seniority"].value_counts().reset_index()
    seniority_counts.columns = ["Seniority", "Count"]
    fig = px.pie(
        seniority_counts, names="Seniority", values="Count",
        title="Seniority Distribution",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig.update_layout(
        plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
        font_color="#ccd6f6", height=350
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Row 2: Top Companies ─────────────────────────────────────
st.markdown("<div class='section-header'>Top Hiring Companies</div>", unsafe_allow_html=True)

top_companies = filtered["company"].value_counts().head(20).reset_index()
top_companies.columns = ["Company", "Open Roles"]

fig = px.bar(
    top_companies, x="Open Roles", y="Company", orientation="h",
    color="Open Roles", color_continuous_scale="Blues",
    title="Top 20 Companies Hiring Data Roles in Ireland"
)
fig.update_layout(
    plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
    font_color="#ccd6f6", coloraxis_showscale=False,
    height=500, yaxis={"categoryorder": "total ascending"}
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
<div class='insight-box'>
    💡 <strong>Insight:</strong> Companies hiring across multiple data role types signal large, mature data teams —
    these are typically better environments for interns and junior hires to learn and grow quickly.
</div>
""", unsafe_allow_html=True)


# ── Row 3: Skills Demand ─────────────────────────────────────
st.markdown("<div class='section-header'>Most In-Demand Skills</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

def get_skill_counts(data):
    all_skills = []
    for skills in data["skills_mentioned"].dropna():
        all_skills.extend([s.strip() for s in skills.split(",") if s.strip()])
    return pd.Series(all_skills).value_counts().reset_index()

with col1:
    skill_counts = get_skill_counts(filtered)
    skill_counts.columns = ["Skill", "Mentions"]
    skill_counts = skill_counts.head(15)

    fig = px.bar(
        skill_counts, x="Mentions", y="Skill", orientation="h",
        color="Mentions", color_continuous_scale="Blues",
        title="Top 15 Skills Across All Data Roles"
    )
    fig.update_layout(
        plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
        font_color="#ccd6f6", coloraxis_showscale=False,
        height=450, yaxis={"categoryorder": "total ascending"}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    intern_data = filtered[filtered["job_type"] == "Internship / Graduate"]
    if not intern_data.empty:
        intern_skills = get_skill_counts(intern_data)
        intern_skills.columns = ["Skill", "Mentions"]
        intern_skills = intern_skills.head(15)

        fig = px.bar(
            intern_skills, x="Mentions", y="Skill", orientation="h",
            color="Mentions", color_continuous_scale="Greens",
            title="Top Skills for Internship / Graduate Roles"
        )
        fig.update_layout(
            plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
            font_color="#ccd6f6", coloraxis_showscale=False,
            height=450, yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No internship listings in current filter selection.")


# ── Row 4: Location ──────────────────────────────────────────
st.markdown("<div class='section-header'>Location & Work Model</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    def extract_city(loc):
        if not isinstance(loc, str):
            return "Not Specified"
        loc = loc.lower()
        if "dublin" in loc: return "Dublin"
        if "cork" in loc: return "Cork"
        if "limerick" in loc: return "Limerick"
        if "galway" in loc: return "Galway"
        if "waterford" in loc: return "Waterford"
        if "remote" in loc: return "Remote"
        if "hybrid" in loc: return "Hybrid"
        return "Other"

    filtered["city"] = filtered["location"].apply(extract_city)
    city_counts = filtered["city"].value_counts().reset_index()
    city_counts.columns = ["City", "Listings"]

    fig = px.pie(
        city_counts, names="City", values="Listings",
        title="Listings by Location",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig.update_layout(
        plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
        font_color="#ccd6f6", height=380
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    source_counts = filtered["source"].value_counts().reset_index()
    source_counts.columns = ["Source", "Listings"]

    fig = px.bar(
        source_counts, x="Source", y="Listings",
        color="Listings", color_continuous_scale="Blues",
        title="Listings by Source"
    )
    fig.update_layout(
        plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
        font_color="#ccd6f6", coloraxis_showscale=False,
        height=380
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Row 5: Raw Data Table ────────────────────────────────────
st.markdown("<div class='section-header'>Browse All Listings</div>", unsafe_allow_html=True)

display_cols = ["title", "company", "location", "job_type", "seniority", "salary_clean", "skills_mentioned", "source", "posted"]
available_cols = [c for c in display_cols if c in filtered.columns]

search = st.text_input("🔍 Search by title, company or skill", "")
table_data = filtered[available_cols].copy()
if search:
    mask = table_data.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
    table_data = table_data[mask]

table_data.columns = [c.replace("_", " ").title() for c in table_data.columns]
st.dataframe(table_data, use_container_width=True, height=400)

# Download button
csv = filtered.to_csv(index=False)
st.download_button(
    label="⬇️ Download Full Dataset as CSV",
    data=csv,
    file_name=f"ireland_data_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# ── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style='color:#8892b0; font-size:0.85rem; text-align:center;'>
    Data scraped from Indeed.ie and Jobs.ie · Refreshed weekly via GitHub Actions ·
    Built with Python, SQLite, Streamlit & Plotly
</p>
""", unsafe_allow_html=True)
