import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Wordcloud removed
WORDCLOUD_OK = False

st.set_page_config(page_title="Startup Funding — Project 1 (Advanced)", layout="wide")

# ------------------------------
# Helper functions
# ------------------------------
def standardize_columns(df):
    rename_map = {
        "Startup Name": "startup",
        "Founded Year": "year",
        "Headquarters": "city",
        "Location (Locality)": "locality",
        "Sector/Industry": "sector",
        "Total Funding (INR)": "amount",
        "Round Type": "round_type",
        "Investor/s (Proxy)": "investors"
    }
    df = df.rename(columns={c: c.strip() for c in df.columns})
    rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    return df


def clean_amount_series(s):
    return (
        s.astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("INR", "", regex=False)
        .str.strip()
    )


def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def extract_investor_list(df):
    inv_series = (
        df.get("investors", pd.Series([], dtype=str))
        .fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
    )
    inv_series = inv_series[inv_series != ""]
    return sorted(inv_series.unique())


def safe_contains(series, pat):
    return series.fillna("").astype(str).str.contains(str(pat), case=False, na=False, regex=False)


# ------------------------------
# Load & prepare data
# ------------------------------
@st.cache_data(show_spinner=False)
def load_data(path="project.csv"):
    raw = pd.read_csv(path)
    df = standardize_columns(raw)

    if "amount" in df.columns:
        df["amount"] = clean_amount_series(df["amount"])
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    else:
        df["amount"] = 0

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    else:
        df["year"] = pd.NA

    df["startup"] = df.get("startup", pd.Series([""] * len(df))).astype(str)
    df["city"] = df.get("city", pd.Series([""] * len(df))).astype(str)
    df["sector"] = df.get("sector", pd.Series([""] * len(df))).astype(str)
    df["investors"] = df.get("investors", pd.Series([""] * len(df))).astype(str)

    return df


try:
    df = load_data("project.csv")
except Exception as e:
    st.error(f"Could not load project.csv: {e}")
    st.stop()

st.session_state.setdefault("raw_df", df.copy())
st.session_state.setdefault("working_df", df.copy())
working_df = st.session_state["working_df"]

# ------------------------------
# Aggregations for business recommendation
# ------------------------------
@st.cache_data
def sector_summary(df):
    s = (
        df.groupby("sector")["amount"]
        .agg(["sum", "mean", "min", "max", "count"])
        .rename(columns={"sum": "total_funding", "mean": "avg_funding", "count": "deals"})
        .reset_index()
    )

    uniq = df.groupby("sector")["startup"].nunique().reset_index()
    uniq = uniq.rename(columns={"startup": "unique_startups"})
    s = s.merge(uniq, on="sector", how="left")

    if "year" in df.columns and df["year"].notna().any():
        years = sorted([int(y) for y in df["year"].dropna().unique()])
        if len(years) >= 2:
            last_year = years[-1]
            recent = (
                df[df["year"] >= last_year - 1]
                .groupby("sector")["amount"]
                .sum()
                .reset_index()
                .rename(columns={"amount": "recent_funding"})
            )
            s = s.merge(recent, on="sector", how="left")
            s["recent_funding"] = s["recent_funding"].fillna(0)
        else:
            s["recent_funding"] = 0
    else:
        s["recent_funding"] = 0

    return s.fillna(0)


@st.cache_data
def sector_city_breakdown(df):
    records = {}
    for sector, grp in df.groupby("sector"):
        by_city = grp.groupby("city")["amount"].sum().reset_index().sort_values("amount", ascending=False)
        records[sector] = by_city
    return records


sector_stats = sector_summary(working_df)
sector_city = sector_city_breakdown(working_df)

# ------------------------------
# Recommendation logic
# ------------------------------
def recommend_businesses(budget, preferred_sector=None, preferred_city=None, top_n=5):
    results = []

    W_fit = 0.45
    W_demand = 0.25
    W_growth = 0.15
    W_competition = 0.15

    for _, row in sector_stats.iterrows():
        sector = row["sector"]
        avg_f = float(row["avg_funding"])
        min_f = float(row["min"])
        max_f = float(row["max"])
        total = float(row["total_funding"])
        unique = float(row["unique_startups"])
        deals = float(row["deals"])
        recent = float(row["recent_funding"])

        if budget <= 0:
            fit_score = 0
        else:
            if avg_f == 0:
                fit_score = 0.2
            else:
                ratio = min(budget / avg_f, 10)
                fit_score = np.tanh(np.log1p(ratio))
                fit_score = float(np.clip(fit_score, 0, 1))

        demand_score = np.tanh(np.log1p(unique + deals))
        growth_score = float(np.clip((recent / total) if total > 0 else 0, 0, 1))
        competition_score = float(np.clip(1 - np.tanh(np.log1p(unique)), 0, 1))

        score = (
            W_fit * fit_score
            + W_demand * demand_score
            + W_growth * growth_score
            + W_competition * competition_score
        )

        city_df = sector_city.get(sector, pd.DataFrame(columns=["city", "amount"]))
        top_cities = city_df.head(5).to_dict(orient="records")

        if preferred_sector and preferred_sector.lower() == sector.lower():
            score *= 1.08

        suggested_min = int(min_f) if min_f > 0 else int(avg_f * 0.5)
        suggested_max = int(max_f) if max_f > 0 else int(avg_f * 1.5)

        results.append({
            "sector": sector,
            "score": float(score),
            "fit_score": float(fit_score),
            "demand_score": float(demand_score),
            "growth_score": float(growth_score),
            "competition_score": float(competition_score),
            "suggested_min": suggested_min,
            "suggested_max": suggested_max,
            "unique_startups": int(unique),
            "deals": int(deals),
            "top_cities": top_cities
        })

    results = [r for r in results if r["sector"].strip() != ""]
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results[:top_n], results


# ------------------------------
# Sidebar Navigation
# ------------------------------
st.sidebar.markdown("<h1 style='color:#00E5FF;'>🚀 Project 1 — Advanced</h1>", unsafe_allow_html=True)
page = st.sidebar.selectbox("Navigate", [
    "Overview",
    "Startups",
    "Startup Profile",
    "Investors",
    "Investor Analysis",
    "Sectors",
    "Cities",
    "Investor Comparison",
    "Trends",
    "Data & Tools",
    "Business Recommendation"
])

# ------------------------------
# PAGES
# ------------------------------

# ------------------------------
# UPDATED OVERVIEW (with features 1 + 2 + 5)
# ------------------------------
if page == "Overview":
    st.markdown("<h1 style='color:#2b7cff;'>📊 Overview</h1>", unsafe_allow_html=True)

    total_funding = working_df["amount"].sum()
    total_startups = working_df["startup"].nunique()
    total_deals = len(working_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Funding", f"₹{int(total_funding):,}")
    col2.metric("Total Startups", total_startups)
    col3.metric("Total Deals", total_deals)

    # 1️⃣ Total unique investors
    unique_investors = len(extract_investor_list(working_df))
    st.metric("Unique Investors", unique_investors)

    # 2️⃣ Sector count + most funded sector
    sector_count = working_df["sector"].nunique()
    top_sector = working_df.groupby("sector")["amount"].sum().idxmax()

    a, b = st.columns(2)
    a.metric("Total Sectors", sector_count)
    b.metric("Most Funded Sector", top_sector)

    # 5️⃣ Funding Growth YoY %
    st.subheader("📈 Funding Growth Over Time (Year-on-Year %)")

    yearly = (
        working_df.groupby("year")["amount"]
        .sum()
        .reset_index()
        .sort_values("year")
    )
    yearly["growth_%"] = yearly["amount"].pct_change() * 100

    st.dataframe(yearly, use_container_width=True)

    st.plotly_chart(px.line(yearly, x="year", y="amount", markers=True), use_container_width=True)

    # Existing Top Sector chart
    sec = (
        working_df.groupby("sector")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .head(10)
    )
    st.subheader("Top 10 Funded Sectors")
    st.plotly_chart(px.bar(sec, x="sector", y="amount", text="amount"), use_container_width=True)

# ---------------------------------------------------------------------
# Remaining pages unchanged
# ---------------------------------------------------------------------

elif page == "Startups":
    st.markdown("<h1 style='color:#ab47bc;'>🚀 Startups</h1>", unsafe_allow_html=True)
    selected = st.selectbox("Select Startup", sorted(working_df["startup"].unique()))

    data = working_df[working_df["startup"] == selected]
    st.dataframe(data, use_container_width=True)

    if "round_type" in data.columns:
        st.plotly_chart(px.bar(data, x="round_type", y="amount"), use_container_width=True)

elif page == "Startup Profile":
    st.markdown("<h1 style='color:#ab47bc;'>📄 Startup Profile</h1>", unsafe_allow_html=True)

    startups = sorted(working_df["startup"].dropna().unique())
    sel = st.selectbox("Select Startup", ["-- choose --"] + startups)

    if sel != "-- choose --":
        df_sel = working_df[working_df["startup"] == sel]
        st.dataframe(df_sel, use_container_width=True)

        yearly = df_sel.groupby("year")["amount"].sum().reset_index()
        st.plotly_chart(px.bar(yearly, x="year", y="amount"), use_container_width=True)

elif page == "Investors":
    st.markdown("<h1 style='color:#66bb6a;'>💼 Investors</h1>", unsafe_allow_html=True)

    investors = extract_investor_list(working_df)
    investor = st.selectbox("Select Investor", ["-- choose --"] + investors)

    if investor != "-- choose --":
        data = working_df[safe_contains(working_df["investors"], investor)]
        st.dataframe(data, use_container_width=True)

        sec = data.groupby("sector")["amount"].sum().reset_index()
        st.plotly_chart(px.pie(sec, names="sector", values="amount"), use_container_width=True)

elif page == "Investor Analysis":
    st.markdown("<h1 style='color:#66bb6a;'>📈 Investor Analysis</h1>", unsafe_allow_html=True)

    inv_list = extract_investor_list(working_df)
    sel_inv = st.selectbox("Select Investor", ["-- choose --"] + inv_list)

    if sel_inv != "-- choose --":
        df_inv = working_df[safe_contains(working_df["investors"], sel_inv)]
        st.dataframe(df_inv, use_container_width=True)

        bar = df_inv.groupby("sector")["amount"].sum().reset_index()
        st.plotly_chart(px.bar(bar, x="sector", y="amount"), use_container_width=True)

elif page == "Sectors":
    st.markdown("<h1 style='color:#ff9800;'>🏭 Sector Analysis</h1>", unsafe_allow_html=True)

    clean_sectors = sorted([s for s in working_df["sector"].unique() if s.strip() != ""])
    sector = st.selectbox("Select Sector", ["-- choose --"] + clean_sectors)

    if sector != "-- choose --":
        data = working_df[working_df["sector"] == sector]

        summary = (
            data.groupby("startup")
            .agg(
                total_funding=("amount", "sum"),
                years=("year", lambda x: ", ".join(sorted({str(int(y)) for y in x if pd.notna(y)})))
            )
            .reset_index()
            .sort_values("total_funding", ascending=False)
        )

        st.dataframe(summary, use_container_width=True)
        st.plotly_chart(px.bar(summary, x="startup", y="total_funding"), use_container_width=True)

elif page == "Cities":
    st.markdown("<h1 style='color:#29b6f6;'>📍 City Analysis</h1>", unsafe_allow_html=True)

    cities = sorted(working_df["city"].dropna().unique())
    city = st.selectbox("Select City", ["-- choose --"] + cities)

    if city != "-- choose --":
        df_city = working_df[working_df["city"] == city]

        total_funding = df_city["amount"].sum()
        total_startups = df_city["startup"].nunique()
        total_deals = len(df_city)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Funding", f"₹{int(total_funding):,}")
        c2.metric("Total Startups", total_startups)
        c3.metric("Total Deals", total_deals)

        top = df_city.groupby("startup")["amount"].sum().reset_index().sort_values("amount", ascending=False)
        st.dataframe(top, use_container_width=True)

        trend = df_city.groupby("year")["amount"].sum().reset_index()
        st.plotly_chart(px.line(trend, x="year", y="amount"), use_container_width=True)

elif page == "Investor Comparison":
    st.markdown("<h1 style='color:#7c4dff;'>⚔️ Compare Investors</h1>", unsafe_allow_html=True)

    inv_list = extract_investor_list(working_df)

    inv1 = st.selectbox("Investor 1", ["-- choose --"] + inv_list)
    inv2 = st.selectbox("Investor 2", ["-- choose --"] + inv_list)

    if inv1 != "-- choose --" and inv2 != "-- choose --":
        df1 = working_df[safe_contains(working_df["investors"], inv1)]
        df2 = working_df[safe_contains(working_df["investors"], inv2)]

        c1, c2 = st.columns(2)
        c1.metric(inv1, f"₹{df1['amount'].sum():,.0f}")
        c2.metric(inv2, f"₹{df2['amount'].sum():,.0f}")

        sec1 = df1.groupby("sector")["amount"].sum().reset_index()
        sec2 = df2.groupby("sector")["amount"].sum().reset_index()

        colA, colB = st.columns(2)
        colA.plotly_chart(px.pie(sec1, names="sector", values="amount"), use_container_width=True)
        colB.plotly_chart(px.pie(sec2, names="sector", values="amount"), use_container_width=True)

elif page == "Trends":
    st.markdown("<h1 style='color:#1976d2;'>📈 Funding Trends</h1>", unsafe_allow_html=True)

    yearly = (
        working_df.groupby("year")
        .agg(
            total_funding=("amount", "sum"),
            deal_count=("startup", "count"),
            avg_funding=("amount", "mean"),
        )
        .reset_index()
        .sort_values("year")
    )

    st.dataframe(yearly, use_container_width=True)
    st.plotly_chart(px.line(yearly, x="year", y="total_funding"), use_container_width=True)
    st.plotly_chart(px.bar(yearly, x="year", y="deal_count"), use_container_width=True)


# ------------------------------
# BUSINESS RECOMMENDATION (Fixed)
# ------------------------------
elif page == "Business Recommendation":
    st.markdown("<h1 style='color:#4caf50;'>💡 Business Recommendation</h1>", unsafe_allow_html=True)

    default_budget = int(np.median(working_df["amount"]))
    budget = st.number_input("Available Budget (₹)", min_value=0, value=default_budget, step=10000)

    clean_sectors = sorted([
        s for s in sector_stats["sector"].astype(str).unique()
        if s.strip() != "" and not s.replace(".", "", 1).isdigit()
    ])

    preferred_sector = st.selectbox("Preferred Sector (optional)", ["-- any --"] + clean_sectors)
    if preferred_sector == "-- any --":
        preferred_sector = None

    cities = sorted(working_df["city"].dropna().unique())
    preferred_city = st.selectbox("Preferred City (optional)", ["-- any --"] + cities)
    if preferred_city == "-- any --":
        preferred_city = None

    top_k = st.slider("Number of recommendations", 1, 10, 5)

    if st.button("Recommend Business Ideas"):
        recs, all_recs = recommend_businesses(
            budget=budget,
            preferred_sector=preferred_sector,
            preferred_city=preferred_city,
            top_n=top_k
        )

        st.subheader("Top Recommendations")

        out_rows = []

        for i, r in enumerate(recs, start=1):
            st.markdown(f"### {i}. Sector: **{r['sector']}** — Score: **{r['score']:.3f}**")
            st.write(f"- Funding fit: {r['fit_score']:.3f}")
            st.write(f"- Demand score: {r['demand_score']:.3f}")
            st.write(f"- Growth score: {r['growth_score']:.3f}")
            st.write(f"- Competition score: {r['competition_score']:.3f}")
            st.write(f"- Suggested funding: ₹{r['suggested_min']:,} — ₹{r['suggested_max']:,}")

            if r["top_cities"]:
                st.write("Top Cities:")
                df_city = pd.DataFrame(r["top_cities"])
                df_city["amount"] = df_city["amount"].apply(lambda x: f"₹{int(x):,}")
                st.table(df_city)

            st.write("---")

            out_rows.append({
                "rank": i,
                "sector": r["sector"],
                "score": r["score"],
                "suggested_min": r["suggested_min"],
                "suggested_max": r["suggested_max"],
            })

        export_df = pd.DataFrame(out_rows)
        st.download_button("Download Recommendations", df_to_csv_bytes(export_df),
                           "business_recommendations.csv")

# ------------------------------
# DATA & TOOLS
# ------------------------------
elif page == "Data & Tools":
    st.markdown("<h1 style='color:#009688;'>🛠 Data Tools</h1>", unsafe_allow_html=True)

    tool = st.selectbox("Select Tool", ["Preview Data", "Column Analyzer", "Data Filter", "Export Cleaned CSV"])

    if tool == "Preview Data":
        st.dataframe(working_df, use_container_width=True)

    elif tool == "Column Analyzer":
        col = st.selectbox("Choose Column", working_df.columns)
        st.write("### Column Info")
        st.write("Data Type:", working_df[col].dtype)
        st.write("Unique Values:", working_df[col].nunique())

        vc = working_df[col].value_counts().reset_index()
        vc.columns = ["Value", "Count"]
        st.dataframe(vc)

    elif tool == "Data Filter":
        start_list = ["All"] + sorted(working_df["startup"].dropna().unique())
        city_list = ["All"] + sorted(working_df["city"].dropna().unique())
        sec_list = ["All"] + sorted(working_df["sector"].dropna().unique())

        c1, c2, c3 = st.columns(3)

        s_start = c1.selectbox("Startup", start_list)
        s_city = c2.selectbox("City", city_list)
        s_sec = c3.selectbox("Sector", sec_list)

        min_amt = int(working_df["amount"].min())
        max_amt = int(working_df["amount"].max())

        amt_range = st.slider("Funding Range", min_amt, max_amt, (min_amt, max_amt))

        filtered = working_df.copy()
        if s_start != "All":
            filtered = filtered[filtered["startup"] == s_start]
        if s_city != "All":
            filtered = filtered[filtered["city"] == s_city]
        if s_sec != "All":
            filtered = filtered[filtered["sector"] == s_sec]

        filtered = filtered[(filtered["amount"] >= amt_range[0]) & (filtered["amount"] <= amt_range[1])]

        st.dataframe(filtered, use_container_width=True)
        st.download_button("Download Filtered CSV", df_to_csv_bytes(filtered), "filtered_data.csv")

    elif tool == "Export Cleaned CSV":
        st.download_button("Download Cleaned CSV", df_to_csv_bytes(working_df), "cleaned_project.csv")
