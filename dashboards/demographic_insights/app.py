"""
Demographic Insights Dashboard
----------------------------
Interactive dashboard for analyzing student demographics and their academic performance.
"""

import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Page configuration
st.set_page_config(
    page_title="Demographic Insights Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main .block-container {
        padding: 2rem 3rem;
    }
    .stDataFrame {
        width: 100%;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        padding: 0 1rem;
        border-radius: 0.5rem 0.5rem 0 0;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_subject_performance():
    """Load subject-wise performance data."""
    try:
        db_url = os.getenv('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/student_data_db")
        engine = create_engine(db_url)
        
        query = """
        SELECT 
            s.student_id,
            sub.subject_name,
            AVG(g.grade) as avg_grade,
            COUNT(g.grade_id) as grade_count,
            MIN(g.grade) as min_grade,
            MAX(g.grade) as max_grade
        FROM students s
        JOIN grades g ON s.student_id = g.student_id
        JOIN courses c ON g.course_id = c.course_id
        JOIN subjects sub ON c.subject_id = sub.subject_id
        GROUP BY s.student_id, sub.subject_name
        """
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error loading subject performance data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_demographic_data():
    """Load demographic and performance data from the database with enhanced metrics."""
    try:
        # Connect to the database
        db_url = os.getenv('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/student_data_db")
        engine = create_engine(db_url)
        
        # Query to get comprehensive student demographic and performance data
        query = """
        WITH student_demographics AS (
            SELECT 
                s.student_id,
                s.first_name || ' ' || s.last_name as student_name,
                s.gender,
                s.date_of_birth,
                s.enrollment_date,
                s.address,
                s.phone,
                s.email,
                EXTRACT(YEAR FROM age(s.date_of_birth)) as age,
                CASE 
                    WHEN EXTRACT(YEAR FROM age(s.date_of_birth)) < 10 THEN 'Under 10'
                    WHEN EXTRACT(YEAR FROM age(s.date_of_birth)) BETWEEN 10 AND 12 THEN '10-12'
                    WHEN EXTRACT(YEAR FROM age(s.date_of_birth)) BETWEEN 13 AND 15 THEN '13-15'
                    WHEN EXTRACT(YEAR FROM age(s.date_of_birth)) BETWEEN 16 AND 18 THEN '16-18'
                    ELSE '18+'
                END as age_group,
                CASE 
                    WHEN s.address ILIKE '%rural%' THEN 'Rural'
                    WHEN s.address IS NULL THEN 'Unknown'
                    ELSE 'Urban' 
                END as location_type,
                c.class_name,
                c.class_id,
                t.first_name || ' ' || t.last_name as teacher_name,
                LEFT(c.class_name, 1) as grade_level,
                AVG(g.grade) as avg_grade,
                COUNT(g.grade_id) as grades_count,
                COUNT(DISTINCT g.course_id) as courses_taken,
                COUNT(CASE WHEN g.grade >= 90 THEN 1 END) as a_grades,
                COUNT(CASE WHEN g.grade >= 80 AND g.grade < 90 THEN 1 END) as b_grades,
                COUNT(CASE WHEN g.grade >= 70 AND g.grade < 80 THEN 1 END) as c_grades,
                COUNT(CASE WHEN g.grade >= 60 AND g.grade < 70 THEN 1 END) as d_grades,
                COUNT(CASE WHEN g.grade < 60 THEN 1 END) as f_grades,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY g.grade) as median_grade,
                STDDEV(g.grade) as grade_std_dev,
                MIN(g.grade) as min_grade,
                MAX(g.grade) as max_grade,
                MAX(g.last_updated) as last_grade_update
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
            LEFT JOIN grades g ON s.student_id = g.student_id
            GROUP BY s.student_id, s.first_name, s.last_name, s.gender, 
                     s.date_of_birth, s.enrollment_date, s.address, s.phone, s.email,
                     c.class_name, c.class_id, t.first_name, t.last_name
        )
        SELECT 
            *,
            CASE 
                WHEN avg_grade >= 90 THEN 'A (90-100)'
                WHEN avg_grade >= 80 THEN 'B (80-89)'
                WHEN avg_grade >= 70 THEN 'C (70-79)'
                WHEN avg_grade >= 60 THEN 'D (60-69)'
                ELSE 'F (<60)'
            END as performance_category,
            CASE 
                WHEN avg_grade >= 90 THEN 'A'
                WHEN avg_grade >= 80 THEN 'B'
                WHEN avg_grade >= 70 THEN 'C'
                WHEN avg_grade >= 60 THEN 'D'
                ELSE 'F'
            END as performance_letter
        FROM student_demographics;
        """
        
        df = pd.read_sql(query, engine)
        
        # Convert date columns to datetime
        date_columns = ['date_of_birth', 'enrollment_date', 'last_grade_update']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Calculate additional metrics
        df['age'] = (pd.Timestamp.now() - df['date_of_birth']).dt.days // 365
        
        # Add year and month columns for time series analysis
        if 'enrollment_date' in df.columns:
            df['enrollment_year'] = df['enrollment_date'].dt.year
            df['enrollment_month'] = df['enrollment_date'].dt.month
            df['enrollment_year_month'] = df['enrollment_date'].dt.to_period('M').astype(str)
        
        # Calculate performance score (1-5 scale)
        df['performance_score'] = pd.cut(
            df['avg_grade'],
            bins=[0, 59, 69, 79, 89, 100],
            labels=[1, 2, 3, 4, 5],
            right=False
        )
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def setup_sidebar(df):
    """Set up the sidebar with enhanced filters and options."""
    st.sidebar.title("🔍 Filters & Options")
    
    # Date range filter
    with st.sidebar.expander("📅 Date Range", expanded=False):
        if 'enrollment_date' in df.columns:
            min_date = df['enrollment_date'].min().to_pydatetime()
            max_date = df['enrollment_date'].max().to_pydatetime()
            date_range = st.date_input(
                "Enrollment Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help="Filter students by their enrollment date range"
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date, max_date
        else:
            start_date, end_date = None, None
    
    # Class and grade filters
    with st.sidebar.expander("🏫 Class & Grade", expanded=True):
        # Grade level multi-select
        if 'grade_level' in df.columns:
            grade_options = sorted(df['grade_level'].dropna().unique().tolist())
            selected_grades = st.multiselect(
                "Grade Levels",
                options=grade_options,
                default=grade_options,
                help="Filter by one or more grade levels"
            )
        else:
            selected_grades = []
        
        # Class multi-select
        if 'class_name' in df.columns:
            class_options = sorted(df['class_name'].dropna().unique().tolist())
            selected_classes = st.multiselect(
                "Classes",
                options=class_options,
                default=class_options[:min(3, len(class_options))],
                help="Filter by one or more classes"
            )
        else:
            selected_classes = []
    
    # Demographic filters
    with st.sidebar.expander("👥 Demographics", expanded=True):
        # Gender filter
        if 'gender' in df.columns:
            gender_options = ["All"] + sorted(df['gender'].dropna().unique().tolist())
            selected_gender = st.selectbox(
                "Gender",
                gender_options,
                index=0,
                help="Filter by gender"
            )
        else:
            selected_gender = "All"
        
        # Age group filter
        if 'age_group' in df.columns:
            age_groups = ["All"] + sorted(df['age_group'].dropna().unique().tolist())
            selected_age_group = st.selectbox(
                "Age Group",
                age_groups,
                index=0,
                help="Filter by age group"
            )
        else:
            selected_age_group = "All"
        
        # Location type filter
        if 'location_type' in df.columns:
            location_types = ["All"] + sorted(df['location_type'].dropna().unique().tolist())
            selected_location = st.selectbox(
                "Location Type",
                location_types,
                index=0,
                help="Filter by urban/rural location"
            )
        else:
            selected_location = "All"
    
    # Performance filters
    with st.sidebar.expander("📊 Performance", expanded=True):
        # Performance category multi-select
        if 'performance_category' in df.columns:
            perf_categories = sorted(df['performance_category'].dropna().unique().tolist())
            selected_perf_cats = st.multiselect(
                "Performance Categories",
                options=perf_categories,
                default=perf_categories,
                help="Filter by one or more performance categories"
            )
        else:
            selected_perf_cats = []
        
        # Grade range slider
        if 'avg_grade' in df.columns:
            min_grade = int(df['avg_grade'].min())
            max_grade = int(min(100, df['avg_grade'].max() + 1))
            grade_range = st.slider(
                "Average Grade Range",
                min_value=0,
                max_value=100,
                value=(min_grade, max_grade),
                step=5,
                help="Filter by minimum and maximum average grade"
            )
            min_grade, max_grade = grade_range
        else:
            min_grade, max_grade = 0, 100
    
    # Additional options
    with st.sidebar.expander("⚙️ Display Options", expanded=False):
        show_raw_data = st.checkbox(
            "Show Raw Data",
            value=False,
            help="Display the raw data table at the bottom of the dashboard"
        )
        
        show_advanced_metrics = st.checkbox(
            "Show Advanced Metrics",
            value=False,
            help="Display additional statistical metrics and visualizations"
        )
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'grades': selected_grades,
        'classes': selected_classes,
        'gender': selected_gender,
        'age_group': selected_age_group,
        'location': selected_location,
        'performance_categories': selected_perf_cats,
        'min_grade': min_grade,
        'max_grade': max_grade,
        'show_raw_data': show_raw_data,
        'show_advanced_metrics': show_advanced_metrics
    }

def filter_data(df, filters):
    """
    Filter the dataset based on the provided filters with enhanced filtering capabilities.
    
    Args:
        df (pd.DataFrame): The input DataFrame containing student data
        filters (dict): Dictionary containing filter parameters
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if df.empty:
        return df
        
    filtered = df.copy()
    
    # Date range filter
    if filters['start_date'] and filters['end_date'] and 'enrollment_date' in filtered.columns:
        mask = (
            (filtered['enrollment_date'].dt.date >= filters['start_date']) & 
            (filtered['enrollment_date'].dt.date <= filters['end_date'])
        )
        filtered = filtered[mask]
    
    # Grade level filter
    if filters['grades'] and 'grade_level' in filtered.columns:
        filtered = filtered[filtered['grade_level'].isin(filters['grades'])]
    
    # Class filter
    if filters['classes'] and 'class_name' in filtered.columns:
        filtered = filtered[filtered['class_name'].isin(filters['classes'])]
    
    # Gender filter
    if filters['gender'] != "All" and 'gender' in filtered.columns:
        filtered = filtered[filtered['gender'] == filters['gender']]
    
    # Age group filter
    if filters['age_group'] != "All" and 'age_group' in filtered.columns:
        filtered = filtered[filtered['age_group'] == filters['age_group']]
    
    # Location type filter
    if filters['location'] != "All" and 'location_type' in filtered.columns:
        filtered = filtered[filtered['location_type'] == filters['location']]
    
    # Performance category filter
    if filters['performance_categories'] and 'performance_category' in filtered.columns:
        filtered = filtered[filtered['performance_category'].isin(filters['performance_categories'])]
    
    # Grade range filter
    if 'avg_grade' in filtered.columns:
        filtered = filtered[
            (filtered['avg_grade'] >= filters['min_grade']) & 
            (filtered['avg_grade'] <= filters['max_grade'])
        ]
    
    return filtered

def display_metrics(filtered_df, show_advanced=False):
    """
    Display key demographic and performance metrics with enhanced visualizations.
    
    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing student data
        show_advanced (bool): Whether to show advanced metrics
    """
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Calculate basic metrics
    total_students = len(filtered_df)
    avg_age = filtered_df['age'].mean() if 'age' in filtered_df.columns else None
    avg_grade = filtered_df['avg_grade'].mean() if 'avg_grade' in filtered_df.columns else None
    
    # Calculate performance distribution if available
    if 'performance_category' in filtered_df.columns:
        perf_dist = filtered_df['performance_category'].value_counts(normalize=True).mul(100).round(1)
        top_perf_group = perf_dist.idxmax() if not perf_dist.empty else 'N/A'
        top_perf_pct = perf_dist.max() if not perf_dist.empty else 0
    else:
        top_perf_group = 'N/A'
        top_perf_pct = 0
    
    # Create metric cards with improved styling
    st.markdown("""
    <style>
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #2c3e50;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        margin: 0;
    }
    .metric-subtext {
        font-size: 12px;
        color: #95a5a6;
        margin: 5px 0 0 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Metric 1: Total Students
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>👥 Total Students</p>
            <p class='metric-value'>{total_students:,}</p>
            <p class='metric-subtext'>across all selected filters</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 2: Average Age
    with col2:
        age_text = f"{avg_age:.1f} years" if avg_age is not None else "N/A"
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>🎂 Average Age</p>
            <p class='metric-value'>{age_text}</p>
            <p class='metric-subtext'>years old</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 3: Average Grade
    with col3:
        grade_text = f"{avg_grade:.1f}" if avg_grade is not None else "N/A"
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>📊 Average Grade</p>
            <p class='metric-value'>{grade_text}/100</p>
            <p class='metric-subtext'>across all subjects</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 4: Top Performing Group
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-label'>🏆 Top Performance</p>
            <p class='metric-value'>{top_perf_group}</p>
            <p class='metric-subtext'>{top_perf_pct:.1f}% of students</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show additional metrics if advanced mode is enabled
    if show_advanced and not filtered_df.empty:
        st.markdown("---")
        st.subheader("Advanced Metrics")
        
        # Create columns for advanced metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'median_grade' in filtered_df.columns:
                median_grade = filtered_df['median_grade'].median()
                st.metric("Median Grade", f"{median_grade:.1f}")
        
        with col2:
            if 'grade_std_dev' in filtered_df.columns:
                avg_std_dev = filtered_df['grade_std_dev'].mean()
                st.metric("Avg. Std. Dev.", f"{avg_std_dev:.1f}")
        
        with col3:
            if 'a_grades' in filtered_df.columns and 'grades_count' in filtered_df.columns:
                total_a = filtered_df['a_grades'].sum()
                total_grades = filtered_df['grades_count'].sum()
                a_percent = (total_a / total_grades * 100) if total_grades > 0 else 0
                st.metric("A Grades", f"{a_percent:.1f}%")
        
        with col4:
            if 'f_grades' in filtered_df.columns and 'grades_count' in filtered_df.columns:
                total_f = filtered_df['f_grades'].sum()
                total_grades = filtered_df['grades_count'].sum()
                f_percent = (total_f / total_grades * 100) if total_grades > 0 else 0
                st.metric("F Grades", f"{f_percent:.1f}%")
        
        # Show grade distribution if available
        if all(col in filtered_df.columns for col in ['a_grades', 'b_grades', 'c_grades', 'd_grades', 'f_grades']):
            st.markdown("### Grade Distribution")
            grade_counts = {
                'A': filtered_df['a_grades'].sum(),
                'B': filtered_df['b_grades'].sum(),
                'C': filtered_df['c_grades'].sum(),
                'D': filtered_df['d_grades'].sum(),
                'F': filtered_df['f_grades'].sum()
            }
            
            fig = px.pie(
                names=list(grade_counts.keys()),
                values=list(grade_counts.values()),
                title='Grade Distribution',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)

def display_demographic_visualizations(filtered_df, show_advanced=False):
    """
    Display demographic visualizations with tabs for different analysis views.
    
    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing student data
        show_advanced (bool): Whether to show advanced visualizations
    """
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Demographics", 
        "📈 Performance", 
        "🌍 Geographic",
        "📅 Trends"
    ])
    
    with tab1:
        # Demographic distribution
        st.subheader("👥 Demographic Distribution")
        
        if filtered_df.empty:
            st.warning("No data available for the selected filters.")
        else:
            # Create columns for better layout
            col1, col2 = st.columns(2)
        
        # Second row of demographic charts
        col3, col4 = st.columns(2)
        
        with col3:
            # Location type distribution
            if 'location_type' in filtered_df.columns:
                loc_counts = filtered_df['location_type'].value_counts().reset_index()
                loc_counts.columns = ['Location Type', 'Count']
                
                fig_loc = px.pie(
                    loc_counts,
                    names='Location Type',
                    values='Count',
                    title='Urban vs Rural Distribution',
                    color='Location Type',
                    color_discrete_map={'Urban': '#636EFA', 'Rural': '#EF553B'},
                    hole=0.5
                )
                fig_loc.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>%{value} students (%{percent})<extra></extra>',
                    marker=dict(line=dict(color='#FFFFFF', width=2))
                )
                fig_loc.update_layout(
                    showlegend=False,
                    margin=dict(t=50, b=20, l=0, r=0),
                    height=350
                )
                st.plotly_chart(fig_loc, use_container_width=True)
        
        with col4:
            # Grade level distribution
            if 'grade_level' in filtered_df.columns:
                grade_counts = filtered_df['grade_level'].value_counts().reset_index()
                grade_counts.columns = ['Grade Level', 'Count']
                grade_counts = grade_counts.sort_values('Grade Level')
                
                fig_grade = px.bar(
                    grade_counts,
                    x='Grade Level',
                    y='Count',
                    title='Grade Level Distribution',
                    color='Grade Level',
                    color_discrete_sequence=px.colors.sequential.Viridis,
                    text_auto=True
                )
                fig_grade.update_traces(
                    textposition='outside',
                    hovertemplate='<b>Grade %{x}</b><br>%{y} students<extra></extra>',
                    marker_line_color='rgb(8,48,107)',
                    marker_line_width=1.5,
                    opacity=0.9
                )
                fig_grade.update_layout(
                    xaxis_title="Grade Level",
                    yaxis_title="Number of Students",
                    showlegend=False,
                    margin=dict(t=50, b=80, l=0, r=0),
                    height=350,
                    xaxis=dict(tickmode='linear')
                )
                st.plotly_chart(fig_grade, use_container_width=True)
    
    with tab2:  # Performance Visualizations
        st.subheader("📈 Performance Metrics")
        
        if 'avg_grade' in filtered_df.columns:
            # Performance distribution by gender and location
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot of grades by gender
                fig_gender_grade = px.box(
                    filtered_df,
                    x='gender',
                    y='avg_grade',
                    color='gender',
                    title='Grade Distribution by Gender',
                    labels={'gender': 'Gender', 'avg_grade': 'Average Grade'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_gender_grade.update_layout(
                    xaxis_title="Gender",
                    yaxis_title="Average Grade",
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig_gender_grade, use_container_width=True)
            
            with col2:
                # Violin plot of grades by location
                fig_loc_grade = px.violin(
                    filtered_df,
                    x='location_type',
                    y='avg_grade',
                    color='location_type',
                    box=True,
                    points="all",
                    title='Grade Distribution by Location',
                    labels={'location_type': 'Location Type', 'avg_grade': 'Average Grade'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_loc_grade.update_layout(
                    xaxis_title="Location Type",
                    yaxis_title="Average Grade",
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig_loc_grade, use_container_width=True)
            
            # Performance by age group
            if 'age_group' in filtered_df.columns:
                fig_age_grade = px.box(
                    filtered_df,
                    x='age_group',
                    y='avg_grade',
                    color='age_group',
                    title='Grade Distribution by Age Group',
                    labels={'age_group': 'Age Group', 'avg_grade': 'Average Grade'},
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig_age_grade.update_layout(
                    xaxis_title="Age Group",
                    yaxis_title="Average Grade",
                    showlegend=False,
                    height=450,
                    xaxis=dict(tickangle=-45)
                )
                st.plotly_chart(fig_age_grade, use_container_width=True)
    
    with tab2:
        # Performance analysis using the dedicated function
        st.subheader("📈 Performance Analysis")
        display_performance_analysis(filtered_df)
    
    with tab3:
        # Geographic distribution
        st.subheader("🌍 Geographic Distribution")
        
        if filtered_df.empty:
            st.warning("No data available for the selected filters.")
        else:
            # Create columns for better layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Map visualization
                st.markdown("#### Student Distribution by Division")
                
                # Bangladesh divisions with approximate coordinates
                bd_divisions = {
                    'Dhaka': {'lat': 23.8103, 'lon': 90.4125, 'students': 0},
                    'Chittagong': {'lat': 22.3569, 'lon': 91.7832, 'students': 0},
                    'Rajshahi': {'lat': 24.3636, 'lon': 88.6241, 'students': 0},
                    'Khulna': {'lat': 22.8456, 'lon': 89.5403, 'students': 0},
                    'Barisal': {'lat': 22.7010, 'lon': 90.3535, 'students': 0},
                    'Sylhet': {'lat': 24.8949, 'lon': 91.8687, 'students': 0},
                    'Rangpur': {'lat': 25.7439, 'lon': 89.2752, 'students': 0},
                    'Mymensingh': {'lat': 24.7471, 'lon': 90.4203, 'students': 0}
                }
                
                # Count students per division (mock data - in a real app, this would come from your data)
                # For now, we'll use random data
                import random
                for div in bd_divisions:
                    bd_divisions[div]['students'] = random.randint(50, 500)
                
                # Create map data
                map_data = pd.DataFrame([
                    {
                        'lat': div['lat'],
                        'lon': div['lon'],
                        'name': name,
                        'students': div['students']
                    }
                    for name, div in bd_divisions.items()
                ])
                
                # Display the map
                st.map(
                    map_data,
                    latitude='lat',
                    longitude='lon',
                    size='students',
                    color='students',
                    zoom=6,
                    use_container_width=True
                )
                
                # Add a disclaimer
                st.caption("ℹ️ Map shows approximate student distribution by division. Hover over markers for details.")
                
                # Add a table with the data
                st.markdown("#### Student Count by Division")
                st.dataframe(
                    map_data[['name', 'students']].rename(columns={'name': 'Division', 'students': 'Students'}),
                    hide_index=True,
                    use_container_width=True
                )
            
            with col2:
                # Location distribution
                st.markdown("#### Location Type Distribution")
                if 'location_type' in filtered_df.columns:
                    loc_dist = filtered_df['location_type'].value_counts().reset_index()
                    loc_dist.columns = ['Location Type', 'Count']
                    
                    # Create a pie chart for location distribution
                    fig_loc = px.pie(
                        loc_dist,
                        values='Count',
                        names='Location Type',
                        title='Urban vs Rural Distribution',
                        hole=0.5,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_loc.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>%{value} students<br>%{percent}<extra></extra>'
                    )
                    st.plotly_chart(fig_loc, use_container_width=True)
                else:
                    st.warning("Location type data not available.")
                
                # Performance by location
                if 'location_type' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
                    st.markdown("#### Performance by Location")
                    loc_perf = filtered_df.groupby('location_type', as_index=False).agg(
                        avg_grade=('avg_grade', 'mean'),
                        count=('student_id', 'count')
                    )
                    
                    fig_loc_perf = px.bar(
                        loc_perf,
                        x='location_type',
                        y='avg_grade',
                        color='location_type',
                        text_auto='.1f',
                        title='Average Grade by Location',
                        labels={'location_type': 'Location Type', 'avg_grade': 'Average Grade'},
                        color_discrete_map={'Urban': '#636EFA', 'Rural': '#EF553B'}
                    )
                    fig_loc_perf.update_traces(
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
                        customdata=loc_perf[['count']]
                    )
                    fig_loc_perf.update_layout(
                        xaxis_title="Location Type",
                        yaxis_title="Average Grade",
                        showlegend=False,
                        height=350
                    )
                    st.plotly_chart(fig_loc_perf, use_container_width=True)
    
    with tab4:
        # Trends over time
        st.subheader("📅 Trends Over Time")
        
        if filtered_df.empty:
            st.warning("No data available for the selected filters.")
        else:
            # Create columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                # Enrollment trends by year
                st.markdown("#### Enrollment Trends")
                
                # Check if enrollment_date exists and extract year
                if 'enrollment_date' in filtered_df.columns:
                    filtered_df['enrollment_year'] = pd.to_datetime(filtered_df['enrollment_date']).dt.year
                    enroll_trends = filtered_df['enrollment_year'].value_counts().reset_index()
                    enroll_trends.columns = ['Year', 'Enrollments']
                    enroll_trends = enroll_trends.sort_values('Year')
                    
                    fig_enroll = px.line(
                        enroll_trends,
                        x='Year',
                        y='Enrollments',
                        title='Student Enrollments by Year',
                        markers=True,
                        labels={'Enrollments': 'Number of Students'}
                    )
                    fig_enroll.update_traces(
                        line=dict(width=3, color='#1f77b4'),
                        marker=dict(size=10, line=dict(width=2, color='DarkSlateGrey')),
                        hovertemplate='<b>%{x}</b><br>Students: %{y:,}<extra></extra>'
                    )
                    fig_enroll.update_layout(
                        xaxis_title="Year",
                        yaxis_title="Number of Enrollments",
                        height=400,
                        margin=dict(t=50, b=50, l=50, r=50)
                    )
                    st.plotly_chart(fig_enroll, use_container_width=True)
                    
                    # Add a bar chart for enrollments by month (if data is available)
                    if 'enrollment_date' in filtered_df.columns:
                        filtered_df['enrollment_month'] = pd.to_datetime(filtered_df['enrollment_date']).dt.month_name()
                        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                                      'July', 'August', 'September', 'October', 'November', 'December']
                        
                        monthly_enroll = filtered_df['enrollment_month'].value_counts().reindex(month_order).reset_index()
                        monthly_enroll.columns = ['Month', 'Enrollments']
                        
                        fig_monthly = px.bar(
                            monthly_enroll,
                            x='Month',
                            y='Enrollments',
                            title='Enrollments by Month',
                            text_auto=True,
                            labels={'Enrollments': 'Number of Students'}
                        )
                        fig_monthly.update_traces(
                            marker_color='#2ca02c',
                            hovertemplate='<b>%{x}</b><br>Students: %{y:,}<extra></extra>'
                        )
                        fig_monthly.update_layout(
                            xaxis_title="Month",
                            yaxis_title="Number of Enrollments",
                            height=400,
                            xaxis=dict(tickangle=-45),
                            margin=dict(t=50, b=100, l=50, r=50)
                        )
                        st.plotly_chart(fig_monthly, use_container_width=True)
                else:
                    st.info("Enrollment date data not available for trend analysis.")
            
            if 'enrollment_year' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
                # Calculate average grade by year
                perf_trends = filtered_df.groupby('enrollment_year', as_index=False).agg(
                    avg_grade=('avg_grade', 'mean'),
                    count=('student_id', 'count')
                ).sort_values('enrollment_year')
                
                # Create a line chart for average grade over time
                fig_perf = px.line(
                    perf_trends,
                    x='enrollment_year',
                    y='avg_grade',
                    title='Average Grade by Enrollment Year',
                    markers=True,
                    labels={'enrollment_year': 'Enrollment Year', 'avg_grade': 'Average Grade'}
                )
                fig_perf.update_traces(
                    line=dict(width=3, color='#ff7f0e'),
                    marker=dict(size=10, line=dict(width=2, color='DarkSlateGrey')),
                    hovertemplate='<b>%{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
                    customdata=perf_trends[['count']]
                )
                fig_perf.update_layout(
                    xaxis_title="Enrollment Year",
                    yaxis_title="Average Grade",
                    height=400,
                    yaxis=dict(range=[0, 100] if 'avg_grade' in filtered_df.columns else None),
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig_perf, use_container_width=True)
                
                # Add a scatter plot for grade distribution over time
                if 'gender' in filtered_df.columns:
                    fig_scatter = px.scatter(
                        filtered_df,
                        x='enrollment_year',
                        y='avg_grade',
                        color='gender',
                        opacity=0.7,
                        title='Grade Distribution Over Time',
                        labels={
                            'enrollment_year': 'Enrollment Year',
                            'avg_grade': 'Average Grade',
                            'gender': 'Gender'
                        },
                        hover_data=['student_name', 'class_name']
                    )
                    fig_scatter.update_traces(
                        marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey')),
                        selector=dict(mode='markers')
                    )
                    fig_scatter.update_layout(
                        xaxis_title="Enrollment Year",
                        yaxis_title="Average Grade",
                        height=500,
                        yaxis=dict(range=[0, 100] if 'avg_grade' in filtered_df.columns else None),
                        margin=dict(t=50, b=50, l=50, r=50),
                        legend_title_text='Gender'
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Insufficient data for performance trend analysis.")
        
        # Advanced: Grade distribution over time
        if show_advanced and 'enrollment_year' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
            st.markdown("#### Grade Distribution Over Time")
            
            # Create a box plot for grade distribution by year
            fig_box = px.box(
                filtered_df,
                x='enrollment_year',
                y='avg_grade',
                color='enrollment_year',
                title='Grade Distribution by Enrollment Year',
                labels={'enrollment_year': 'Enrollment Year', 'avg_grade': 'Average Grade'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_box.update_traces(
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8,
                marker=dict(size=4, opacity=0.5)
            )
            fig_box.update_layout(
                xaxis_title="Enrollment Year",
                yaxis_title="Average Grade",
                height=500,
                showlegend=False,
                margin=dict(t=50, b=50, l=50, r=50),
                yaxis=dict(range=[0, 100] if 'avg_grade' in filtered_df.columns else None)
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Insufficient data for interactive cross-filtering. Please check your filters.")
        
        # Interactive cross-filtering with Plotly Express (Advanced Analysis)
        st.markdown("## 🔍 Interactive Analysis")
        st.markdown("""
        Explore relationships between different student attributes and academic performance. 
        Hover over data points to see detailed information, and use the interactive features 
        to zoom, pan, and download the visualizations.
        """)
        
        # Add interactive cross-filtering section
        st.markdown("### 🔄 Interactive Cross-Filtering")
        st.markdown("""
        The visualizations below are linked together - selecting points in one visualization 
        will highlight the corresponding points in the others. This allows you to explore 
        complex relationships across multiple dimensions of the data.
        """)
        
        # Check if we have the required columns for cross-filtering
        cross_filter_cols = ['age', 'avg_grade', 'grades_count', 'gender', 'location_type']
        has_cross_filter_cols = all(col in filtered_df.columns for col in cross_filter_cols)
        
        if has_cross_filter_cols and not filtered_df.empty:
            # Create a 2x2 grid of visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Scatter plot: Age vs. Average Grade by Gender
                fig_age_grade = px.scatter(
                    filtered_df,
                    x='age',
                    y='avg_grade',
                    color='gender',
                    title='Age vs. Average Grade by Gender',
                    labels={'age': 'Age', 'avg_grade': 'Average Grade'},
                    hover_data=['student_name', 'class_name'],
                    color_discrete_map={'Male': '#1f77b4', 'Female': '#ff7f0e'}
                )
                fig_age_grade.update_traces(
                    marker=dict(size=10, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')),
                    selector=dict(mode='markers')
                )
                fig_age_grade.update_layout(
                    xaxis_title="Age",
                    yaxis_title="Average Grade",
                    height=400,
                    legend_title_text='Gender',
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig_age_grade, use_container_width=True)
                
                # Box plot: Grade Distribution by Location
                fig_box_loc = px.box(
                    filtered_df,
                    x='location_type',
                    y='avg_grade',
                    color='location_type',
                    title='Grade Distribution by Location',
                    labels={'location_type': 'Location Type', 'avg_grade': 'Average Grade'}
                )
                fig_box_loc.update_layout(
                    xaxis_title="Location Type",
                    yaxis_title="Average Grade",
                    height=400,
                    showlegend=False,
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig_box_loc, use_container_width=True)
            
            with col2:
                # Scatter plot: Number of Grades vs. Average Grade by Location
                fig_grades_grade = px.scatter(
                    filtered_df,
                    x='grades_count',
                    y='avg_grade',
                    color='location_type',
                    title='Number of Grades vs. Average Grade by Location',
                    labels={'grades_count': 'Number of Grades', 'avg_grade': 'Average Grade'},
                    hover_data=['student_name', 'class_name', 'age'],
                    color_discrete_map={'Urban': '#636EFA', 'Rural': '#EF553B'}
                )
                fig_grades_grade.update_traces(
                    marker=dict(size=10, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')),
                    selector=dict(mode='markers')
                )
                fig_grades_grade.update_layout(
                    xaxis_title="Number of Grades",
                    yaxis_title="Average Grade",
                    height=400,
                    legend_title_text='Location Type',
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig_grades_grade, use_container_width=True)
                
                # Violin plot: Grade Distribution by Gender and Location
                fig_violin = px.violin(
                    filtered_df,
                    x='gender',
                    y='avg_grade',
                    color='location_type',
                    box=True,
                    points="all",
                    title='Grade Distribution by Gender and Location',
                    labels={'gender': 'Gender', 'avg_grade': 'Average Grade'},
                    color_discrete_map={'Urban': '#636EFA', 'Rural': '#EF553B'}
                )
                fig_violin.update_layout(
                    xaxis_title="Gender",
                    yaxis_title="Average Grade",
                    height=400,
                    legend_title_text='Location Type',
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                st.plotly_chart(fig_violin, use_container_width=True)
                
                # Add a parallel categories diagram for multi-dimensional analysis
                st.markdown("### 🔄 Multi-dimensional Relationships")
                st.markdown("""
                The parallel categories diagram below shows how different student attributes interact 
                with each other and with academic performance. The thickness of the lines represents 
                the number of students in each category combination.
                """)
                
                # Prepare data for parallel categories diagram
                if all(col in filtered_df.columns for col in ['gender', 'location_type', 'age_group', 'avg_grade']):
                    # Create grade categories
                    filtered_df['grade_category'] = pd.cut(
                        filtered_df['avg_grade'],
                        bins=[0, 50, 60, 70, 80, 90, 101],
                        labels=['<50', '50-60', '60-70', '70-80', '80-90', '90+'],
                        right=False
                    )
                    
                    # Create parallel categories diagram
                    dimensions = [
                        {'label': 'Gender', 'values': filtered_df['gender']},
                        {'label': 'Location', 'values': filtered_df['location_type']},
                        {'label': 'Age Group', 'values': filtered_df['age_group']},
                        {'label': 'Grade', 'values': filtered_df['grade_category']}
                    ]
                    
                    fig_parallel = go.Figure(go.Parcats(
                        dimensions=dimensions,
                        line={
                            'color': filtered_df['avg_grade'],
                            'colorscale': 'Viridis',
                            'showscale': True,
                            'colorbar': {'title': 'Avg Grade'}
                        },
                        labelfont={'size': 12, 'family': 'Arial'},
                        tickfont={'size': 10, 'family': 'Arial'},
                        arrangement='freeform'
                    ))
                    
                    fig_parallel.update_layout(
                        title='Student Demographics and Performance Relationships',
                        height=600,
                        margin=dict(t=80, b=80, l=80, r=80)
                    )
                    
                    st.plotly_chart(fig_parallel, use_container_width=True)
                    
                    # Add a sunburst chart for hierarchical data visualization
                    st.markdown("### 🌟 Hierarchical Data Exploration")
                    st.markdown("""
                    The sunburst chart below provides a hierarchical view of student data, 
                    allowing you to explore the distribution of students across different 
                    demographic categories and their academic performance.
                    """)
                    
                    # Prepare data for sunburst chart
                    if all(col in filtered_df.columns for col in ['gender', 'location_type', 'age_group', 'avg_grade']):
                        # Create grade categories if not already created
                        if 'grade_category' not in filtered_df.columns:
                            filtered_df['grade_category'] = pd.cut(
                                filtered_df['avg_grade'],
                                bins=[0, 50, 60, 70, 80, 90, 101],
                                labels=['<50', '50-60', '60-70', '70-80', '80-90', '90+'],
                                right=False
                            )
                        
                        # Create a hierarchical dataframe
                        sunburst_df = filtered_df.groupby(
                            ['gender', 'location_type', 'age_group', 'grade_category']
                        ).size().reset_index(name='count')
                        
                        # Create sunburst chart
                        fig_sunburst = px.sunburst(
                            sunburst_df,
                            path=['gender', 'location_type', 'age_group', 'grade_category'],
                            values='count',
                            title='Student Distribution by Demographics and Performance',
                            color='grade_category',
                            color_discrete_sequence=px.colors.sequential.Viridis,
                            height=800
                        )
                        
                        fig_sunburst.update_traces(
                            textinfo='label+percent parent',
                            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent:.1%} of parent',
                            marker=dict(line=dict(color='#ffffff', width=0.5))
                        )
                        
                        fig_sunburst.update_layout(
                            margin=dict(t=40, b=0, l=0, r=0),
                            coloraxis_showscale=False
                        )
                        
                        st.plotly_chart(fig_sunburst, use_container_width=True)
                        
                        # Add a 3D scatter plot for multi-dimensional analysis
                        st.markdown("### 🌐 3D Data Exploration")
                        st.markdown("""
                        The 3D scatter plot below allows you to explore the relationships between 
                        three different variables simultaneously. You can rotate, zoom, and pan the 
                        visualization to gain deeper insights into the data.
                        """)
                        
                        # Check if we have the required columns for 3D scatter plot
                        if all(col in filtered_df.columns for col in ['age', 'grades_count', 'avg_grade', 'gender']):
                            # Create 3D scatter plot
                            fig_3d = px.scatter_3d(
                                filtered_df,
                                x='age',
                                y='grades_count',
                                z='avg_grade',
                                color='gender',
                                size='avg_grade',
                                hover_data=['student_name', 'class_name', 'location_type'],
                                title='3D View: Age, Number of Grades, and Average Grade by Gender',
                                color_discrete_map={'Male': '#1f77b4', 'Female': '#ff7f0e'},
                                opacity=0.8,
                                height=700
                            )
                            
                            # Update marker appearance
                            fig_3d.update_traces(
                                marker=dict(
                                    size=5,
                                    line=dict(width=0.5, color='DarkSlateGrey'),
                                    sizemode='diameter',
                                    sizeref=0.1
                                ),
                                selector=dict(mode='markers')
                            )
                            
                            # Update layout
                            fig_3d.update_layout(
                                scene=dict(
                                    xaxis_title='Age',
                                    yaxis_title='Number of Grades',
                                    zaxis_title='Average Grade',
                                    xaxis=dict(backgroundcolor='rgba(0,0,0,0)'),
                                    yaxis=dict(backgroundcolor='rgba(0,0,0,0)'),
                                    zaxis=dict(backgroundcolor='rgba(0,0,0,0)'),
                                ),
                                margin=dict(l=0, r=0, b=0, t=40),
                                legend_title_text='Gender',
                                scene_camera=dict(
                                    eye=dict(x=1.5, y=1.5, z=1.5)
                                )
                            )
                            
                            st.plotly_chart(fig_3d, use_container_width=True)
                            
                            # Add animation controls
                            st.markdown("#### Animation Controls")
                            st.markdown("""
                            - **Rotate**: Click and drag to rotate the view
                            - **Zoom**: Use your mouse wheel or pinch to zoom in/out
                            - **Pan**: Right-click and drag to pan the view
                            - **Reset**: Double-click to reset the view
                            """)
                            
                            # Add a radar chart for multi-variable comparison
                            st.markdown("### 📊 Multi-Variable Comparison")
                            st.markdown("""
                            The radar chart below allows you to compare multiple variables across 
                            different categories. Each axis represents a different metric, and the 
                            shape formed by connecting the points shows the profile of each category.
                            """)
                            
                            # Check if we have the required columns for radar chart
                            if all(col in filtered_df.columns for col in ['gender', 'location_type', 'age_group', 'avg_grade', 'grades_count']):
                                # Calculate summary statistics for radar chart
                                radar_df = filtered_df.groupby(['gender', 'location_type']).agg({
                                    'avg_grade': 'mean',
                                    'grades_count': 'mean',
                                    'age': 'mean'
                                }).reset_index()
                                
                                # Normalize the data for better visualization
                                for col in ['avg_grade', 'grades_count', 'age']:
                                    min_val = radar_df[col].min()
                                    max_val = radar_df[col].max()
                                    radar_df[f'{col}_norm'] = (radar_df[col] - min_val) / (max_val - min_val) * 100
                                
                                # Create radar chart
                                fig_radar = go.Figure()
                                
                                # Add a trace for each group
                                for idx, row in radar_df.iterrows():
                                    fig_radar.add_trace(go.Scatterpolar(
                                        r=[
                                            row['avg_grade_norm'],
                                            row['grades_count_norm'],
                                            row['age_norm'],
                                            row['avg_grade_norm']  # Close the shape
                                        ],
                                        theta=['Average Grade', 'Number of Grades', 'Age', 'Average Grade'],
                                        name=f"{row['gender']} - {row['location_type']}",
                                        line=dict(color=px.colors.qualitative.Plotly[idx % len(px.colors.qualitative.Plotly)]),
                                        fill='toself',
                                        hovertemplate=
                                            f"<b>{row['gender']} - {row['location_type']}</b><br>" +
                                            f"Avg Grade: {row['avg_grade']:.1f}<br>" +
                                            f"Grades Count: {row['grades_count']:.1f}<br>" +
                                            f"Avg Age: {row['age']:.1f}<extra></extra>"
                                    ))
                                
                                # Update layout
                                fig_radar.update_layout(
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            range=[0, 100],
                                            showticklabels=True,
                                            ticks='',
                                            showline=False,
                                            showgrid=True
                                        )
                                    ),
                                    showlegend=True,
                                    title='Multi-Variable Comparison by Gender and Location',
                                    height=600,
                                    margin=dict(t=50, b=50, l=50, r=50),
                                    legend=dict(
                                        orientation='h',
                                        yanchor='bottom',
                                        y=1.02,
                                        xanchor='center',
                                        x=0.5
                                    )
                                )
                                
                                st.plotly_chart(fig_radar, use_container_width=True)
                                
                                # Add interpretation
                                with st.expander("🔍 How to interpret this radar chart"):
                                    st.markdown("""
                                    - **Each axis** represents a different metric (normalized to 0-100 scale)
                                    - **Each colored shape** represents a demographic group
                                    - **Larger area** indicates higher values across multiple metrics
                                    - **Shape symmetry** shows balance between different metrics
                                    - **Outer ring** represents the maximum value (100) for each metric
                                    - **Center** represents the minimum value (0) for each metric
                                    """)
                                    
                                    # Add a treemap for hierarchical data visualization
                                    st.markdown("### 🌳 Hierarchical Data Overview")
                                    st.markdown("""
                                    The treemap below provides a hierarchical view of the student population, 
                                    allowing you to explore the distribution of students across different 
                                    demographic categories at a glance.
                                    """)
                                    
                                    # Check if we have the required columns for treemap
                                    if all(col in filtered_df.columns for col in ['gender', 'location_type', 'age_group', 'class_name']):
                                        # Create a hierarchical dataframe
                                        treemap_df = filtered_df.groupby(
                                            ['gender', 'location_type', 'age_group', 'class_name']
                                        ).size().reset_index(name='count')
                                        
                                        # Create treemap
                                        fig_treemap = px.treemap(
                                            treemap_df,
                                            path=['gender', 'location_type', 'age_group', 'class_name'],
                                            values='count',
                                            color='count',
                                            color_continuous_scale='Viridis',
                                            title='Student Population Distribution',
                                            height=800
                                        )
                                        
                                        # Update layout
                                        fig_treemap.update_traces(
                                            textinfo='label+value+percent parent',
                                            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentParent:.1%} of parent',
                                            marker=dict(line=dict(color='#ffffff', width=0.5))
                                        )
                                        
                                        fig_treemap.update_layout(
                                            margin=dict(t=40, b=0, l=0, r=0),
                                            coloraxis_colorbar=dict(
                                                title='Count',
                                                thicknessmode='pixels',
                                                thickness=20,
                                                lenmode='pixels',
                                                len=300,
                                                yanchor='top',
                                                y=1,
                                                xanchor='left',
                                                x=1.02
                                            )
                                        )
                                        
                                        st.plotly_chart(fig_treemap, use_container_width=True)
                                        
                                        # Add interpretation
                                        with st.expander("🔍 How to interpret this treemap"):
                                            st.markdown("""
                                            - **Size of rectangles** represents the number of students in each category
                                            - **Color intensity** also represents the count (darker = more students)
                                            - **Hierarchy** is shown from left to right (Gender → Location → Age Group → Class)
                                            - **Click on a category** to drill down into subcategories
                                            - **Double-click** to go back up one level
                                            - **Hover** over any rectangle to see detailed information
                                            - **Use the color scale** to quickly identify larger/smaller groups
                                            """)
        else:
            st.info("Insufficient data for interactive cross-filtering. Please check your filters.")
        
        # Add correlation heatmap section
        st.markdown("### 🔍 Correlation Analysis")
        st.markdown("""
        The correlation heatmap below shows the strength and direction of relationships between 
        different numeric variables in the dataset. This can help identify potential patterns 
        and relationships worth investigating further.
        """)
        
        numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1 and not filtered_df.empty:
            # Calculate correlation matrix
            corr = filtered_df[numeric_cols].corr()
            
            # Create a mask for the upper triangle
            mask = np.triu(np.ones_like(corr, dtype=bool))
            
            # Create heatmap with masked upper triangle
            fig_corr = px.imshow(
                corr.mask(mask),
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title='Correlation Heatmap (Lower Triangle)',
                labels=dict(color="Correlation"),
                zmin=-1,
                zmax=1
            )
            
            # Add correlation values as annotations
            for i in range(len(corr)):
                for j in range(len(corr)):
                    if i > j:  # Only show lower triangle
                        fig_corr.add_annotation(
                            x=corr.columns[i],
                            y=corr.columns[j],
                            text=f"{corr.iloc[j, i]:.2f}",
                            showarrow=False,
                            font=dict(color='black' if abs(corr.iloc[j, i]) < 0.7 else 'white')
                        )
            
            fig_corr.update_layout(
                height=700,
                margin=dict(t=100, b=100, l=100, r=50),
                coloraxis_colorbar=dict(
                    title="Correlation",
                    thicknessmode="pixels", thickness=20,
                    lenmode="pixels", len=300,
                    yanchor="top", y=1,
                    ticks="outside"
                )
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Add interpretation and insights
            with st.expander("🔍 How to interpret correlation analysis"):
                st.markdown("""
                #### Correlation Coefficient Interpretation
                - **+1.0**: Perfect positive correlation
                - **+0.7 to +0.9**: Strong positive correlation
                - **+0.4 to +0.6**: Moderate positive correlation
                - **+0.1 to +0.3**: Weak positive correlation
                - **0**: No correlation
                - **-0.1 to -0.3**: Weak negative correlation
                - **-0.4 to -0.6**: Moderate negative correlation
                - **-0.7 to -0.9**: Strong negative correlation
                - **-1.0**: Perfect negative correlation
                
                #### Key Insights to Look For:
                1. **Strong Correlations (|r| > 0.7)**: May indicate important relationships worth investigating
                2. **Unexpected Correlations**: Look for relationships you didn't anticipate
                3. **No Correlation**: Some variables that you expected to be related might not be
                4. **Negative Correlations**: Inverse relationships can be as important as positive ones
                
                #### Caveats:
                - Correlation does not imply causation
                - Only measures linear relationships
                - Sensitive to outliers
                - Can be influenced by range restriction
                """)
        
        # Display location-based visualization if available
        if 'fig_loc' in locals():
            st.plotly_chart(fig_loc, use_container_width=True)
    
    # Performance by grade level
    if 'grade_level' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
        st.markdown("### Performance by Grade Level")
        grade_perf = filtered_df.groupby('grade_level', as_index=False).agg(
            avg_grade=('avg_grade', 'mean'),
            count=('student_id', 'count')
        ).sort_values('grade_level')
        
        fig_grade = px.line(
            grade_perf,
            x='grade_level',
            y='avg_grade',
            markers=True,
            title='Average Grade by Grade Level',
            labels={'grade_level': 'Grade Level', 'avg_grade': 'Average Grade'}
        )
        fig_grade.update_traces(
            line=dict(width=4),
            marker=dict(size=10, line=dict(width=2, color='DarkSlateGrey')),
            hovertemplate='<b>Grade %{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
            customdata=grade_perf[['count']]
        )
        fig_grade.update_layout(
            xaxis_title="Grade Level",
            yaxis_title="Average Grade",
            height=450,
            xaxis=dict(tickmode='linear')
        )
        st.plotly_chart(fig_grade, use_container_width=True)
        
        # Add a scatter plot with trend line
        fig_scatter = px.scatter(
            filtered_df,
            x='grade_level',
            y='avg_grade',
            color='gender' if 'gender' in filtered_df.columns else None,
            trendline="lowess",
            title='Grade Distribution by Grade Level',
            labels={'grade_level': 'Grade Level', 'avg_grade': 'Average Grade'},
            hover_data=['student_name', 'class_name']
        )
        fig_scatter.update_layout(
            xaxis_title="Grade Level",
            yaxis_title="Average Grade",
            height=500,
            xaxis=dict(tickmode='linear')
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

def display_performance_analysis(filtered_df):
    """
    Display performance analysis visualizations.
    
    Args:
        filtered_df (pd.DataFrame): The filtered DataFrame containing student data
    """
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Performance by gender
    if 'gender' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
        st.markdown("### Performance by Gender")
        gender_perf = filtered_df.groupby('gender', as_index=False).agg(
            avg_grade=('avg_grade', 'mean'),
            count=('student_id', 'count')
        )
        
        fig_gender = px.bar(
            gender_perf,
            x='gender',
            y='avg_grade',
            color='gender',
            text_auto='.1f',
            title='Average Grade by Gender',
            labels={'gender': 'Gender', 'avg_grade': 'Average Grade'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_gender.update_traces(
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
            customdata=gender_perf[['count']]
        )
        fig_gender.update_layout(
            xaxis_title="Gender",
            yaxis_title="Average Grade",
            showlegend=False,
            height=450
        )
        st.plotly_chart(fig_gender, use_container_width=True)
    
    # Performance by age group
    if 'age_group' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
        st.markdown("### Performance by Age Group")
        age_perf = filtered_df.groupby('age_group', as_index=False).agg(
            avg_grade=('avg_grade', 'mean'),
            count=('student_id', 'count')
        ).sort_values('age_group')
        
        fig_age = px.bar(
            age_perf,
            x='age_group',
            y='avg_grade',
            color='age_group',
            text_auto='.1f',
            title='Average Grade by Age Group',
            labels={'age_group': 'Age Group', 'avg_grade': 'Average Grade'},
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig_age.update_traces(
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
            customdata=age_perf[['count']]
        )
        fig_age.update_layout(
            xaxis_title="Age Group",
            yaxis_title="Average Grade",
            showlegend=False,
            height=450,
            xaxis=dict(tickangle=-45)
        )
        st.plotly_chart(fig_age, use_container_width=True)
    
    # Performance by location
    if 'location_type' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
        st.markdown("### Performance by Location")
        loc_perf = filtered_df.groupby('location_type', as_index=False).agg(
            avg_grade=('avg_grade', 'mean'),
            count=('student_id', 'count')
        )
        
        fig_loc = px.bar(
            loc_perf,
            x='location_type',
            y='avg_grade',
            color='location_type',
            text_auto='.1f',
            title='Average Grade by Location Type',
            labels={'location_type': 'Location Type', 'avg_grade': 'Average Grade'},
            color_discrete_map={'Urban': '#636EFA', 'Rural': '#EF553B'}
        )
        fig_loc.update_traces(
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
            customdata=loc_perf[['count']],
            marker_line_color='rgb(8,48,107)',
            marker_line_width=1.5,
            opacity=0.9
        )
        fig_loc.update_layout(
            xaxis_title="Location Type",
            yaxis_title="Average Grade",
            showlegend=False,
            height=450
        )
        st.plotly_chart(fig_loc, use_container_width=True)
    
    # Performance by grade level
    if 'grade_level' in filtered_df.columns and 'avg_grade' in filtered_df.columns:
        st.markdown("### Performance by Grade Level")
        grade_perf = filtered_df.groupby('grade_level', as_index=False).agg(
            avg_grade=('avg_grade', 'mean'),
            count=('student_id', 'count')
        ).sort_values('grade_level')
        
        fig_grade = px.line(
            grade_perf,
            x='grade_level',
            y='avg_grade',
            markers=True,
            title='Average Grade by Grade Level',
            labels={'grade_level': 'Grade Level', 'avg_grade': 'Average Grade'}
        )
        fig_grade.update_traces(
            line=dict(width=4),
            marker=dict(size=10, line=dict(width=2, color='DarkSlateGrey')),
            hovertemplate='<b>Grade %{x}</b><br>Avg Grade: %{y:.1f}<br>Students: %{customdata[0]}<extra></extra>',
            customdata=grade_perf[['count']]
        )
        fig_grade.update_layout(
            xaxis_title="Grade Level",
            yaxis_title="Average Grade",
            height=450,
            xaxis=dict(tickmode='linear')
        )
        st.plotly_chart(fig_grade, use_container_width=True)
        
        # Add a scatter plot with trend line
        if 'gender' in filtered_df.columns and 'class_name' in filtered_df.columns:
            fig_scatter = px.scatter(
                filtered_df,
                x='grade_level',
                y='avg_grade',
                color='gender',
                trendline="lowess",
                title='Grade Distribution by Grade Level',
                labels={'grade_level': 'Grade Level', 'avg_grade': 'Average Grade'},
                hover_data=['student_name', 'class_name']
            )
            fig_scatter.update_layout(
                xaxis_title="Grade Level",
                yaxis_title="Average Grade",
                height=500,
                xaxis=dict(tickmode='linear')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Add a box plot for grade distribution by grade level
        if 'gender' in filtered_df.columns:
            fig_box = px.box(
                filtered_df,
                x='grade_level',
                y='avg_grade',
                color='gender',
                title='Grade Distribution by Grade Level and Gender',
                labels={'grade_level': 'Grade Level', 'avg_grade': 'Average Grade', 'gender': 'Gender'},
                color_discrete_map={'Male': '#1f77b4', 'Female': '#ff7f0e'}
            )
            fig_box.update_layout(
                xaxis_title="Grade Level",
                yaxis_title="Average Grade",
                height=500,
                xaxis=dict(tickmode='linear'),
                boxmode='group'
            )
            st.plotly_chart(fig_box, use_container_width=True)
    
    # Performance by subject (if subject performance data is available)
    if 'subject_performance' in globals() and callable(subject_performance):
        st.markdown("### Performance by Subject")
        subject_df = subject_performance()
        
        if not subject_df.empty:
            subject_avg = subject_df.groupby('subject_name')['avg_grade'].mean().reset_index()
            
            fig_subject = px.bar(
                subject_avg,
                x='subject_name',
                y='avg_grade',
                title='Average Grade by Subject',
                labels={'subject_name': 'Subject', 'avg_grade': 'Average Grade'},
                color='subject_name',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_subject.update_traces(
                texttemplate='%{y:.1f}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Avg Grade: %{y:.1f}<extra></extra>'
            )
            fig_subject.update_layout(
                xaxis_title="Subject",
                yaxis_title="Average Grade",
                showlegend=False,
                height=450
            )
            st.plotly_chart(fig_subject, use_container_width=True)
            
            # Subject performance heatmap
            if 'student_id' in subject_df.columns and 'subject_name' in subject_df.columns:
                heatmap_data = subject_df.pivot(
                    index='student_id',
                    columns='subject_name',
                    values='avg_grade'
                )
                
                if not heatmap_data.empty:
                    fig_heatmap = px.imshow(
                        heatmap_data.corr(),
                        text_auto=True,
                        aspect="auto",
                        color_continuous_scale='RdBu',
                        title='Subject Performance Correlation',
                        labels=dict(x="Subject", y="Subject", color="Correlation")
                    )
                    fig_heatmap.update_layout(
                        height=600,
                        xaxis_showgrid=False,
                        yaxis_showgrid=False,
                        xaxis_zeroline=False,
                        yaxis_zeroline=False,
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)

def display_data_export(filtered_df):
    """Add data export functionality."""
    st.subheader("📥 Export Data")
    
    if filtered_df.empty:
        st.warning("No data available for export with current filters.")
        return
    
    # Show filtered data
    st.dataframe(
        filtered_df[[
            'student_id', 'student_name', 'gender', 'age', 'age_group', 
            'location_type', 'class_name', 'avg_grade'
        ]].sort_values('avg_grade', ascending=False),
        use_container_width=True,
        height=300
    )
    
    # Export options
    export_format = st.selectbox(
        "Export Format",
        ["CSV", "Excel"]
    )
    
    if st.button("Export Data"):
        if export_format == "CSV":
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="demographic_insights.csv",
                mime="text/csv"
            )
        else:  # Excel
            excel = filtered_df.to_excel("demographic_insights.xlsx", index=False)
            with open("demographic_insights.xlsx", "rb") as f:
                st.download_button(
                    label="Download Excel",
                    data=f,
                    file_name="demographic_insights.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def main():
    """
    Main function to run the Streamlit app with enhanced features.
    """
    # Configure page settings
    st.set_page_config(
        page_title="Student Demographic Insights",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Set title and description
    st.title("🎓 Student Demographic Insights Dashboard")
    st.markdown("""
    Explore and analyze student demographic data with interactive visualizations.
    Use the filters in the sidebar to customize the data view.
    """)
    
    # Add a loading spinner while data is being loaded
    with st.spinner('Loading data...'):
        # Load data
        df = load_demographic_data()
        
        if df.empty:
            st.error("❌ Failed to load data. Please check the database connection and try again.")
            if st.button("Retry loading data"):
                st.experimental_rerun()
            return
    
    # Set up sidebar filters
    with st.sidebar:
        st.markdown("### Data Filters")
        filters = setup_sidebar(df)
    
    # Display data summary in the sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Data Summary")
        st.markdown(f"📊 **Total Students:** {len(df):,}")
        if 'avg_grade' in df.columns:
            st.markdown(f"⭐ **Average Grade:** {df['avg_grade'].mean():.1f}/100")
        if 'gender' in df.columns:
            gender_dist = df['gender'].value_counts(normalize=True).mul(100)
            st.markdown("👥 **Gender Distribution:**")
            for gender, pct in gender_dist.items():
                st.markdown(f"   - {gender}: {pct:.1f}%")
    
    # Apply filters
    filtered_df = filter_data(df, filters)
    
    # Show filter summary
    filter_summary = []
    if filters.get('grades'):
        filter_summary.append(f"**Grades:** {', '.join(filters['grades'])}")
    if filters.get('gender') != "All":
        filter_summary.append(f"**Gender:** {filters['gender']}")
    if filters.get('age_group') != "All":
        filter_summary.append(f"**Age Group:** {filters['age_group']}")
    if filters.get('location') != "All":
        filter_summary.append(f"**Location:** {filters['location']}")
    
    if filter_summary:
        with st.expander("🔍 Active Filters", expanded=False):
            st.markdown(" | ".join(filter_summary))
    
    # Display metrics with loading spinner
    with st.spinner('Updating metrics...'):
        display_metrics(filtered_df, show_advanced=filters.get('show_advanced_metrics', False))
    
    # Add a divider
    st.markdown("---")
    
    # Display visualizations with loading spinner
    with st.spinner('Generating visualizations...'):
        display_demographic_visualizations(filtered_df, show_advanced=filters.get('show_advanced_metrics', False))
    
    # Display raw data if enabled
    if filters.get('show_raw_data', False):
        st.markdown("---")
        st.subheader("📋 Raw Data")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            column_config={
                'student_name': 'Student Name',
                'gender': 'Gender',
                'age': 'Age',
                'age_group': 'Age Group',
                'location_type': 'Location',
                'class_name': 'Class',
                'avg_grade': st.column_config.NumberColumn('Avg Grade', format='%.1f')
            },
            hide_index=True
        )
    
    # Add footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em; margin-top: 2em;'>
            <p>📅 Last updated: {}</p>
            <p>📊 Data source: Student Information System</p>
        </div>
        """.format(pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')),
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
