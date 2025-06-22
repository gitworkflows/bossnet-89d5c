"""
Visualization Service for Student Performance Dashboard
Handles all chart creation and analytics visualizations.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class VisualizationService:
    """Service class for creating visualizations."""
    
    @staticmethod
    def create_performance_heatmap(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create performance heatmap by region and subject."""
        if df.empty:
            return None
        
        try:
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
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return None
    
    @staticmethod
    def create_time_series_analysis(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create time series analysis of performance trends."""
        if df.empty:
            return None
        
        try:
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
        except Exception as e:
            logger.error(f"Error creating time series: {e}")
            return None
    
    @staticmethod
    def create_comparative_analysis(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create comparative analysis dashboards."""
        if df.empty:
            return None
        
        try:
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
                    if pd.notna(gender):
                        gender_data = df[df['gender'] == gender]['percentage']
                        fig.add_trace(
                            go.Box(y=gender_data, name=gender, boxpoints='outliers'),
                            row=1, col=1
                        )
            
            # Age group comparison
            if 'age_group' in df.columns:
                for age_group in df['age_group'].unique():
                    if pd.notna(age_group):
                        age_data = df[df['age_group'] == age_group]['percentage']
                        fig.add_trace(
                            go.Box(y=age_data, name=age_group, boxpoints='outliers'),
                            row=1, col=2
                        )
            
            # School type comparison (if available)
            if 'school_type' in df.columns:
                for school_type in df['school_type'].unique():
                    if pd.notna(school_type):
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
        except Exception as e:
            logger.error(f"Error creating comparative analysis: {e}")
            return None
    
    @staticmethod
    def create_performance_distribution(df: pd.DataFrame) -> Dict[str, go.Figure]:
        """Create performance distribution charts."""
        charts = {}
        
        try:
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
            charts['histogram'] = fig_hist
            
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
                charts['subject_box'] = fig_box
            
            # Performance by region
            if 'division' in df.columns:
                fig_region = px.box(
                    df,
                    x='division',
                    y='percentage',
                    title='Performance by Division',
                    labels={'division': 'Division', 'percentage': 'Percentage Score'}
                )
                fig_region.update_xaxes(tickangle=45)
                charts['region_box'] = fig_region
            
            return charts
        except Exception as e:
            logger.error(f"Error creating distribution charts: {e}")
            return {}
    
    @staticmethod
    def create_equity_analysis(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create equity analysis visualization."""
        if df.empty:
            return None
        
        try:
            # Calculate equity metrics
            equity_data = []
            
            # Gender equity
            if 'gender' in df.columns:
                gender_equity = df.groupby('gender')['percentage'].agg(['mean', 'count']).reset_index()
                gender_equity['metric'] = 'Gender'
                equity_data.append(gender_equity)
            
            # Socioeconomic equity
            if 'socioeconomic_status' in df.columns:
                ses_equity = df.groupby('socioeconomic_status')['percentage'].agg(['mean', 'count']).reset_index()
                ses_equity['metric'] = 'Socioeconomic Status'
                equity_data.append(ses_equity)
            
            # Rural/Urban equity
            if 'is_rural' in df.columns:
                rural_equity = df.groupby('is_rural')['percentage'].agg(['mean', 'count']).reset_index()
                rural_equity['metric'] = 'Rural/Urban'
                equity_data.append(rural_equity)
            
            if not equity_data:
                return None
            
            # Combine all equity data
            combined_equity = pd.concat(equity_data, ignore_index=True)
            
            # Create visualization
            fig = px.bar(
                combined_equity,
                x='metric',
                y='mean',
                color='gender' if 'gender' in combined_equity.columns else 'socioeconomic_status',
                title='Equity Analysis: Average Performance by Demographics',
                labels={'mean': 'Average Percentage', 'metric': 'Demographic Factor'},
                barmode='group'
            )
            
            fig.update_layout(
                height=500,
                xaxis_title="Demographic Factor",
                yaxis_title="Average Percentage"
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating equity analysis: {e}")
            return None
    
    @staticmethod
    def create_performance_trends(df: pd.DataFrame) -> Optional[go.Figure]:
        """Create performance trends over time."""
        if df.empty:
            return None
        
        try:
            # Convert assessment_date to datetime
            df['assessment_date'] = pd.to_datetime(df['assessment_date'])
            
            # Aggregate by month and subject
            monthly_subject = df.groupby([
                df['assessment_date'].dt.to_period('M'),
                'subject_name'
            ])['percentage'].mean().reset_index()
            
            monthly_subject['assessment_date'] = monthly_subject['assessment_date'].astype(str)
            
            # Create line chart
            fig = px.line(
                monthly_subject,
                x='assessment_date',
                y='percentage',
                color='subject_name',
                title='Performance Trends by Subject Over Time',
                labels={'assessment_date': 'Month', 'percentage': 'Average Percentage', 'subject_name': 'Subject'}
            )
            
            fig.update_layout(
                height=500,
                xaxis_title="Month",
                yaxis_title="Average Percentage"
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating performance trends: {e}")
            return None 