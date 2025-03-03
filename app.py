import pandas as pd
import streamlit as st
import altair as alt
import csv
import datetime
import os
import json

if st.experimental_get_query_params():
    raw = st.experimental_get_query_params()
    if 'link' in raw:
        log_click(raw['link'][0])


# Log link clicks to a CSV file
def log_click(link):
    with open("click_log.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, link])



# ------------------------------------ SETUP ------------------------------------

# Set up page and branding
st.set_page_config(layout="wide", page_title="SRN CSRD Archive", page_icon="srn-icon.png")
st.markdown("""<style> footer {visibility: hidden;} </style> """, unsafe_allow_html=True)

standard_info_mapper = pd.DataFrame({
    'standard': ['e1', 'e2', 'e3', 'e4', 'e5', 's1', 's2', 's3', 's4', 'g1'],
    'standard2': ['E1 Climate', 'E2 Pollution', 'E3 Water', 'E4 Biodiv', 'E5 Circular', 'S1 Workforce', 'S2 Value chain', 'S3 Communities', 'S4 Consumers', 'G1 Conduct'],
    'standardgroup': ['E', 'E', 'E', 'E', 'E', 'S', 'S', 'S', 'S', 'G'],
    'ig3_dp': [217, 72, 51, 125, 67, 198, 71, 69, 69, 55]
})


# ------------------------------------ PREPARE DF -------------------------------
# Prepare the CSRD DataFrame
df = (
    pd.read_csv("https://docs.google.com/spreadsheets/d/1Nlyf8Yz_9Fst8rEmQc2IMc-DWLF1fpmBTB7n4FlZwxs/export?format=csv&gid=0", skiprows=2)
    .query("verified == 'yes'")
    .rename(columns={
        'SASB industry \n(SICS® Industries)': "industry",
        })
    .merge(
        # Merge Industry-Sector Lookup from separate sheet
        pd.read_csv(
            "https://docs.google.com/spreadsheets/d/1Nlyf8Yz_9Fst8rEmQc2IMc-DWLF1fpmBTB7n4FlZwxs/export?format=csv&gid=218767986#gid=218767986"
            ).rename(columns={
                "SICS® Industries": "industry",
                "SICS® Sector": "sector"
                }
            ), on="industry", how="left"
        )
.assign(
    link = lambda x: [
        f'<a href="{y}#name={z}" target="_blank" '
        f'onclick="window.parent.logClick(\'{y}#name={z}\')">{z}</a>'
        for y, z in zip(x["link"], x["company"])
    ],
    company = lambda x: x["company"].str.strip()
)
    .loc[:, ['company', 'link', 'country', 'sector', 'industry', "publication date", "pages PDF", "auditor"]]
    .dropna()
    # Merge the standard-counts dataframe
    .merge(
        (
            pd.read_csv("https://docs.google.com/spreadsheets/d/1Vj8yau93kmSs_WqnV5w1V_tdU-JlMo-BV6htDvAv1TI/export?format=csv&gid=1792638779#gid=1792638779")
            .assign(
                company = lambda x: x["company"].str.strip()
                )
            .query("year == 2024")
            .drop("pages", axis=1)
            .drop_duplicates(subset=['company'])
        ),
        on=["company"], how="outer", indicator=True
    )
    .query("_merge != 'right_only'")
    .sort_values("publication date", ascending=True)
)


# ------------------------------------ EXPLANATIONS -----------------------------
col1c, col2c = st.columns((0.6, 0.4))
with col1c:
    st.markdown(f"""
                We are crowd-sourcing the collection of CSRD-compliant reports to support prepares and users of sustainability reporting.

                Below, you find a continuously updated list of {len(df)} CSRD-compliant reports.
                
                Want to make an addition? Feel free to do so [using this Google Sheet](https://docs.google.com/spreadsheets/d/1Nlyf8Yz_9Fst8rEmQc2IMc-DWLF1fpmBTB7n4FlZwxs/edit?gid=1695573594#gid=1695573594) and [follow us on LinkedIn](https://www.linkedin.com/company/sustainability-reporting-navigator/).
                """)

with col2c:
    # Custom CSS for Bubble Counter
    st.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        ">
            <p style="
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100px;
                height: 100px;
                background-color: #4200ff;
                color: white;
                font-size: 36px;
                font-weight: bold;
                border-radius: 50%;
                text-align: center;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
                margin: 0;
            ">
                {len(df)}
            </p>
            <p style="margin-top: 10px;">CSRD reports so far</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()


# ------------------------------------ FILTERS ----------------------------------
# Create filters in two columns
col1, col2 = st.columns(2)

with col1:
    country_options = ["All"] + sorted(df["country"].unique())
    selected_countries = st.multiselect("Select countries", options=country_options, default=["All"], key="tab1_country")

with col2:
    industry_options = ["All"] + sorted(df["sector"].unique())
    selected_industries = st.multiselect("Select sector", options=industry_options, default=["All"], key="tab1_industry")

# Apply filtering logic
if "All" in selected_countries:
    filtered_countries = df["country"].unique()
else:
    filtered_countries = selected_countries

if "All" in selected_industries:
    filtered_industries = df["sector"].unique()
else:
    filtered_industries = selected_industries

filtered_df = df[
    df["country"].isin(filtered_countries) &
    df["sector"].isin(filtered_industries)
]

# Next, we prepare a list of companies from this filtered DataFrame:
company_list = sorted(filtered_df["company"].unique())

# We add a 'None' item to represent "no company selected yet".
selected_company = st.selectbox(
    label="Search for a company",
    options=[None] + company_list,            # None is the first option
    format_func=lambda x: "Search for a company..." if x is None else x,  # Display text
    index=0,                                   # Default to None selected
    key="tab1_selectbox"
)

# If the user selects a company, we filter; otherwise we keep all rows.
if selected_company is not None:
    filtered_df = filtered_df[filtered_df["company"] == selected_company]


# ------------------------------------ LIST AND HEATMAP -----------------------
# ------------------------------------ LIST

try:
    tab1, tab2 = st.tabs(["List of reports", "Heatmap of topics reported"])

    with tab1:
        # Display the filtered table with custom formatting and column configurations
        st.dataframe(
            filtered_df.loc[:, ['link', 'country', 'sector', 'industry', 'publication date', 'pages PDF', 'auditor']],
            column_config={
                # "company": st.column_config.Column(width="medium", label="Company"),
                "link": st.column_config.LinkColumn(
                    label="Company",
                    width="medium", 
                    display_text="^https://.*#name=(.*)$"
                    ),
                "country": st.column_config.Column(label="Country"),
                "sector": st.column_config.Column(width="medium", label="Sector"),
                "industry": st.column_config.Column(width="medium", label="Industry"),
                "publication date": st.column_config.DateColumn(format="DD.MM.YYYY", width="small", label="Published"),
                "pages PDF": st.column_config.TextColumn(help="The number of pages of the sustainability statement.", label="Pages"),
                "auditor": st.column_config.TextColumn(label="Auditor"),
            },
            hide_index=True,
            use_container_width=True,
            height=35 * len(filtered_df) + 38
        )

# ------------------------------------ HEATMAP
    with tab2:
        # Create filters in two columns
        col1d, col2d = st.columns([0.5, 0.5])

        with col1d:
            st.markdown("""
                        ##### Explanation \n\n
                        This chart shows simple counts of how often a standard is referenced in the company's sustainability statement. To compute the count, we scan the pages of the sustainability statement and count the occurrences of the standard identifier (e.g., E1, E2, ..., G1).
                        """)

            st.markdown("###### Scaling\n\n")
            st.checkbox(label="Scale the counts by the length of the sustainability statement (to control for longer reports)", key="scale_by_pages")
            st.checkbox(label="Scale the counts by the number of datapoints per standard from IG-3 (to control for longer standards)", key="scale_by_dp")
            scale_by_pages = st.session_state.get("scale_by_pages", False)
            scale_by_dp = st.session_state.get("scale_by_dp", False)

            st.markdown("###### Split view")
            split_view = st.radio(label="", options=("by sector", "by country", "by auditor", "no split"), index=0, horizontal=True, label_visibility="collapsed")


        with col2d:
            filtered_melted_df = (
                filtered_df
                .loc[:, ['company', "sector", "country", "auditor", "pages PDF", 'e1', 'e2', "e3", "e4", "e5", "s1", "s2", "s3", "s4", "g1"]]
                .melt(id_vars=["company", "sector", "country", "auditor", "pages PDF"], value_name="hits", var_name="standard")
                .merge(standard_info_mapper)
                .assign(
                    standard=lambda x: x['standard'].str.upper(),
                    hits=lambda x: x["hits"] / x["pages PDF"] if scale_by_pages else x["hits"], 
                    )
                .assign(
                    hits=lambda x: x["hits"] / x["ig3_dp"] if scale_by_dp else x["hits"],  
                )
                .sort_values("sector")
                .dropna()
            )

            # print(filtered_melted_df)

            if filtered_melted_df.empty:
                st.error(f"We have not analyzed this company yet but will do so very soon!", icon="🚨")

            else:

                filtered_melted_df["norm_hits"] = (
                    filtered_melted_df.groupby("company")["hits"]
                    .transform(lambda x: x / x.max() if x.max() != 0 else 0)
                )
                color_field = "norm_hits:Q"
                color_scale = alt.Scale(
                    domain=[0, 0.5, 1],
                    range=['#ffffff', '#a0a0ff', '#4200ff']
                )

                if split_view != "no split":

                    heatmap_faceted = (
                        alt.Chart(filtered_melted_df)
                        .mark_rect(stroke="lightgray", filled=True)
                        .encode(
                            x=alt.X(
                                "standard",
                                title=None,
                                axis=alt.Axis(orient="top", labelAngle=0),
                                sort=[
                                    'E1', 'E2', 'E3', 'E4', 'E5',
                                    'S1', 'S2', 'S3', 'S4',
                                    'G1'
                                ]
                            ),
                            y=alt.Y("company", title=None), 
                            color=alt.Color(
                                color_field,
                                scale=color_scale,
                                legend=None
                            ),
                            tooltip=[
                                alt.Tooltip("company", title="Company"),
                                alt.Tooltip("standard2", title="ESRS topic"),
                                alt.Tooltip("hits", title="Referenced", format=".2f" if scale_by_pages or scale_by_dp else "d")
                            ]
                        )
                        .properties(width = 400)
                        .facet(
                            row=alt.Row(
                                "sector:N" if split_view == "by sector" else "country:N" if split_view == "by country" else "auditor:N", 
                                header=alt.Header(
                                    orient='top',
                                    labelAngle=0,
                                    title=""
                                )
                            )
                        )
                        # Make sure each facet has its own y-axis domain
                        .resolve_scale(
                            x="independent",
                            y='independent',
                            color="shared"
                        )
                    )
                    
                    st.altair_chart(heatmap_faceted)

                else:

                    heatmap = (
                        alt.Chart(filtered_melted_df)
                        .mark_rect(stroke="lightgray", filled=True)
                        .encode(
                            x=alt.X(
                                "standard",
                                title=None,
                                axis=alt.Axis(orient="top", labelAngle=0),
                                sort=[
                                    'E1', 'E2', 'E3', 'E4', 'E5',
                                    'S1', 'S2', 'S3', 'S4',
                                    'G1'
                                ]
                            ),
                            y=alt.Y("company", title=None), 
                            color=alt.Color(
                                color_field,
                                scale=color_scale,
                                legend=None
                            ),
                            tooltip=[
                                alt.Tooltip("company", title="Company"),
                                alt.Tooltip("standard2", title="ESRS topic"),
                                alt.Tooltip("hits", title="Referenced", format=".2f" if scale_by_pages or scale_by_dp else "d")
                            ]
                        )
                        .properties(width = 400)
                    )
                    
                    st.altair_chart(heatmap)






except Exception as e:
    st.error('This is an error. We are working on a fix. In the meantime, check out our Google Sheet!', icon="🚨")
    print(e)

# st.markdown("""
#             :gray[20250226-12:43am]
#             """)

