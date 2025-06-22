{{ config(
    materialized='table',
    schema='dimensions',
    unique_key='student_key',
    tags=['dimensions']
) }}

WITH student_updates AS (
    -- Get all student records with row numbers to identify changes
    SELECT
        student_id,
        full_name,
        gender,
        date_of_birth,
        division,
        district,
        upazila,
        socioeconomic_status,
        disability_status,
        guardian_contact,
        created_at,
        -- Generate a hash of all attributes to detect changes
        TO_HEX(
            MD5(
                CONCAT(
                    COALESCE(CAST(student_id AS STRING), ''),
                    COALESCE(full_name, ''),
                    COALESCE(gender, ''),
                    COALESCE(CAST(date_of_birth AS STRING), ''),
                    COALESCE(division, ''),
                    COALESCE(district, ''),
                    COALESCE(upazila, ''),
                    COALESCE(socioeconomic_status, ''),
                    COALESCE(disability_status, ''),
                    COALESCE(guardian_contact, '')
                )
            )
        ) AS row_hash,
        -- Get the previous hash for this student
        LAG(
            TO_HEX(
                MD5(
                    CONCAT(
                        COALESCE(CAST(student_id AS STRING), ''),
                        COALESCE(full_name, ''),
                        COALESCE(gender, ''),
                        COALESCE(CAST(date_of_birth AS STRING), ''),
                        COALESCE(division, ''),
                        COALESCE(district, ''),
                        COALESCE(upazila, ''),
                        COALESCE(socioeconomic_status, ''),
                        COALESCE(disability_status, ''),
                        COALESCE(guardian_contact, '')
                    )
                )
            )
        ) OVER (PARTITION BY student_id ORDER BY created_at) AS previous_row_hash,
        -- Get the next created_at to set valid_to date
        LEAD(created_at) OVER (PARTITION BY student_id ORDER BY created_at) AS next_created_at,
        -- Row number for deduplication
        ROW_NUMBER() OVER (PARTITION BY student_id, created_at ORDER BY created_at) AS rn
    FROM {{ source('raw', 'students') }}
    WHERE student_id IS NOT NULL
),

-- Only include rows where there's a change in the data or it's the first record
changed_records AS (
    SELECT
        student_id,
        full_name,
        gender,
        date_of_birth,
        division,
        district,
        upazila,
        socioeconomic_status,
        disability_status,
        guardian_contact,
        created_at,
        next_created_at,
        -- Calculate age based on date of birth
        DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) - 
            IF(EXTRACT(DAYOFYEAR FROM CURRENT_DATE) < EXTRACT(DAYOFYEAR FROM date_of_birth), 1, 0) AS age,
        -- Age group for analysis
        CASE
            WHEN DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) < 5 THEN '0-4'
            WHEN DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) BETWEEN 5 AND 9 THEN '5-9'
            WHEN DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) BETWEEN 10 AND 14 THEN '10-14'
            WHEN DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) BETWEEN 15 AND 19 THEN '15-19'
            WHEN DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) BETWEEN 20 AND 24 THEN '20-24'
            ELSE '25+'
        END AS age_group,
        -- Derive first and last names if needed
        SPLIT(full_name, ' ')[OFFSET(0)] AS first_name,
        ARRAY_REVERSE(SPLIT(full_name, ' '))[OFFSET(0)] AS last_name,
        -- Standardize gender values
        CASE 
            WHEN LOWER(gender) IN ('m', 'male', 'mâle', 'homme') THEN 'Male'
            WHEN LOWER(gender) IN ('f', 'female', 'femme') THEN 'Female'
            WHEN LOWER(gender) IN ('o', 'other', 'autre') THEN 'Other'
            ELSE 'Unknown'
        END AS standardized_gender,
        -- Disability flag
        CASE 
            WHEN disability_status IS NULL OR LOWER(disability_status) IN ('none', 'no', 'na', '') 
            THEN FALSE 
            ELSE TRUE 
        END AS has_disability,
        -- Urban/rural classification based on upazila name patterns (simplified)
        CASE
            WHEN LOWER(upazila) LIKE '%sadar%' OR LOWER(upazila) LIKE '%town%' OR 
                 LOWER(upazila) LIKE '%city%' OR LOWER(upazila) LIKE '%metro%' THEN 'Urban'
            ELSE 'Rural'
        END AS area_type,
        -- Current record indicator
        CASE WHEN next_created_at IS NULL THEN TRUE ELSE FALSE END AS is_current,
        -- Record effective dates
        created_at AS effective_from,
        COALESCE(
            TIMESTAMP_SUB(
                TIMESTAMP(next_created_at), 
                INTERVAL 1 SECOND
            ), 
            TIMESTAMP('9999-12-31 23:59:59')
        ) AS effective_to
    FROM student_updates
    WHERE (row_hash != previous_row_hash OR previous_row_hash IS NULL) AND rn = 1
)

SELECT
    -- Surrogate key
    GENERATE_UUID() AS student_key,
    
    -- Business key
    student_id,
    
    -- Attributes
    full_name,
    first_name,
    last_name,
    standardized_gender AS gender,
    date_of_birth,
    age,
    age_group,
    division,
    district,
    upazila,
    area_type,
    socioeconomic_status,
    has_disability,
    disability_status,
    guardian_contact,
    
    -- Metadata
    is_current,
    effective_from,
    effective_to,
    
    -- Audit fields
    CURRENT_TIMESTAMP() AS dwh_created_at,
    CURRENT_TIMESTAMP() AS dwh_updated_at,
    
    -- Record source
    '{{ this }}' AS record_source
FROM changed_records
ORDER BY student_id, effective_from
