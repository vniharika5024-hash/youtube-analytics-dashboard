import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

#PAGE CONIGURATION
st.set_page_config(
    page_title = "YouTube Global Statistics",
    page_icon = "▶",
    layout="wide",
    initial_sidebar_state="expanded",
)

#CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #e63946;
    border-radius: 12px;
    padding: 14px 18px;
    height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-times: center;
    text-align: center;
    color: white;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #e63946;

    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-label{
    font-size: 0.82rem;
    color: #adb5bd;
    text-transform: uppercase;
    letter-spacing: 1px;
    line-height: 1.5;
    min-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 10px;
}
.feature-badge {
    display: inline-block;
    background: #e63946;
    color: white;
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 5px 14px;
    border-radius: 4px;
    margin-bottom: 6px;    
}
.feature-desc {
    font-size: 0.85rem;
    color: #6c757d;
    margin-bottom: 12px;
}
.cascade-note {
    background: #fff8e1;
    border-left: 4px solid #ffc107;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 0.82rem;
    color: #555;
    margin-bottom: 8px;
}
.sidebar-title {
    font-family: 'syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #e63946;
}
</style>   
""", unsafe_allow_html=True)

#Cleaned dataset loading
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("global-youtube_cleaned.csv", encoding="latin-1")
        return df

    except FileNotFoundError:
        df = pd.read_csv("Global YouTube Statistics.csv", encoding="latin-1")
        df.columns = (
            df.columns.str.strip().str.lower()
            .str.replace(" ","_").str.replace(r"[^\w]","_",regex=True)
        )
        num_cols = [
            "subscribers", "video_views", "uploads", "lowest_monthly_earnings",
            "highest_monthly_earnings", "lowest_yearly_earnings","highest_yearly_earnings",
            "subscribers_for_last_30","created_year","latitude", "longitude", "population", "unemploymnent_rate", "urban_population",
        ]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["subscribers", "video_views"])
        if "category" in df.columns:
            df = df[df["category"].notna()]
            df["category"] = df["category"].astype(str).str.strip().str.title()

        if "avg_monthly_earnings" not in df.columns:
            if "lowest_monthly_earnings" in df.columns and "highest_monthly_earnings" in df.columns:
                df["avg_monthly_earnings"] = (
                    df["lowest_monthly_earnings"] + df["highest_monthly_earnings"]
                ) / 2
        
        if "avg_yearly_earnings" not in df.columns:
            if "lowest_yearly_earnings" in df.columns and "highest_yearly_earnings" in df.columns:
                df["avg_yearly_earnings"] = (
                    df["lowest_yearly_earnings"] + df["highest_yearly_earnings"]
                ) / 2
                
        if "views_per_subscriber" not in df.columns:
            df["views_per_subscriber"] = df["video_views"] / df["subscribers"].replace(0, np.nan)
            
        if "channel_age_years" not in df.columns and "created_year" in df.columns:
            df["channel_age_years"] = 2023 - df["created_year"]

        return df

def fmt_big(n) -> str:
    if pd.isna(n):
        return "N/A"
    if n >= 1e9:
        return f"{n/1e9:.2f}B"
    if n >= 1e6:
        return f"{n/1e6:.1f}M"
    if n >= 1e3:
        return f"{n/1e3:.1f}K"
    return f"{n:,.0f}"

df = load_data()

#SIDEBAR (Cascading filters)

st.sidebar.markdown('<p class="sidebar-title">▶ Dashboard Controls</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Cascading Filters")
st.sidebar.caption(
    "**Step 1 → 2 cascade:** The country list below updates automatically"
    "to show only countries that have channels in your selected categories."
)

# LEVEL 1 - Categories (filter)
all_categories = sorted(df["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "① Content Category",
    options=all_categories,
    default=all_categories[:8],
    help="Select categories. The country filter below will cascade to match.",
)

#Applying category filter FIRST and this drives the cascading country options
df_cat = df[df["category"].isin(selected_categories)] if selected_categories else df.copy()

#LEVEL 2 - Country (child filter, options derived from Level 1 results)
if "country" in df_cat.columns:
    available_countries = sorted(df_cat["country"].dropna().unique().tolist())
    st.sidebar.markdown(
        '<div class="cascade-note">'
        '↳ Countries below are limited to those with channels in the selcted categories above'
        '</div>',
        unsafe_allow_html=True,
    )
    selected_countries = st.sidebar.multiselect(
        "② Country 🌐",
        options=available_countries,
        default=available_countries[:15],
        help="Only countries present in the selected categories are listed here.",
    )
    df_filtered = (
        df_cat[df_cat["country"].isin(selected_countries)]
        if selected_countries else df_cat.copy()       
    )
else:
    df_filtered = df_cat.copy()

# Subscriber range   
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Dynamic Configuration")
st.sidebar.caption("Customise analysis parameters - charts update instantly.")

sub_min = int(df["subscribers"].min())
sub_max = int(df["subscribers"].max())
sub_range = st.sidebar.slider(
    "👥 Subscribers Rage",
    min_value=sub_min, max_value=sub_max,
    value=(sub_min, sub_max), format="%d",
    help = "All Charts update to this range.",
)
df_filtered = df_filtered[
    (df_filtered["subscribers"] >= sub_range[0])
    & (df_filtered["subscribers"] <= sub_range[1])
]

top_n = st.sidebar.slider(
    " Top-N Channels in Charts", min_value=5, max_value=50, value=15, step=5,
    help="Controls how many channels appear in ranked bar charts.",

)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👁 Conditional Sections")
st.sidebar.caption("Toggle entire sections on or off")
show_earnings = st.sidebar.checkbox("Earnings Analysis 💰", value=True)
show_map = st.sidebar.checkbox("Geographic View 🗺️", value=True)
show_growth = st.sidebar.checkbox("Growth & Trends 📈", value=True)
show_estimator = st.sidebar.checkbox("Earning Estimator 🔧", value=True)

st.sidebar.markdown("---")
n_match = len(df_filtered)
if n_match == 0:
    st.sidebar.error("⚠️ No Channels match the applied filters. Widen your selection")
else:
    st.sidebar.success(f"**{n_match:,}** channels match current filters")
                       

# Header
st.markdown("""
<h1 style='font-family:Syne, sans-serif; font-size: 2.4rem; margin-bottom:0; color:#e63946;'>
▶ Global Youtube Statistics
</h1>
<p style='color:#6c757d; margin-top:4px; font-size:1rem'>
Interactive analytics dashboard · World's top Youtube channels &nbsp;|&nbsp;
<em>IS41570 Assignment · UCD iSchool · Spring 2026</em>
</p>
""", unsafe_allow_html=True)
st.markdown("---")

#Empty-state gaurd
if n_match == 0:
    st.warning(
        "⚠️ No channels match your current filter combination."
        "Please expand your category or country selections in the sidebar."
    )
                       
    st.stop()

#TABS
tab1, tab2, tab3 = st.tabs([
    "📊 Page 1 - Channel Intelligence",
    "💰 Page 2 - Earnings & Geography Insights",
    "📈 Page 3 - Growth & Trends Insights",
])

#TAB 1 - Channel Intelligence
with tab1:
    
    st.markdown("""
    <h2 style='font-family:Syne,sans-serif; margin-bottom:2px;'>📊 Channel Intelligence</h2>
    <p style='color:#6c757d; font-size:0.9rem; margin-top:0;'>
    who are the top channels and what content performs best?
    </p>
    """, unsafe_allow_html=True)
    
    #Advanced Feature: Summary Metrics
    st.markdown('<span class="feature-badge">Advanced Feature: Summary Metrics</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="feature-desc">Five KPIs that recalculates in real time with every filter change.</p>',
        unsafe_allow_html=True,
    )
    
    total_subs  = df_filtered["subscribers"].sum()
    total_views = df_filtered["video_views"].sum()
    avg_monthly = (
        df_filtered["avg_monthly_earnings"].median()
        if "avg_monthly_earnings" in df_filtered.columns else np.nan
        )
    top_category = df_filtered["category"].value_counts().idxmax()
    metrics = [
        (f"{n_match:,}", "Channels in View"),
        (fmt_big(total_subs), "Total Subscribers"),
        (fmt_big(total_views), "Total Video Views"),
        (top_category,  "Largest Category"),
    ]
    for col, (val, label) in zip(st.columns(4), metrics):
        col.markdown(
            f"""<div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
                </div>""",
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    
    #Connected Visualisations
    st.markdown("---")
    st.markdown('<span class="feature-badge">Connected Visualisations</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="feature-desc">'
        'All three charts below share the same filtered dataset. A single sidebar change'
        'updates all of them simultaneously which provides multiple perspective on the same data slice.'
        '</p>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Top Channels by Subscribers")
        top_ch = df_filtered.nlargest(top_n, "subscribers")
        y_col = "youtuber" if "youtuber" in top_ch.columns else top_ch.index.astype(str)
        fig_bar = px.bar(
            top_ch, x="subscribers", y=y_col, orientation="h",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"subscribers": "Subscribers", "youtuber": "Channel"},
            template="plotly_dark",
        )
        fig_bar.update_traces(width=0.42)
        fig_bar.update_layout(
            height=520,
            yaxis={"categoryorder": "total ascending"},
            
            margin=dict(l=5, r=5, t=30, b=5),
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117", legend=dict(
                orientation="v",
                yanchor="top",
                x=0.98,
                xanchor="left",
                y=0.98,
                font=dict(size=9, color="white"),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0
            ),
            legend_title_text=""
            
        )
        fig_bar.update_xaxes(tickformat=".2s", color="white")
        fig_bar.update_yaxes(color="white")
        st.plotly_chart(fig_bar, use_container_width=True)
            
    with c2:
        st.subheader("Category Share (Donut)")
        cat_cnt = df_filtered["category"].value_counts().reset_index()
        cat_cnt.columns = ["category", "count"]
        fig_pie = px.pie(
            cat_cnt, names="category", values="count", hole=0.36,
            color_discrete_sequence=px.colors.qualitative.Bold,
            template="plotly_dark",
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            height=520, margin=dict(l=5, r=5, t=30, b=5),
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            legend=dict(font=dict(size=9, color="white"),
        ))
        st.plotly_chart(fig_pie, use_container_width=True)

            
    #Third connected chart with colour axis configuration
    st.subheader("Views vs Subscribers - Scatter (log-log)")
    st.caption(
        "Each dot is one channel and both axes are log base 10 scale so the full size range is visible."
        "Hover for next figures."
    )
    colour_options = ["category"] + (
        ["channel_type"] if "channel_type" in df_filtered.columns else []

    )
    colour_by = st.radio(
        "Colour points by:",
        options=["category"] + (["channel_type"] if "channel_type" in df_filtered.columns else []),
        horizontal=True, key="scatter_colour",
    )
    sc_df = df_filtered.dropna(subset=["subscribers", "video_views"]).copy()
    sc_df["log_subs"]  = np.log10(sc_df["subscribers"].replace(0, np.nan))
    sc_df["log_views"] = np.log10(sc_df["video_views"].replace(0, np.nan))
    fig_sc = px.scatter(
        sc_df, x="log_subs", y="log_views",
        color=colour_by if colour_by in sc_df.columns else "category",
        hover_name="youtuber" if "youtuber" in sc_df.columns else None,
        hover_data={
            "subscribers": ":,.0f", "video_views": ":,.0f",
            "log_subs": False, "log_views": False,
        },
        labels={"log_subs": "log₁₀(Subscribers)", "log_views": "log₁₀(Video Views)"},
        color_discrete_sequence=px.colors.qualitative.Bold,
        template="plotly_dark", opacity=0.75,
    )
    fig_sc.update_traces(marker_size=7)
    fig_sc.update_layout(
        height=440, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        margin=dict(l=5, r=5, t=30, b=5),
        legend=dict(font=dict(size=10, color="white")),
    )
    st.plotly_chart(fig_sc, use_container_width=True)
    

# TAB 2 - Earnings💰 & Geography🗺
with tab2:
    st.markdown("""
    <h2 style='font-family:Syne,sans-serif; margin-bottom:2px;'>
    💰 Earnings <span style='color:#e63946;'>&</span> Geography
    </h2>
    <p style='color:#6c757d; fot-size:0.9rem; margin-top:0;'>
    Where are channels based and how much do they earn?
    Use the sidebar toggles to show or hide individual sections.
    </p>
    """, unsafe_allow_html=True)
    # Conditional content - Geographical Map
    if show_map and "country" in df_filtered.columns:
        st.markdown("---")
        st.markdown('<span class="feature-badge">Conditional Content - Geographical View</span>', unsafe_allow_html=True)
        st.markdown(
            '<p class="feature-desc">'
            '<strong>Type: Boolean Control</strong> - togglable via sidebar.'
            'Also includes an inline <strong>dynamic configuration</strong> radio to switch the map metric.'
            '</p>',
            unsafe_allow_html=True,
        )
        country_agg = (
            df_filtered.groupby("country")
            .agg(
                channel_count=("subscribers", "count"),
                total_subscribers=("subscribers", "sum"),
            )
            .reset_index()
        )
        if "avg_monthly_earnings" in df_filtered.columns:
            ea = (
                df_filtered.groupby("country")["avg_monthly_earnings"]
                .median().reset_index()
            )
            ea.columns = ["country", "median_monthly_earnings"]
            country_agg = country_agg.merge(ea, on="country", how="left")
            map_cols = {
                "channel_count": "Number of Channels",
                "total_subscribers": "Total Subscribers"
            }
            if "median_monthly_earnings" in country_agg.columns:
                map_cols["median_monthly_earnings"] = "Median Monthly Earnings"
            map_metric = st.radio(
                "Choropleth colour metric:",
                list(map_cols.keys()),
                format_func=lambda x: map_cols[x],
                horizontal=True,
            )

            st.subheader("🗺 Country-Level Chloropleth")
            fig_map = px.choropleth(
                country_agg, locations="country", locationmode="country names",
                color=map_metric, hover_name="country",
                labels={k: v for k, v in map_cols.items()},
            )
            fig_map.update_layout(
                height=480,
                geo=dict(showframe=False, showcoastlines=True, bgcolor="#0d1117"),
                paper_bgcolor="#0d1117", margin=dict(l=0, r=0, t=30, b=0),
                coloraxis_colorbar=dict(title=""),
            )
            st.plotly_chart(fig_map, use_container_width=True)
            if "latitude" in df_filtered.columns and "longitude" in df_filtered.columns:
                st.subheader("📍 Channel Locations - Bubble Map")
                st.caption("Bubble size = subscriber count. Colour = content category.")
                map_df = df_filtered.dropna(subset = ["latitude", "longitude"])
                fig_bubble = px.scatter_geo(
                    map_df,
                    lat="latitude", lon="longitude",
                    size="subscribers", color="category",
                    hover_name="youtuber" if "youtuber" in map_df.columns else None,
                    hover_data={"subscribers": ":,.0f", "latitude": False, "longitude": False},
                    size_max=30,
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    template="plotly_dark",
                )
                fig_bubble.update_layout(
                    height=460,
                    geo=dict(showframe=False, showcoastlines=True, bgcolor="#0d1117"),
                    paper_bgcolor="#0d1117",
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig_bubble, use_container_width=True)

        #Conditional data on Earnings
        if show_earnings and "avg_monthly_earnings" in df_filtered.columns:
            st.markdown("---")
            st.markdown('<span class="feature-badge">Conditional content - Earnings Analysis</span>', unsafe_allow_html=True)
            st.markdown(
                '<p class="feature-desc">'
                '<strong>Type: Boolean Control</strong> - this section appears only when "Earnings Analysis" '
                'is checked in the sidebar. Uncheck it to hide this content entierly.'
                '</p>',
                unsafe_allow_html=True,
            )

            earn_df = df_filtered.dropna(subset = ["avg_monthly_earnings"])
            earn_df = earn_df[earn_df["avg_monthly_earnings"] > 0]

            if len(earn_df) == 0:
                st.info("No earnings data available for the current filter selection.")
            else:
                e1, e2 = st.columns(2)

                with e1:
                    st.subheader("Median Monthly Earnings by Category")
                    earn_cat = (
                        earn_df.groupby("category")["avg_monthly_earnings"]
                        .median().sort_values(ascending=True).reset_index()
                    )
                    fig_earn = px.bar(
                        earn_cat, x="avg_monthly_earnings", y="category", orientation="h",
                        color="avg_monthly_earnings", color_continuous_scale= "Reds",
                        labels={"avg_monthly_earnings": "Median Monthly Earnings (USD)", "category": ""},
                        template="plotly_dark",
                    )
                    fig_earn.update_layout(
                        height=430, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                        coloraxis_showscale=False, margin=dict(l=5, r=5, t=30, b=5),
                    )
                    fig_earn.update_xaxes(tickformat="$,.0f")
                    st.plotly_chart(fig_earn, use_container_width=True)
                            
                with e2:
                    st.subheader("Earnings Distribution - Box Plot")
                    top_cats_e = earn_df["category"].value_counts().head(8).index
                    box_df = earn_df[earn_df["category"].isin(top_cats_e)]
                    order_e = (
                        box_df.groupby("category")["avg_monthly_earnings"]
                        .median().sort_values(ascending=False).index.tolist()
                    )
                    fig_box = px.box(
                        box_df, x="category", y="avg_monthly_earnings",
                        color="category", category_orders={"category": order_e},
                        color_discrete_sequence=px.colors.qualitative.Bold,
                        log_y=True,
                        labels={"avg_monthly_earnings": "Monthly Earnings USD (log)", "category": ""},
                        template="plotly_dark",
                    )
                    fig_box.update_layout(
                        height=430, showlegend=False,
                        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                        margin=dict(l=5, r=5, t=30, b=5),
                    )
                    fig_box.update_xaxes(tickangle=30)
                    st.plotly_chart(fig_box, use_container_width=True)
                    
#TAB 3 - Growth and Trend Insights + Interactive table
with tab3:
    st.markdown("""
    <h2 style='font-family:Syne,sans-serif; margin-bottom:2px;'>
    📈 Growth<span style='color:#e63946;'>&</span>Trends Insights
    </h2>
    <p style='color:#6c757d; fot-size:0.9rem; margin-top:0;'>
    How has the YouTube crreator landscape evolved with time?
    Use the sidebar toggles to show or hide individual sections.
    </p>
    """, unsafe_allow_html=True)
    #Conditional Content -> Growth and trends
    if show_growth and "created_year" in df_filtered.columns:
        st.markdown("---")
        st.markdown('<span class="feature-badge">Conditional Content - Trends & Growth</span>', unsafe_allow_html=True)
        st.markdown(
            '<p class="feature-desc">'
            '<strong>Type: Analysis Mode Switching</strong> - uses a radio button to switch between'
            'two different chart types for the same underlying temporal data.'
            '</p>',
            unsafe_allow_html=True,
        )

        trend_mode = st.radio(
            "Select analysis mode:",
            ["📈 Channel Creation per Year (Line)", "Subscriber Heatmap by Era 🔥"],
            horizontal=True, key="trend_mode",
        )

        if "📈" in trend_mode:
            st.subheader("Top-Channel Creation per Year (2005-2022)")
            yr = df_filtered["created_year"].dropna().astype(int)
            yr = yr[(yr >= 2005) & (yr <= 2022)]

            if len(yr) == 0:
                st.info("No creation year data for the current filter.")
            else:
                yc = yr.value_counts().sort_index().reset_index()
                yc.columns = ["year", "count"]
                fig_line = px.line(
                    yc, x="year", y="count", markers=True,
                    color_discrete_sequence=["#e63946"],
                    labels={"year": "Year Created", "count": "Channels Created"},
                    template="plotly_dark",
                )
                fig_line.update_traces(line_width=3, marker_size=9)
                fig_line.update_layout(
                    height=380, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    margin=dict(l=5, r=5, t=30, b=5),
                )
                fig_line.add_annotation(
                    text="⚠ 2023 excluded - snapshot year<br>(not a full year of data)",
                    xref="paper", yref="paper", x=0.99, y=0.98,
                    showarrow=False, font=dict(size=10, color="#adb5bd"), align="right",
                )
                st.plotly_chart(fig_line, use_container_width=True)
                st.caption(
                    "2023 is the snapshot year for this dataset; it is excluded from the line chart"
                    "because it does not represent a full year of channel creations."
                )

        else:
            st.subheader("Median Subscribers by Category & Creation Era - Heatmap")
            hm = df_filtered.dropna(subset=["created_year", "category"]).copy()
            hm["era"] = pd.cut(
                hm["created_year"],
                bins=[2004, 2008, 2012, 2016, 2020, 2023],
                labels=["2005-08", "2009-12", "2013-16", "2017-20", "2021-23"],
            )
            pivot = hm.pivot_table(
                index="category", columns="era", values="subscribers", aggfunc="median"
            ).dropna(how="all")

            if pivot.empty:
                st.info("Not enough data for the heatmap with current filter.")
            else:
                fig_heat = px.imshow(
                    pivot / 1e6,
                    color_continuous_scale="YlOrRd",
                    aspect="auto", text_auto=".1f",
                    labels={"color": "Median Subs (M)", "x": "Creation Era", "y": "Category"},
                    template="plotly_dark",
                )
                fig_heat.update_layout(
                    height=500, paper_bgcolor="#0d1117",
                    margin=dict(l=5, r=5, t=30, b=5),
                    coloraxis_colorbar=dict(title="Median Subs (M)"),
                )
                st.plotly_chart(fig_heat, use_container_width=True)

    # Conditional Content + Advanced Feature -> Dynamic Configuration
    if show_estimator:
        st.markdown("---")
        st.markdown(
            '<span class="feature-badge">Conditional Content + Advanced Feature: Dynamic Configuration - Earnings Estimator</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="feature-desc">'
            '<strong>Type: Dynamic Configuration</strong> - user customisable analysis parameters.'
            'Adjust CPM, monetisation rate, and category in real time to model estimated channel earnings.'
            'Also functions as <strong>conditional content</strong> via sidebar checkbox toggle.'
            '</p>',
            unsafe_allow_html=True,
        )

        cfg1, cfg2, cfg3 = st.columns(3)
        with cfg1:
            custom_cpm = st.slider(
                "CPM Rate (USD / 1,000 views)", 0.5, 15.0, 3.5, 0.5,
                help="Cost Per Mille - revenue per 1,000 monetised views.",
            )
        with cfg2:
            monetised_pct = st.slider(
                "% of Views Monetised", 10, 100, 45, 5,
                help="Estimated share of total views that generate ad revenue.",
            )
        with cfg3:
            available_cats = sorted(df_filtered["category"].dropna().unique())
            selected_cat_est = st.selectbox("Category to Model", available_cats) if available_cats else None

        if selected_cat_est:
            cat_est = df_filtered[df_filtered["category"] == selected_cat_est].copy()

        #using a 30 day view column if available, else approximate
        views_30_col = "video_views_for_the_last_30_days"
        if views_30_col in cat_est.columns:
            cat_est = cat_est.dropna(subset=[views_30_col])
            cat_est["estimated_monthly_earnings"] = (
                cat_est[views_30_col] * (monetised_pct / 100) / 1000 * custom_cpm
            )
            view_note = ""
        else:
            if "channel_age_years" in cat_est.columns:
                cat_est["est_monthly_views"] = cat_est["video_views"] / (
                    (cat_est["channel_age_years"] * 12).replace(0, np.nan)
                )
            else:
                cat_est["est_monthly_views"] = cat_est["video_views"] / 60

            cat_est["estimated_monthly_earnings"] = (
                cat_est["est_monthly_views"] * (monetised_pct / 100) / 1000 * custom_cpm
            )
            view_note = " *(estimated from lifetime views / channel age)*"


        if len(cat_est) == 0:
            st.info(f"No data available for **{selected_cat_est}** with current filters.")
        else:
            top_est = cat_est.nlargest(top_n, "estimated_monthly_earnings")
            fig_est = px.bar(
                top_est,
                x="estimated_monthly_earnings",
                y="youtuber" if "youtuber" in top_est.columns else top_est.index.astype(str),
                orientation = "h",
                color="estimated_monthly_earnings",
                color_continuous_scale="Reds",
                labels={"estimated_monthly_earnings": "Est. Monthly Earnings (USD)", "youtuber": ""},
                template="plotly_dark",
                title=(
                    f"Top {top_n} Estimated Earners - {selected_cat_est}  "
                    f"| CPM ${custom_cpm}  |   {monetised_pct}% monetised{view_note}"
                ),
            )
            fig_est.update_layout(
                height=430, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"},
                margin=dict(l=5, r=5, t=60, b=5),
            )
            fig_est.update_xaxes(tickformat="$,.0f")
            st.plotly_chart(fig_est, use_container_width=True)


    # Advanced feature: Interactive data table
    st.markdown("---")
    st.markdown('<span class="feature-badge">Advanced Feature: Interactive Data Table</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="feature-desc">'
        'Click any column header to sort. Search by channel name.'
        'Select which columns to display using the multiselect.'
        'All rows reflect the current side filter state.'
        '</p>',
        unsafe_allow_html=True,
    )
    display_options = [c for c in [
        "youtuber", "subscribers", "video_views", "uploads", "category",
        "channel_type", "country", "avg_monthly_earnings", "avg_yearly_earnings",
        "views_per_subscriber", "created_year", "channel_age_years",
    ] if c in df_filtered.columns]

    tc1, tc2 = st.columns([3, 1])
    with tc1:
        selected_cols = st.multiselect(
            "Columns to display:", options=display_options, default=display_options[:7],
        )
    with tc2:
        search_term = st.text_input("🔍Search channel name:", "")
    table_df = df_filtered[selected_cols].copy() if selected_cols else df_filtered.copy()
    if search_term and "youtuber" in table_df.columns:
        table_df = table_df[
            table_df["youtuber"].str.contains(search_term, case=False, na=False)
        ]
            
    views_col_name = "video_views" if "video_views" in table_df.columns else "video_views"
    for col in ["subscribers", "video_views", "uploads"]:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")
    for col in["avg_monthly_earnings", "avg_yearly_earnings"]:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "")
    if "views_per_subscriber" in table_df.columns:
        table_df["views_per_subscriber"] = table_df["views_per_subscriber"].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "")
    st.dataframe(table_df.reset_index(drop=True), use_container_width=True, height=400)
    st.caption(f"Showing **{len(table_df):,}** channels · Click any column header to sort ↑↓")
                  
#─────────────────────────────────────────────           
# FOOTER           
#─────────────────────────────────────────────              
st.markdown("---")
st.caption(
    "**Data source:** Nelgiriyewithana, N. (2023). *Global Youtube Statistics 2023* [Data set]. Kaggle"
    "https://www.kaggle.com/datasets/nelgiriyewithana/global-youtube-statistics-2023 "
    
    " | **Built By:** Niharika Verma (25221704)"
    " | **Built with:** Streamlit · Plotly · Pandas "
    " | **Course:** IS41570 · UCD iSchool · Spring 2026"
)



            




            


            
                       


                       
                       



        
    

        
        
        
    
