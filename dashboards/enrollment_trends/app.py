"""Streamlit dashboard for enrollment changes over time."""

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Enrollment Trends Dashboard", layout="wide")
st.title("📈 Enrollment Trends Over Time")

# Placeholder for loading real data
years = np.arange(2015, 2024)
regions = ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Barisal"]
data = pd.DataFrame(
    {
        "Year": np.tile(years, len(regions)),
        "Region": np.repeat(regions, len(years)),
        "Enrollment": np.random.randint(20000, 50000, len(years) * len(regions)),
    }
)

# Enrollment Trend (All Regions)
st.subheader("Total Enrollment Over Years")
total_enrollment = data.groupby("Year")["Enrollment"].sum()
st.line_chart(total_enrollment)

# Regional Breakdown
st.subheader("Regional Enrollment Breakdown")
for region in regions:
    st.write(f"### {region}")
    region_data = data[data["Region"] == region]
    st.line_chart(region_data.set_index("Year")["Enrollment"])

# TODO: Integrate with real processed data and add filters for school type, gender, etc.
