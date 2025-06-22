{{
  config(
    materialized = 'incremental',
    schema = 'facts',
    unique_key = 'attendance_key',
    tags = ['facts'],
    partition_by = {
      'field': 'attendance_date',
      'data_type': 'date',
      'granularity': 'month'
    },
    cluster_by = ['school_id', 'student_id', 'grade', 'section'],
    partition_expiration_days = 365 * 3,  -- Keep 3 years of data
    require_partition_filter = true,  -- Enforce partition pruning for queries
    incremental_strategy = 'insert_overwrite'  -- Better for partition management
  )
}}

WITH 
-- Get the latest attendance records
attendance_source AS (
  SELECT 
    attendance_id,
    student_id,
    school_id,
    attendance_date,
    is_present,
    reason_for_absence,
    recorded_by,
    recorded_at,
    academic_year,
    term,
    grade,
    section,
    subject_id,
    is_excused,
    -- Add any other relevant fields from source
    ROW_NUMBER() OVER (
      PARTITION BY attendance_id 
      ORDER BY recorded_at DESC
    ) as rn
  FROM {{ ref('stg_attendances') }}  -- Reference staging model instead of raw source
  WHERE attendance_date IS NOT NULL  -- Ensure we have a valid date
  {% if is_incremental() %}
    -- For incremental loads, only process new or updated records
    -- Process data from the beginning of the current month to catch any backdated records
    AND recorded_at >= (
      SELECT 
        TIMESTAMP_SUB(
          TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), MONTH)), 
          INTERVAL 1 MONTH
        )
    )
  {% endif %}
),

-- Get student and school information for enrichment
student_info AS (
  SELECT
    student_id,
    full_name AS student_name,
    gender AS student_gender,
    age_group AS student_age_group,
    socioeconomic_status,
    has_disability
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
    is_rural
  FROM {{ ref('dim_schools') }}
  WHERE is_current = TRUE
),

-- Join all data together
enriched_attendance AS (
  SELECT
    -- Surrogate key (deterministic for idempotent loads)
    {{ dbt_utils.generate_surrogate_key([
      'a.attendance_id', 
      'a.recorded_at'
    ]) }} AS attendance_key,
    
    -- Business keys
    a.attendance_id,
    a.student_id,
    a.school_id,
    a.subject_id,
    
    -- Date and time dimensions
    DATE(a.attendance_date) AS attendance_date,
    DATE_TRUNC(a.attendance_date, MONTH) AS attendance_month,
    DATE_TRUNC(a.attendance_date, QUARTER) AS attendance_quarter,
    DATE_TRUNC(a.attendance_date, YEAR) AS attendance_year,
    
    -- Academic context
    a.academic_year,
    a.term,
    a.grade,
    a.section,
    
    -- Student information
    si.student_name,
    si.student_gender,
    si.student_age_group,
    si.socioeconomic_status,
    si.has_disability,
    
    -- School information
    sch.school_name,
    sch.school_type,
    sch.education_level,
    sch.is_rural,
    
    -- Attendance facts
    a.is_present,
    a.is_excused,
    a.reason_for_absence,
    
    -- Derived metrics (for easier analysis and aggregation)
    CASE WHEN a.is_present THEN 1 ELSE 0 END AS present_count,
    CASE WHEN NOT a.is_present AND a.is_excused THEN 1 ELSE 0 END AS excused_absence_count,
    CASE WHEN NOT a.is_present AND NOT a.is_excused THEN 1 ELSE 0 END AS unexcused_absence_count,
    
    -- Categorize absences
    CASE 
      WHEN a.is_present THEN 'Present'
      WHEN NOT a.is_present AND a.is_excused THEN 'Absent (Excused)'
      WHEN NOT a.is_present AND NOT a.is_excused THEN 'Absent (Unexcused)'
      ELSE 'Unknown'
    END AS attendance_status,
    
    -- Metadata
    a.recorded_by,
    a.recorded_at,
    
    -- Audit fields
    CURRENT_TIMESTAMP() AS dwh_created_at,
    CURRENT_TIMESTAMP() AS dwh_updated_at,
    
    -- Record source
    '{{ this }}' AS record_source
    
  FROM attendance_source a
  LEFT JOIN student_info si ON a.student_id = si.student_id
  LEFT JOIN school_info sch ON a.school_id = sch.school_id
  WHERE a.rn = 1  -- Only take the most recent record per attendance_id
)

-- Final SELECT with explicit column ordering
SELECT
  attendance_key,
  attendance_id,
  student_id,
  school_id,
  subject_id,
  attendance_date,
  attendance_month,
  attendance_quarter,
  attendance_year,
  academic_year,
  term,
  grade,
  section,
  student_name,
  student_gender,
  student_age_group,
  socioeconomic_status,
  has_disability,
  school_name,
  school_type,
  education_level,
  is_rural,
  is_present,
  is_excused,
  reason_for_absence,
  present_count,
  excused_absence_count,
  unexcused_absence_count,
  attendance_status,
  recorded_by,
  recorded_at,
  dwh_created_at,
  dwh_updated_at,
  record_source
FROM enriched_attendance
-- Only include records that are not already in the target table
{% if is_incremental() %}
  WHERE attendance_id NOT IN (
    SELECT attendance_id 
    FROM {{ this }}
    WHERE attendance_date >= DATE_TRUNC(CURRENT_DATE(), MONTH)
  )
{% endif %}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY attendance_id 
  ORDER BY recorded_at DESC
) = 1
ORDER BY attendance_date, school_id, student_id
