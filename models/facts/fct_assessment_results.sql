{{
  config(
    materialized = 'incremental',
    schema = 'facts',
    unique_key = 'assessment_result_key',
    tags = ['facts'],
    partition_by = {
      'field': 'assessment_date',
      'data_type': 'date',
      'granularity': 'month'
    },
    cluster_by = ['school_id', 'student_id', 'academic_year', 'term', 'subject_id'],
    partition_expiration_days = 365 * 5,  -- Keep 5 years of assessment data
    require_partition_filter = true,  -- Enforce partition pruning for queries
    incremental_strategy = 'insert_overwrite'  -- Better for partition management
  )
}}

WITH 
-- Get the latest assessment results from staging
assessment_results AS (
  SELECT 
    assessment_result_id,
    student_id,
    teacher_id,
    school_id,
    assessment_id,
    assessment_date,
    academic_year,
    term,
    subject_id,
    grade,
    section,
    marks_obtained,
    max_marks,
    percentage,
    grade_letter,
    is_passed,
    remarks,
    recorded_at,
    recorded_by,
    assessment_type,
    assessment_category,
    is_makeup_exam,
    -- Add row number to handle potential duplicates
    ROW_NUMBER() OVER (
      PARTITION BY assessment_result_id 
      ORDER BY recorded_at DESC
    ) as rn
  FROM {{ ref('stg_assessment_results') }}  -- Reference staging model instead of raw source
  WHERE assessment_date IS NOT NULL  -- Ensure we have a valid date
  {% if is_incremental() %}
    -- For incremental loads, only process new or updated records
    -- Process data from the beginning of the current academic year to catch any backdated records
    AND recorded_at >= (
      SELECT 
        TIMESTAMP_SUB(
          TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), YEAR)), 
          INTERVAL 1 YEAR
        )
    )
  {% endif %}
),

-- Get student information for enrichment
student_info AS (
  SELECT
    student_id,
    full_name AS student_name,
    gender AS student_gender,
    age_group AS student_age_group,
    socioeconomic_status,
    has_disability,
    is_current
  FROM {{ ref('dim_students') }}
  WHERE is_current = TRUE
),

-- Get teacher information for enrichment
teacher_info AS (
  SELECT
    teacher_id,
    full_name AS teacher_name,
    subject_specialization,
    years_of_experience,
    is_current
  FROM {{ ref('dim_teachers') }}
  WHERE is_current = TRUE
),

-- Get school information for enrichment
school_info AS (
  SELECT
    school_id,
    school_name,
    school_type,
    education_level,
    is_rural,
    is_current
  FROM {{ ref('dim_schools') }}
  WHERE is_current = TRUE
),

-- Join all data together and calculate metrics
enriched_results AS (
  SELECT
    -- Surrogate key (deterministic for idempotent loads)
    {{ dbt_utils.generate_surrogate_key([
      'ar.assessment_result_id', 
      'ar.recorded_at'
    ]) }} AS assessment_result_key,
    
    -- Business keys
    ar.assessment_result_id,
    ar.student_id,
    ar.teacher_id,
    ar.school_id,
    ar.assessment_id,
    
    -- Date and time dimensions
    DATE(ar.assessment_date) AS assessment_date,
    DATE_TRUNC(ar.assessment_date, MONTH) AS assessment_month,
    DATE_TRUNC(ar.assessment_date, QUARTER) AS assessment_quarter,
    DATE_TRUNC(ar.assessment_date, YEAR) AS assessment_year,
    ar.recorded_at,
    
    -- Academic context
    ar.academic_year,
    ar.term,
    ar.subject_id,
    sub.subject_name,
    ar.grade,
    ar.section,
    ar.assessment_type,
    ar.assessment_category,
    ar.is_makeup_exam,
    
    -- Student information
    si.student_name,
    si.student_gender,
    si.student_age_group,
    si.socioeconomic_status,
    si.has_disability,
    
    -- Teacher information
    ti.teacher_name,
    ti.subject_specialization,
    ti.years_of_experience,
    
    -- School information
    sch.school_name,
    sch.school_type,
    sch.education_level,
    sch.is_rural,
    
    -- Assessment metrics
    ar.marks_obtained,
    ar.max_marks,
    ar.percentage,
    ar.grade_letter,
    ar.is_passed,
    ar.remarks,
    
    -- Derived metrics
    CASE 
      WHEN ar.percentage >= 80 THEN 'A+'
      WHEN ar.percentage >= 70 THEN 'A'
      WHEN ar.percentage >= 60 THEN 'A-'
      WHEN ar.percentage >= 50 THEN 'B'
      WHEN ar.percentage >= 40 THEN 'C'
      WHEN ar.percentage >= 33 THEN 'D'
      ELSE 'F'
    END AS standardized_grade,
    
    -- Performance indicators
    SAFE_DIVIDE(ar.marks_obtained, NULLIF(ar.max_marks, 0)) * 100 AS calculated_percentage,
    
    CASE 
      WHEN ar.percentage >= 80 THEN 'Excellent (80-100%)'
      WHEN ar.percentage >= 70 THEN 'Very Good (70-79%)'
      WHEN ar.percentage >= 60 THEN 'Good (60-69%)'
      WHEN ar.percentage >= 50 THEN 'Satisfactory (50-59%)'
      WHEN ar.percentage >= 40 THEN 'Adequate (40-49%)'
      WHEN ar.percentage >= 33 THEN 'Marginal (33-39%)'
      ELSE 'Fail (Below 33%)'
    END AS performance_category,
    
    -- Performance indicators for analysis
    CASE WHEN ar.percentage >= 33 THEN 1 ELSE 0 END AS is_passed_indicator,
    CASE WHEN ar.percentage >= 60 THEN 1 ELSE 0 END AS is_good_performance,
    
    -- Normalized scores (0-1 scale)
    SAFE_DIVIDE(ar.marks_obtained, NULLIF(ar.max_marks, 1)) AS normalized_score,
    
    -- Metadata
    ar.recorded_by,
    
    -- Audit fields
    CURRENT_TIMESTAMP() AS dwh_created_at,
    CURRENT_TIMESTAMP() AS dwh_updated_at,
    
    -- Record source
    '{{ this }}' AS record_source
    
  FROM assessment_results ar
  LEFT JOIN student_info si ON ar.student_id = si.student_id
  LEFT JOIN teacher_info ti ON ar.teacher_id = ti.teacher_id
  LEFT JOIN school_info sch ON ar.school_id = sch.school_id
  LEFT JOIN {{ ref('dim_subjects') }} sub ON ar.subject_id = sub.subject_id
  WHERE ar.rn = 1  -- Only take the most recent record per assessment_result_id
)

-- Final SELECT with explicit column ordering
SELECT
  assessment_result_key,
  assessment_result_id,
  student_id,
  student_name,
  student_gender,
  student_age_group,
  socioeconomic_status,
  has_disability,
  teacher_id,
  teacher_name,
  subject_specialization,
  years_of_experience,
  school_id,
  school_name,
  school_type,
  education_level,
  is_rural,
  assessment_id,
  assessment_date,
  assessment_month,
  assessment_quarter,
  assessment_year,
  recorded_at,
  academic_year,
  term,
  subject_id,
  subject_name,
  grade,
  section,
  assessment_type,
  assessment_category,
  is_makeup_exam,
  marks_obtained,
  max_marks,
  percentage,
  grade_letter,
  is_passed,
  is_passed_indicator,
  is_good_performance,
  remarks,
  standardized_grade,
  calculated_percentage,
  performance_category,
  normalized_score,
  recorded_by,
  dwh_created_at,
  dwh_updated_at,
  record_source
FROM enriched_results
-- Only include records that are not already in the target table
{% if is_incremental() %}
  WHERE assessment_result_id NOT IN (
    SELECT assessment_result_id 
    FROM {{ this }}
    WHERE assessment_date >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), YEAR)
  )
{% endif %}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY assessment_result_id 
  ORDER BY recorded_at DESC
) = 1
ORDER BY assessment_date, school_id, student_id, subject_id
