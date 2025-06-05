"""Streamlit dashboard for demographic-based student data patterns."""

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Demographic Insights Dashboard", layout="wide")
st.title("👥 Demographic Insights")

# Placeholder for loading real data
data = pd.DataFrame(
    {
        "Gender": np.random.choice(["Male", "Female"], 500),
        "SES": np.random.choice(["Low", "Medium", "High"], 500, p=[0.4, 0.4, 0.2]),
        "UrbanRural": np.random.choice(["Urban", "Rural"], 500, p=[0.6, 0.4]),
        "GPA": np.random.normal(3.0, 0.5, 500).clip(0, 4),
    }
)

# Gender Distribution
st.subheader("Gender Distribution")
st.bar_chart(data["Gender"].value_counts())

# SES Impact on GPA
st.subheader("Socioeconomic Status (SES) Impact on GPA")
st.bar_chart(data.groupby("SES")["GPA"].mean())

# Urban vs Rural Comparison
st.subheader("Urban vs Rural GPA Comparison")
st.bar_chart(data.groupby("UrbanRural")["GPA"].mean())

# TODO: Integrate with real processed data and add more demographic filters.
