"""
Student Performance Dashboard
---------------------------
Interactive dashboard for analyzing student performance metrics.
Enhanced version with proper database connectivity, data validation, and advanced analytics.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import redis
import hashlib
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Pydantic models for data validation
class StudentPerformanceData(BaseModel):
    """Data model for student performance records."""
    student_id: str = Field(..., description="Unique student identifier")
    student_name: str = Field(..., description="Full name of the student")
    school_name: str = Field(..., description="Name of the school")
    division: str = Field(..., description="Administrative division")
    district: str = Field(..., description="District name")
    upazila: str = Field(..., description="Upazila/Sub-district name")
    gender: str = Field(..., description="Student gender")
    age_group: str = Field(..., description="Age group category")
    socioeconomic_status: Optional[str] = Field(None, description="Socioeconomic status")
    has_disability: bool = Field(False, description="Disability indicator")
    academic_year: str = Field(..., description="Academic year")
    term: str = Field(..., description="Academic term")
    subject_name: str = Field(..., description="Subject name")
    assessment_type: str = Field(..., description="Type of assessment")
    marks_obtained: float = Field(..., ge=0, description="Marks obtained")
    max_marks: float = Field(..., gt=0, description="Maximum possible marks")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")
    grade_letter: str = Field(..., description="Letter grade")
    is_passed: bool = Field(..., description="Pass/fail indicator")
    assessment_date: datetime = Field(..., description="Date of assessment")
    
    @validator('percentage')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        valid_genders = ['Male', 'Female', 'Other', 'Unknown']
        if v not in valid_genders:
            raise ValueError(f'Gender must be one of {valid_genders}')
        return v

class DashboardFilters(BaseModel):
    """Model for dashboard filters."""
    academic_year: Optional[str] = None
    term: Optional[str] = None
    division: Optional[str] = None
    district: Optional[str] = None
    upazila: Optional[str] = None
    school_name: Optional[str] = None
    subject_name: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    socioeconomic_status: Optional[str] = None
    has_disability: Optional[bool] = None
    min_percentage: float = Field(0, ge=0, le=100)
    max_percentage: float = Field(100, ge=0, le=100)
    assessment_type: Optional[str] = None

# Page configuration
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="📊",
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
    .performance-excellent { color: #28a745; font-weight: bold; }
    .performance-good { color: #17a2b8; font-weight: bold; }
    .performance-average { color: #ffc107; font-weight: bold; }
    .performance-poor { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Initialize Redis connection for caching
def get_redis_client():
    """Get Redis client for caching."""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        return redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        return None

def get_cache_key(data_type: str, filters: Dict) -> str:
    """Generate cache key for data."""
    filter_str = json.dumps(filters, sort_keys=True)
    return f"student_performance:{data_type}:{hashlib.md5(filter_str.encode()).hexdigest()}"

def get_cached_data(cache_key: str, ttl: int = 3600) -> Optional[pd.DataFrame]:
    """Get data from cache."""
    redis_client = get_redis_client()
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return pd.read_json(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
    return None

def set_cached_data(cache_key: str, data: pd.DataFrame, ttl: int = 3600):
    """Set data in cache."""
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.setex(cache_key, ttl, data.to_json())
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_performance_data(filters: Dict) -> pd.DataFrame:
    """Load student performance data from the database with advanced querying."""
    try:
        # Connect to the database
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            st.error("DATABASE_URL environment variable not set")
            return pd.DataFrame()
        
        engine = create_engine(database_url)
        
        # Build dynamic query based on filters
        query = """
        WITH performance_data AS (
            SELECT 
                -- Student information
                s.student_id,
                s.full_name AS student_name,
                s.gender,
                s.age_group,
                s.socioeconomic_status,
                s.has_disability,
                s.division,
                s.district,
                s.upazila,
                
                -- School information
                sch.school_name,
                sch.school_type,
                sch.education_level,
                sch.is_rural,
                
                -- Assessment information
                ar.academic_year,
                ar.term,
                ar.subject_id,
                sub.subject_name,
                ar.assessment_type,
                ar.assessment_category,
                ar.assessment_date,
                ar.marks_obtained,
                ar.max_marks,
                ar.percentage,
                ar.grade_letter,
                ar.is_passed,
                ar.performance_category,
                ar.standardized_grade,
                
                -- Teacher information
                t.full_name AS teacher_name,
                t.subject_specialization,
                t.years_of_experience
                
            FROM facts.fct_assessment_results ar
            JOIN dimensions.dim_students s ON ar.student_id = s.student_id
            JOIN dimensions.dim_schools sch ON ar.school_id = sch.school_id
            LEFT JOIN dimensions.dim_teachers t ON ar.teacher_id = t.teacher_id
            LEFT JOIN (
                SELECT DISTINCT subject_id, subject_name 
                FROM facts.fct_assessment_results 
                WHERE subject_name IS NOT NULL
            ) sub ON ar.subject_id = sub.subject_id
            WHERE s.is_current = TRUE
            AND sch.is_current = TRUE
        """
        
        # Add filter conditions
        conditions = []
        params = {}
        
        if filters.get('academic_year'):
            conditions.append("academic_year = :academic_year")
            params['academic_year'] = filters['academic_year']
        
        if filters.get('term'):
            conditions.append("term = :term")
            params['term'] = filters['term']
        
        if filters.get('division'):
            conditions.append("division = :division")
            params['division'] = filters['division']
        
        if filters.get('district'):
            conditions.append("district = :district")
            params['district'] = filters['district']
        
        if filters.get('upazila'):
            conditions.append("upazila = :upazila")
            params['upazila'] = filters['upazila']
        
        if filters.get('school_name'):
            conditions.append("school_name ILIKE :school_name")
            params['school_name'] = f"%{filters['school_name']}%"
        
        if filters.get('subject_name'):
            conditions.append("subject_name ILIKE :subject_name")
            params['subject_name'] = f"%{filters['subject_name']}%"
        
        if filters.get('gender'):
            conditions.append("gender = :gender")
            params['gender'] = filters['gender']
        
        if filters.get('age_group'):
            conditions.append("age_group = :age_group")
            params['age_group'] = filters['age_group']
        
        if filters.get('socioeconomic_status'):
            conditions.append("socioeconomic_status = :socioeconomic_status")
            params['socioeconomic_status'] = filters['socioeconomic_status']
        
        if filters.get('has_disability') is not None:
            conditions.append("has_disability = :has_disability")
            params['has_disability'] = filters['has_disability']
        
        if filters.get('assessment_type'):
            conditions.append("assessment_type = :assessment_type")
            params['assessment_type'] = filters['assessment_type']
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY assessment_date DESC, student_name"
        
        # Execute query
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        
        # Validate data using Pydantic
        validated_records = []
        for _, row in df.iterrows():
            try:
                validated_record = StudentPerformanceData(**row.to_dict())
                validated_records.append(validated_record.dict())
            except Exception as e:
                logger.warning(f"Data validation failed for record {row.get('student_id')}: {e}")
                continue
        
        if validated_records:
            return pd.DataFrame(validated_records)
        else:
            return pd.DataFrame()
            
    except SQLAlchemyError as e:
        st.error(f"Database error: {str(e)}")
        logger.error(f"Database error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        logger.error(f"Data loading error: {e}")
        return pd.DataFrame()

def setup_sidebar() -> DashboardFilters:
    """Set up the sidebar with comprehensive filters."""
    st.sidebar.title("📊 Dashboard Filters")
    
    # Load filter options from database
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        with engine.connect() as conn:
            # Get academic years
            years_df = pd.read_sql("SELECT DISTINCT academic_year FROM facts.fct_assessment_results ORDER BY academic_year DESC", conn)
            year_options = ["All"] + years_df['academic_year'].tolist()
            
            # Get terms
            terms_df = pd.read_sql("SELECT DISTINCT term FROM facts.fct_assessment_results ORDER BY term", conn)
            term_options = ["All"] + terms_df['term'].tolist()
            
            # Get divisions
            divisions_df = pd.read_sql("SELECT DISTINCT division FROM dimensions.dim_students WHERE is_current = TRUE ORDER BY division", conn)
            division_options = ["All"] + divisions_df['division'].tolist()
            
            # Get subjects
            subjects_df = pd.read_sql("SELECT DISTINCT subject_name FROM facts.fct_assessment_results WHERE subject_name IS NOT NULL ORDER BY subject_name", conn)
            subject_options = ["All"] + subjects_df['subject_name'].tolist()
            
    except Exception as e:
        st.sidebar.error(f"Error loading filter options: {e}")
        year_options = term_options = division_options = subject_options = ["All"]
    
    # Academic filters
    st.sidebar.subheader("📚 Academic Filters")
    selected_year = st.sidebar.selectbox("Academic Year", year_options, index=0)
    selected_term = st.sidebar.selectbox("Term", term_options, index=0)
    selected_subject = st.sidebar.selectbox("Subject", subject_options, index=0)
    selected_assessment_type = st.sidebar.selectbox(
        "Assessment Type", 
        ["All", "Midterm", "Final", "Quiz", "Assignment", "Project"], 
        index=0
    )
    
    # Geographic filters
    st.sidebar.subheader("🗺️ Geographic Filters")
    selected_division = st.sidebar.selectbox("Division", division_options, index=0)
    
    # Performance filters
    st.sidebar.subheader("📈 Performance Filters")
    min_percentage, max_percentage = st.sidebar.slider(
        "Percentage Range",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    
    # Demographic filters
    st.sidebar.subheader("👥 Demographic Filters")
    selected_gender = st.sidebar.selectbox(
        "Gender", 
        ["All", "Male", "Female", "Other"], 
        index=0
    )
    
    selected_age_group = st.sidebar.selectbox(
        "Age Group",
        ["All", "5-9", "10-14", "15-19", "20-24"],
        index=0
    )
    
    selected_socioeconomic = st.sidebar.selectbox(
        "Socioeconomic Status",
        ["All", "Low", "Medium", "High"],
        index=0
    )
    
    has_disability_filter = st.sidebar.selectbox(
        "Disability Status",
        ["All", "Yes", "No"],
        index=0
    )
    
    # Convert filter values
    filters = {
        'academic_year': selected_year if selected_year != "All" else None,
        'term': selected_term if selected_term != "All" else None,
        'subject_name': selected_subject if selected_subject != "All" else None,
        'assessment_type': selected_assessment_type if selected_assessment_type != "All" else None,
        'division': selected_division if selected_division != "All" else None,
        'gender': selected_gender if selected_gender != "All" else None,
        'age_group': selected_age_group if selected_age_group != "All" else None,
        'socioeconomic_status': selected_socioeconomic if selected_socioeconomic != "All" else None,
        'has_disability': None if has_disability_filter == "All" else (has_disability_filter == "Yes"),
        'min_percentage': min_percentage,
        'max_percentage': max_percentage
    }
    
    return DashboardFilters(**filters)

def display_advanced_metrics(df: pd.DataFrame):
    """Display comprehensive performance metrics."""
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Calculate metrics
    total_students = df['student_id'].nunique()
    total_assessments = len(df)
    avg_percentage = df['percentage'].mean()
    pass_rate = (df['is_passed'].sum() / len(df)) * 100
    
    # Performance distribution
    excellent_count = len(df[df['percentage'] >= 80])
    good_count = len(df[(df['percentage'] >= 60) & (df['percentage'] < 80)])
    average_count = len(df[(df['percentage'] >= 40) & (df['percentage'] < 60)])
    poor_count = len(df[df['percentage'] < 40])
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Students", 
            f"{total_students:,}",
            help="Number of unique students in the dataset"
        )
    
    with col2:
        st.metric(
            "Total Assessments", 
            f"{total_assessments:,}",
            help="Total number of assessments"
        )
    
    with col3:
        st.metric(
            "Average Performance", 
            f"{avg_percentage:.1f}%",
            delta=f"{avg_percentage - 50:.1f}% vs 50% baseline",
            delta_color="normal" if avg_percentage >= 50 else "inverse",
            help="Average percentage across all assessments"
        )
    
    with col4:
        st.metric(
            "Pass Rate", 
            f"{pass_rate:.1f}%",
            delta=f"{pass_rate - 75:.1f}% vs 75% target",
            delta_color="normal" if pass_rate >= 75 else "inverse",
            help="Percentage of students who passed their assessments"
        )
    
    # Performance distribution
    st.subheader("📊 Performance Distribution")
    perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
    
    with perf_col1:
        st.metric("Excellent (80%+)", f"{excellent_count:,}", f"{(excellent_count/total_assessments)*100:.1f}%")
    with perf_col2:
        st.metric("Good (60-79%)", f"{good_count:,}", f"{(good_count/total_assessments)*100:.1f}%")
    with perf_col3:
        st.metric("Average (40-59%)", f"{average_count:,}", f"{(average_count/total_assessments)*100:.1f}%")
    with perf_col4:
        st.metric("Poor (<40%)", f"{poor_count:,}", f"{(poor_count/total_assessments)*100:.1f}%")

def create_performance_heatmap(df: pd.DataFrame):
    """Create performance heatmap by region and subject."""
    if df.empty:
        return None
    
    # Aggregate data for heatmap
    heatmap_data = df.groupby(['division', 'subject_name'])['percentage'].mean().reset_index()
    heatmap_pivot = heatmap_data.pivot(index='division', columns='subject_name', values='percentage')
    
    fig = px.imshow(
        heatmap_pivot,
        title="Performance Heatmap by Region and Subject",
        labels=dict(x="Subject", y="Division", color="Average Percentage"),
        color_continuous_scale="RdYlGn",
        aspect="auto"
    )
    
    fig.update_layout(
        xaxis_title="Subject",
        yaxis_title="Division",
        height=500
    )
    
    return fig

def create_time_series_analysis(df: pd.DataFrame):
    """Create time series analysis of performance trends."""
    if df.empty:
        return None
    
    # Convert assessment_date to datetime if needed
    df['assessment_date'] = pd.to_datetime(df['assessment_date'])
    
    # Aggregate by month
    monthly_performance = df.groupby(df['assessment_date'].dt.to_period('M')).agg({
        'percentage': ['mean', 'std', 'count'],
        'is_passed': 'sum'
    }).reset_index()
    
    monthly_performance.columns = ['month', 'avg_percentage', 'std_percentage', 'assessment_count', 'pass_count']
    monthly_performance['month'] = monthly_performance['month'].astype(str)
    monthly_performance['pass_rate'] = (monthly_performance['pass_count'] / monthly_performance['assessment_count']) * 100
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Average Performance Over Time', 'Pass Rate Over Time'),
        vertical_spacing=0.1
    )
    
    # Performance trend
    fig.add_trace(
        go.Scatter(
            x=monthly_performance['month'],
            y=monthly_performance['avg_percentage'],
            mode='lines+markers',
            name='Average Performance',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # Pass rate trend
    fig.add_trace(
        go.Scatter(
            x=monthly_performance['month'],
            y=monthly_performance['pass_rate'],
            mode='lines+markers',
            name='Pass Rate',
            line=dict(color='green', width=2)
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        title_text="Performance Trends Over Time",
        showlegend=True
    )
    
    return fig

def create_comparative_analysis(df: pd.DataFrame):
    """Create comparative analysis dashboards."""
    if df.empty:
        return None
    
    # Create subplots for different comparisons
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Performance by Gender',
            'Performance by Age Group',
            'Performance by School Type',
            'Performance by Socioeconomic Status'
        ),
        specs=[[{"type": "box"}, {"type": "box"}],
               [{"type": "box"}, {"type": "box"}]]
    )
    
    # Gender comparison
    if 'gender' in df.columns:
        for gender in df['gender'].unique():
            gender_data = df[df['gender'] == gender]['percentage']
            fig.add_trace(
                go.Box(y=gender_data, name=gender, boxpoints='outliers'),
                row=1, col=1
            )
    
    # Age group comparison
    if 'age_group' in df.columns:
        for age_group in df['age_group'].unique():
            age_data = df[df['age_group'] == age_group]['percentage']
            fig.add_trace(
                go.Box(y=age_data, name=age_group, boxpoints='outliers'),
                row=1, col=2
            )
    
    # School type comparison (if available)
    if 'school_type' in df.columns:
        for school_type in df['school_type'].unique():
            school_data = df[df['school_type'] == school_type]['percentage']
            fig.add_trace(
                go.Box(y=school_data, name=school_type, boxpoints='outliers'),
                row=2, col=1
            )
    
    # Socioeconomic status comparison
    if 'socioeconomic_status' in df.columns:
        for status in df['socioeconomic_status'].unique():
            if pd.notna(status):
                status_data = df[df['socioeconomic_status'] == status]['percentage']
                fig.add_trace(
                    go.Box(y=status_data, name=status, boxpoints='outliers'),
                    row=2, col=2
                )
    
    fig.update_layout(
        height=800,
        title_text="Comparative Performance Analysis",
        showlegend=False
    )
    
    return fig

def display_advanced_visualizations(df: pd.DataFrame):
    """Display advanced data visualizations."""
    if df.empty:
        st.warning("No data available for visualizations.")
        return
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Performance Distribution", 
        "🗺️ Regional Heatmap", 
        "📈 Trend Analysis",
        "🔍 Comparative Analysis"
    ])
    
    with tab1:
        # Performance distribution
        col1, col2 = st.columns(2)
        
        with col1:
            # Histogram
            fig_hist = px.histogram(
                df, 
                x='percentage', 
                nbins=20,
                title='Performance Distribution',
                labels={'percentage': 'Percentage Score'},
                color_discrete_sequence=['#1f77b4']
            )
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Box plot by subject
            if 'subject_name' in df.columns:
                fig_box = px.box(
                    df, 
                    x='subject_name', 
                    y='percentage',
                    title='Performance by Subject',
                    labels={'subject_name': 'Subject', 'percentage': 'Percentage Score'}
                )
                fig_box.update_xaxes(tickangle=45)
                st.plotly_chart(fig_box, use_container_width=True)
    
    with tab2:
        # Regional heatmap
        heatmap_fig = create_performance_heatmap(df)
        if heatmap_fig:
            st.plotly_chart(heatmap_fig, use_container_width=True)
        else:
            st.info("Insufficient data for heatmap visualization.")
    
    with tab3:
        # Time series analysis
        time_series_fig = create_time_series_analysis(df)
        if time_series_fig:
            st.plotly_chart(time_series_fig, use_container_width=True)
        else:
            st.info("Insufficient data for time series analysis.")
    
    with tab4:
        # Comparative analysis
        comparative_fig = create_comparative_analysis(df)
        if comparative_fig:
            st.plotly_chart(comparative_fig, use_container_width=True)
        else:
            st.info("Insufficient data for comparative analysis.")

def export_data(df: pd.DataFrame, format_type: str = "csv"):
    """Export data in various formats."""
    if df.empty:
        st.warning("No data to export.")
        return
    
    if format_type == "csv":
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"student_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    elif format_type == "excel":
        # Note: This would require openpyxl package
        st.info("Excel export requires additional dependencies. Please install openpyxl.")

def display_data_table(df: pd.DataFrame):
    """Display the filtered data in an interactive table."""
    if df.empty:
        st.info("No data available for the selected filters.")
        return
    
    st.subheader("📋 Detailed Performance Data")
    
    # Add export functionality
    col1, col2 = st.columns([3, 1])
    with col2:
        export_format = st.selectbox("Export Format", ["CSV", "Excel"])
        if st.button("📥 Export Data"):
            export_data(df, export_format.lower())
    
    # Display interactive table
    st.dataframe(
        df.sort_values(['percentage', 'student_name'], ascending=[False, True]),
        column_config={
            'student_id': 'Student ID',
            'student_name': 'Name',
            'school_name': 'School',
            'division': 'Division',
            'district': 'District',
            'upazila': 'Upazila',
            'gender': 'Gender',
            'age_group': 'Age Group',
            'socioeconomic_status': 'SES',
            'has_disability': 'Disability',
            'academic_year': 'Year',
            'term': 'Term',
            'subject_name': 'Subject',
            'assessment_type': 'Type',
            'percentage': st.column_config.NumberColumn(
                'Percentage',
                format="%.1f%%",
                help="Student's percentage score"
            ),
            'grade_letter': 'Grade',
            'is_passed': 'Passed',
            'assessment_date': 'Date'
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

def main():
    """Main function to run the enhanced dashboard."""
    st.title("📊 Student Performance Dashboard")
    st.markdown("Comprehensive analytics for Bangladesh education system performance tracking")
    
    # Load data with caching
    filters = setup_sidebar()
    
    # Generate cache key
    cache_key = get_cache_key("performance_data", filters.dict())
    
    # Try to get cached data first
    df = get_cached_data(cache_key)
    
    if df is None:
        # Load fresh data
        with st.spinner("Loading performance data..."):
            df = load_performance_data(filters.dict())
        
        # Cache the data
        if not df.empty:
            set_cached_data(cache_key, df)
    
    if df.empty:
        st.warning("No data available for the selected filters. Please adjust your filter criteria.")
        return
    
    # Apply percentage range filter
    df = df[(df['percentage'] >= filters.min_percentage) & (df['percentage'] <= filters.max_percentage)]
    
    # Display metrics
    display_advanced_metrics(df)
    
    # Display visualizations
    display_advanced_visualizations(df)
    
    # Display data table
    display_data_table(df)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Data Source**: Bangladesh Education Data Warehouse | "
        "**Last Updated**: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == "__main__":
    main()
