import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import subprocess
import sys


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="IMDb Movie Analytics",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0b0d10;
    color: #ffffff;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: #111318;
    border-right: 1px solid #252932;
}

.sidebar-logo {
    font-size: 30px;
    font-weight: 800;
    color: #f5c518;
    margin-bottom: 30px;
}

.sidebar-text {
    color: #8d939f;
    font-size: 13px;
}

/* Main header */

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 4px;
}

.main-subtitle {
    color: #8d939f;
    font-size: 14px;
    margin-bottom: 25px;
}

/* KPI cards */

.metric-card {
    background: #15181e;
    border: 1px solid #252932;
    border-radius: 14px;
    padding: 20px;
    min-height: 125px;
}

.metric-title {
    color: #8d939f;
    font-size: 13px;
    margin-bottom: 10px;
}

.metric-value {
    color: #ffffff;
    font-size: 30px;
    font-weight: 800;
}

.metric-icon {
    font-size: 20px;
}

/* Movie cards */

.movie-card {
    background: #15181e;
    border: 1px solid #252932;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
}

.movie-rank {
    color: #f5c518;
    font-size: 13px;
    font-weight: 700;
}

.movie-name {
    color: #ffffff;
    font-size: 17px;
    font-weight: 700;
    margin-top: 4px;
}

.movie-year {
    color: #858b96;
    font-size: 12px;
    margin-top: 4px;
}

.rating-badge {
    background: #20242b;
    border-radius: 10px;
    padding: 20px 10px;
    text-align: center;
    margin-bottom: 10px;
}

.rating-badge-value {
    color: #f5c518;
    font-size: 17px;
    font-weight: 800;
}

/* Section headings */

.section-title {
    font-size: 21px;
    font-weight: 700;
    color: #ffffff;
    margin-top: 25px;
    margin-bottom: 15px;
}

/* Update button */

div.stButton > button {
    background: #f5c518;
    color: #111318;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    padding: 10px 18px;
}

div.stButton > button:hover {
    background: #ffd84d;
    color: #111318;
}

/* Footer */

.footer {
    text-align: center;
    color: #666d78;
    font-size: 12px;
    margin-top: 40px;
    padding: 20px;
    border-top: 1px solid #252932;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-logo">IMDb</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-text">Movie Analytics Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("### Filters")

    min_rating = st.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1
    )

    min_year = st.slider(
        "Release Year",
        min_value=1900,
        max_value=2026,
        value=1900
    )

    st.markdown("---")

    st.caption("Data Source")
    st.write("IMDb Top 250")


# =========================================================
# HEADER
# =========================================================

header_col1, header_col2 = st.columns([5, 1.5])

with header_col1:

    st.markdown(
        '<div class="main-title">Movie Analytics</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="main-subtitle">'
        'IMDb Top 250 Movie Analysis'
        '</div>',
        unsafe_allow_html=True
    )


with header_col2:

    update_button = st.button(
        "🔄 Update IMDb Data",
        use_container_width=True
    )


# =========================================================
# RUN SCRAPER
# =========================================================

if update_button:

    with st.spinner("Updating IMDb Top 250 data..."):

        try:

            result = subprocess.run(
                [sys.executable, "scraper.py"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:

                st.success(
                    "IMDb data updated successfully!"
                )

                st.rerun()

            else:

                st.error(
                    "The scraper encountered an error."
                )

                if result.stderr:
                    st.code(result.stderr)

        except Exception as e:

            st.error(
                f"Unable to run scraper: {e}"
            )


# =========================================================
# SEARCH
# =========================================================

search = st.text_input(
    "🔎 Search movies",
    placeholder="Search by movie title..."
)


# =========================================================
# LOAD CSV
# =========================================================

try:

    df = pd.read_csv("imdb_top_250.csv")

except FileNotFoundError:

    st.error(
        "imdb_top_250.csv not found. Run scraper.py first."
    )

    st.stop()


# =========================================================
# DATA CLEANING
# =========================================================

df["Rank"] = pd.to_numeric(
    df["Rank"],
    errors="coerce"
)

df["Year"] = pd.to_numeric(
    df["Year"],
    errors="coerce"
)

df["Rating"] = pd.to_numeric(
    df["Rating"],
    errors="coerce"
)

df["Title"] = df["Title"].astype(str).str.strip()

df = df.dropna(
    subset=["Rank", "Title", "Year", "Rating"]
)

df["Rank"] = df["Rank"].astype(int)
df["Year"] = df["Year"].astype(int)

df = df.drop_duplicates(
    subset=["Rank"]
)

df = df.sort_values(
    "Rank"
)


# =========================================================
# SEARCH + FILTER
# =========================================================

filtered_df = df[
    (df["Rating"] >= min_rating) &
    (df["Year"] >= min_year)
].copy()


if search:

    filtered_df = filtered_df[
        filtered_df["Title"]
        .str.contains(
            search,
            case=False,
            na=False
        )
    ]


# =========================================================
# KPI VALUES
# =========================================================

total_movies = len(filtered_df)

if total_movies > 0:

    average_rating = filtered_df["Rating"].mean()
    highest_rating = filtered_df["Rating"].max()
    latest_release = filtered_df["Year"].max()

else:

    average_rating = 0
    highest_rating = 0
    latest_release = 0


# =========================================================
# KPI CARDS
# =========================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL MOVIES</div>
            <div class="metric-value">{total_movies}</div>
            <div class="metric-icon">🎬</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">AVERAGE RATING</div>
            <div class="metric-value">{average_rating:.2f}</div>
            <div class="metric-icon">⭐</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">HIGHEST RATING</div>
            <div class="metric-value">{highest_rating:.1f}</div>
            <div class="metric-icon">🏆</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">LATEST RELEASE</div>
            <div class="metric-value">{latest_release}</div>
            <div class="metric-icon">📅</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# TOP RATED MOVIES
# =========================================================

st.markdown(
    '<div class="section-title">Top Rated Movies</div>',
    unsafe_allow_html=True
)

top_movies = filtered_df.head(5)


for _, movie in top_movies.iterrows():

    card_col1, card_col2 = st.columns([3.5, 1])

    with card_col1:

        st.markdown(
            f'<div class="movie-card">'
            f'<div class="movie-rank">#{int(movie["Rank"])}</div>'
            f'<div class="movie-name">{movie["Title"]}</div>'
            f'<div class="movie-year">{int(movie["Year"])}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with card_col2:

        st.markdown(
            f'<div class="rating-badge">'
            f'<div class="rating-badge-value">'
            f'⭐ {movie["Rating"]:.1f}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )


# =========================================================
# CHART SECTION
# =========================================================

chart_col1, chart_col2 = st.columns(2)


# =========================================================
# RATING OVERVIEW
# =========================================================

with chart_col1:

    st.markdown(
        '<div class="section-title">Rating Overview</div>',
        unsafe_allow_html=True
    )

    rating_df = filtered_df.sort_values("Rank")

    fig_rating = go.Figure()

    fig_rating.add_trace(
        go.Scatter(
            x=rating_df["Rank"],
            y=rating_df["Rating"],
            mode="lines+markers",
            name="IMDb Rating",
            line=dict(width=2),
            marker=dict(size=5)
        )
    )

    fig_rating.update_layout(
        template="plotly_dark",
        height=350,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="Rank",
        yaxis_title="Rating",
        paper_bgcolor="#15181e",
        plot_bgcolor="#15181e"
    )

    st.plotly_chart(
        fig_rating,
        use_container_width=True
    )


# =========================================================
# RATING DISTRIBUTION
# =========================================================

with chart_col2:

    st.markdown(
        '<div class="section-title">Rating Distribution</div>',
        unsafe_allow_html=True
    )

    fig_distribution = px.histogram(
        filtered_df,
        x="Rating",
        nbins=15
    )

    fig_distribution.update_layout(
        template="plotly_dark",
        height=350,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="IMDb Rating",
        yaxis_title="Number of Movies",
        paper_bgcolor="#15181e",
        plot_bgcolor="#15181e"
    )

    st.plotly_chart(
        fig_distribution,
        use_container_width=True
    )


# =========================================================
# MOVIES BY YEAR
# =========================================================

st.markdown(
    '<div class="section-title">Movies by Release Year</div>',
    unsafe_allow_html=True
)

year_df = (
    filtered_df
    .groupby("Year")
    .size()
    .reset_index(name="Movies")
)

fig_year = px.area(
    year_df,
    x="Year",
    y="Movies"
)

fig_year.update_layout(
    template="plotly_dark",
    height=350,
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis_title="Release Year",
    yaxis_title="Number of Movies",
    paper_bgcolor="#15181e",
    plot_bgcolor="#15181e"
)

st.plotly_chart(
    fig_year,
    use_container_width=True
)


# =========================================================
# TOP 10 MOVIES
# =========================================================

st.markdown(
    '<div class="section-title">Top 10 Movies</div>',
    unsafe_allow_html=True
)

top10 = filtered_df.head(10).sort_values(
    "Rating",
    ascending=True
)

fig_top10 = px.bar(
    top10,
    x="Rating",
    y="Title",
    orientation="h",
    text="Rating"
)

fig_top10.update_layout(
    template="plotly_dark",
    height=450,
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis_title="IMDb Rating",
    yaxis_title="",
    paper_bgcolor="#15181e",
    plot_bgcolor="#15181e"
)

fig_top10.update_traces(
    texttemplate="%{text:.1f}",
    textposition="outside"
)

st.plotly_chart(
    fig_top10,
    use_container_width=True
)


# =========================================================
# MOVIE DATABASE
# =========================================================

st.markdown(
    '<div class="section-title">Movie Database</div>',
    unsafe_allow_html=True
)

st.dataframe(
    filtered_df[
        ["Rank", "Title", "Year", "Rating"]
    ],
    use_container_width=True,
    hide_index=True
)


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        IMDb Movie Analytics Dashboard · Built with Python,
        Selenium, Pandas, Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True
)