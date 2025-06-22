{{
  config(
    materialized = 'incremental',
    schema = 'facts',
    unique_key = 'enrollment_key',
    tags = ['facts'],
    partition_by = {
      'field': 'enrollment_date',
      'data_type': 'date',
      'granularity': 'month'
    },
    cluster_by = ['school_id', 'student_id', 'academic_year', 'grade'],
    partition_expiration_days = 365 * 5,  -- Keep 5 years of enrollment data
    require_partition_filter = true,  -- Enforce partition pruning for queries
    incremental_strategy = 'insert_overwrite'  -- Better for partition management
  )
}}

WITH 
-- Get the latest enrollment records
enrollment_source AS (
  SELECT 
    enrollment_id,
    student_id,
    school_id,
    enrollment_year,
    grade,
    section,
    status,
    dropout_reason,
    transfer_school_id,
    created_at,
    updated_at,
    -- Add row number to handle potential duplicates
    ROW_NUMBER() OVER (
      PARTITION BY enrollment_id 
      ORDER BY updated_at DESC, created_at DESC
    ) as rn
  FROM {{ source('raw', 'enrollments') }}
  WHERE enrollment_year IS NOT NULL  -- Ensure we have a valid academic year
  {% if is_incremental() %}
    -- For incremental loads, only process new or updated records
    -- Process data from the beginning of the current academic year to catch any backdated records
    AND (
      updated_at >= (
        SELECT 
          TIMESTAMP_SUB(
            TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), YEAR)), 
            INTERVAL 1 YEAR
          )
      )
      OR created_at >= (
        SELECT 
          TIMESTAMP_SUB(
            TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), YEAR)), 
            INTERVAL 1 YEAR
          )
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
    date_of_birth,
    age_group,
    socioeconomic_status,
    has_disability,
    division,
    district,
    upazila,
    is_current
  FROM {{ ref('dim_students') }}
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
    division AS school_division,
    district AS school_district,
    upazila AS school_upazila,
    is_current
  FROM {{ ref('dim_schools') }}
  WHERE is_current = TRUE
),

-- Get transfer school information for enrichment
transfer_school_info AS (
  SELECT
    school_id,
    school_name AS transfer_school_name,
    school_type AS transfer_school_type,
    is_rural AS is_transfer_school_rural
  FROM {{ ref('dim_schools') }}
  WHERE is_current = TRUE
),

-- Join all data together
enriched_enrollments AS (
  SELECT
    -- Surrogate key (deterministic for idempotent loads)
    {{ dbt_utils.generate_surrogate_key([
      'e.enrollment_id', 
      'e.updated_at'
    ]) }} AS enrollment_key,
    
    -- Business keys
    e.enrollment_id,
    e.student_id,
    e.school_id,
    
    -- Date and time dimensions
    DATE(e.created_at) AS enrollment_date,
    DATE_TRUNC(e.created_at, MONTH) AS enrollment_month,
    DATE_TRUNC(e.created_at, QUARTER) AS enrollment_quarter,
    DATE_TRUNC(e.created_at, YEAR) AS enrollment_year,
    
    -- Academic context
    e.enrollment_year AS academic_year,
    e.grade,
    e.section,
    
    -- Student information
    si.student_name,
    si.student_gender,
    si.date_of_birth,
    si.age_group,
    si.socioeconomic_status,
    si.has_disability,
    si.division AS student_division,
    si.district AS student_district,
    si.upazila AS student_upazila,
    
    -- School information
    sch.school_name,
    sch.school_type,
    sch.education_level,
    sch.is_rural,
    sch.school_division,
    sch.school_district,
    sch.school_upazila,
    
    -- Enrollment facts
    e.status AS enrollment_status,
    e.dropout_reason,
    
    -- Transfer information (if applicable)
    e.transfer_school_id,
    ts.transfer_school_name,
    ts.transfer_school_type,
    ts.is_transfer_school_rural,
    
    -- Derived metrics
    CASE 
      WHEN e.status = 'active' THEN 1 
      ELSE 0 
    END AS is_currently_enrolled,
    
    CASE 
      WHEN e.status = 'transferred' THEN 1 
      ELSE 0 
    END AS is_transferred,
    
    CASE 
      WHEN e.status = 'dropped_out' THEN 1 
      ELSE 0 
    END AS is_dropped_out,
    
    -- Duration metrics (in days)
    DATE_DIFF(
      CURRENT_DATE(), 
      DATE(e.created_at), 
      DAY
    ) AS days_since_enrollment,
    
    -- Metadata
    e.created_at,
    e.updated_at,
    
    -- Audit fields
    CURRENT_TIMESTAMP() AS dwh_created_at,
    CURRENT_TIMESTAMP() AS dwh_updated_at,
    
    -- Record source
    '{{ this }}' AS record_source
    
  FROM enrollment_source e
  LEFT JOIN student_info si ON e.student_id = si.student_id
  LEFT JOIN school_info sch ON e.school_id = sch.school_id
  LEFT JOIN transfer_school_info ts ON e.transfer_school_id = ts.school_id
  WHERE e.rn = 1  -- Only take the most recent record per enrollment_id
)

-- Final SELECT with explicit column ordering
SELECT
  enrollment_key,
  enrollment_id,
  student_id,
  student_name,
  student_gender,
  date_of_birth,
  age_group,
  socioeconomic_status,
  has_disability,
  student_division,
  student_district,
  student_upazila,
  school_id,
  school_name,
  school_type,
  education_level,
  is_rural,
  school_division,
  school_district,
  school_upazila,
  enrollment_date,
  enrollment_month,
  enrollment_quarter,
  enrollment_year,
  academic_year,
  grade,
  section,
  enrollment_status,
  dropout_reason,
  transfer_school_id,
  transfer_school_name,
  transfer_school_type,
  is_transfer_school_rural,
  is_currently_enrolled,
  is_transferred,
  is_dropped_out,
  days_since_enrollment,
  created_at,
  updated_at,
  dwh_created_at,
  dwh_updated_at,
  record_source
FROM enriched_enrollments
-- Only include records that are not already in the target table
{% if is_incremental() %}
  WHERE enrollment_id NOT IN (
    SELECT enrollment_id 
    FROM {{ this }}
    WHERE enrollment_date >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), YEAR)
  )
{% endif %}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY enrollment_id 
  ORDER BY updated_at DESC, created_at DESC
) = 1
ORDER BY enrollment_date, school_id, student_id
