"""
Data Service for Student Performance Dashboard
Handles database connectivity, caching, and data validation.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import redis
from pydantic import BaseModel, Field, validator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class DataService:
    """Service class for handling data operations."""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.redis_client = self._get_redis_client()
        self.engine = None
        if self.database_url:
            self.engine = create_engine(self.database_url)
    
    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client for caching."""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def get_cache_key(self, data_type: str, filters: Dict) -> str:
        """Generate cache key for data."""
        filter_str = json.dumps(filters, sort_keys=True)
        return f"student_performance:{data_type}:{hashlib.md5(filter_str.encode()).hexdigest()}"
    
    def get_cached_data(self, cache_key: str, ttl: int = 3600) -> Optional[pd.DataFrame]:
        """Get data from cache."""
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return pd.read_json(cached_data)
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    def set_cached_data(self, cache_key: str, data: pd.DataFrame, ttl: int = 3600):
        """Set data in cache."""
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl, data.to_json())
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
    
    def load_performance_data(self, filters: Dict) -> pd.DataFrame:
        """Load student performance data from the database."""
        try:
            if not self.engine:
                logger.error("Database engine not initialized")
                return pd.DataFrame()
            
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
            with self.engine.connect() as conn:
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
            logger.error(f"Database error: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Data loading error: {e}")
            return pd.DataFrame()
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get filter options from database."""
        try:
            if not self.engine:
                return {}
            
            with self.engine.connect() as conn:
                # Get academic years
                years_df = pd.read_sql(
                    "SELECT DISTINCT academic_year FROM facts.fct_assessment_results ORDER BY academic_year DESC", 
                    conn
                )
                
                # Get terms
                terms_df = pd.read_sql(
                    "SELECT DISTINCT term FROM facts.fct_assessment_results ORDER BY term", 
                    conn
                )
                
                # Get divisions
                divisions_df = pd.read_sql(
                    "SELECT DISTINCT division FROM dimensions.dim_students WHERE is_current = TRUE ORDER BY division", 
                    conn
                )
                
                # Get subjects
                subjects_df = pd.read_sql(
                    "SELECT DISTINCT subject_name FROM facts.fct_assessment_results WHERE subject_name IS NOT NULL ORDER BY subject_name", 
                    conn
                )
                
                return {
                    'academic_years': years_df['academic_year'].tolist(),
                    'terms': terms_df['term'].tolist(),
                    'divisions': divisions_df['division'].tolist(),
                    'subjects': subjects_df['subject_name'].tolist()
                }
                
        except Exception as e:
            logger.error(f"Error loading filter options: {e}")
            return {} 