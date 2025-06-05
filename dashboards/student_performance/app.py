"""Streamlit dashboard for student performance metrics."""

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Student Performance Dashboard", layout="wide")
st.title("📊 Student Performance Overview")

# Placeholder for loading real data
data = pd.DataFrame(
    {
        "Student": [f"Student {i}" for i in range(1, 101)],
        "GPA": np.random.normal(3.0, 0.5, 100).clip(0, 4),
        "Math": np.random.normal(75, 10, 100).clip(0, 100),
        "English": np.random.normal(70, 12, 100).clip(0, 100),
        "Science": np.random.normal(72, 11, 100).clip(0, 100),
    }
)

# GPA Distribution
st.subheader("GPA Distribution")
st.hist(data["GPA"], bins=20)

# Subject-wise Performance
st.subheader("Subject-wise Performance")
st.bar_chart(data[["Math", "English", "Science"]].mean())

# Top Performers
st.subheader("Top 10 Performers")
st.dataframe(data.sort_values("GPA", ascending=False).head(10))

# TODO: Integrate with real processed data and add more interactive filters.
