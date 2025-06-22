{{
  config(
    materialized = 'incremental',
    unique_key = 'teacher_key',
    tags = ['dimensions'],
    incremental_strategy = 'merge',
    merge_exclude_columns = ['dwh_created_at']
  )
}}

WITH source AS (
  -- Get only new or updated records since last run
  SELECT 
    teacher_id,
    full_name,
    gender,
    date_of_birth,
    qualification,
    subject_specialization,
    join_date,
    email,
    phone_number,
    nid_number,
    present_address,
    permanent_address,
    is_active,
    created_at,
    updated_at
  FROM {{ ref('stg_teachers') }}
  {% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(dwh_updated_at) FROM {{ this }})
  {% endif %}
),

-- Get the most recent record for each teacher
current_records AS (
  SELECT 
    teacher_id,
    MAX(updated_at) AS latest_update
  FROM source
  GROUP BY teacher_id
),

-- Join to get complete current records
current_data AS (
  SELECT 
    s.*
  FROM source s
  INNER JOIN current_records cr 
    ON s.teacher_id = cr.teacher_id 
    AND s.updated_at = cr.latest_update
),

-- Get the existing dimension data
existing_dimension AS (
  SELECT 
    teacher_key,
    teacher_id,
    full_name,
    gender,
    date_of_birth,
    qualification,
    subject_specialization,
    join_date,
    is_active,
    is_current,
    effective_from,
    effective_to,
    dwh_updated_at
  FROM {{ this }}
  WHERE is_current = TRUE
),

-- Identify new or changed records
changed_records AS (
  SELECT 
    cd.*,
    -- Check if this is a new record or has changes
    CASE 
      WHEN ed.teacher_key IS NULL THEN TRUE  -- New record
      WHEN cd.full_name != ed.full_name OR
           cd.gender != ed.gender OR
           cd.date_of_birth != ed.date_of_birth OR
           cd.qualification != ed.qualification OR
           cd.subject_specialization != ed.subject_specialization OR
           cd.is_active != ed.is_active THEN TRUE
      ELSE FALSE
    END AS has_changes
  FROM current_data cd
  LEFT JOIN existing_dimension ed ON cd.teacher_id = ed.teacher_id
  WHERE ed.teacher_key IS NULL OR has_changes = TRUE
),

-- Generate surrogate keys and set effective dates
dim_teachers AS (
  SELECT
    -- Generate a UUID for the surrogate key
    {{ dbt_utils.generate_surrogate_key(['teacher_id', 'updated_at']) }} AS teacher_key,
    teacher_id,
    
    -- Teacher information
    full_name,
    -- Extract first name (first part of full name)
    REGEXP_EXTRACT(full_name, r'^([^ ]+)') AS first_name,
    -- Extract last name (everything after first space)
    CASE 
      WHEN STRPOS(full_name, ' ') > 0 
      THEN SUBSTR(full_name, STRPOS(full_name, ' ') + 1)
      ELSE NULL
    END AS last_name,
    
    -- Standardize gender values
    CASE 
      WHEN LOWER(gender) IN ('m', 'male', 'mâle', 'männlich', 'man', 'homme') THEN 'Male'
      WHEN LOWER(gender) IN ('f', 'female', 'femme', 'weiblich', 'woman', 'frau') THEN 'Female'
      WHEN LOWER(gender) IN ('o', 'other', 'autre', 'andere', 'non-binary', 'nonbinary') THEN 'Other'
      WHEN gender IS NULL OR TRIM(gender) = '' THEN 'Unknown'
      ELSE 'Other'
    END AS gender,
    
    date_of_birth,
    
    -- Calculate age
    DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) - 
      CASE 
        WHEN EXTRACT(MONTH FROM date_of_birth) > EXTRACT(MONTH FROM CURRENT_DATE())
          OR (EXTRACT(MONTH FROM date_of_birth) = EXTRACT(MONTH FROM CURRENT_DATE())
              AND EXTRACT(DAY FROM date_of_birth) > EXTRACT(DAY FROM CURRENT_DATE()))
        THEN 1 
        ELSE 0 
      END AS age,
    
    -- Professional information
    qualification,
    subject_specialization,
    join_date,
    
    -- Calculate years of experience
    DATE_DIFF(CURRENT_DATE(), join_date, YEAR) AS years_of_experience,
    
    -- Categorize experience level
    CASE
      WHEN DATE_DIFF(CURRENT_DATE(), join_date, YEAR) < 2 THEN 'Novice'
      WHEN DATE_DIFF(CURRENT_DATE(), join_date, YEAR) BETWEEN 2 AND 5 THEN 'Experienced'
      WHEN DATE_DIFF(CURRENT_DATE(), join_date, YEAR) > 5 THEN 'Veteran'
      ELSE 'Unknown'
    END AS experience_level,
    
    is_active,
    
    -- Contact information
    email,
    phone_number,
    nid_number,
    present_address,
    permanent_address,
    
    -- SCD Type 2 fields
    TRUE AS is_current,
    CURRENT_TIMESTAMP() AS effective_from,
    TIMESTAMP('9999-12-31 23:59:59') AS effective_to,
    
    -- Audit fields
    CURRENT_TIMESTAMP() AS dwh_created_at,
    CURRENT_TIMESTAMP() AS dwh_updated_at,
    '{{ this }}' AS record_source
    
  FROM changed_records
)

-- Update existing records to set is_current = FALSE and effective_to
-- This is handled by the merge strategy in dbt

-- Return the new or updated records
SELECT * FROM dim_teachers
