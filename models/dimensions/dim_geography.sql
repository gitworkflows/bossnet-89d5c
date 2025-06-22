{{ config(
    materialized='table',
    schema='dimensions',
    unique_key='geography_key',
    tags=['dimensions']
) }}

-- First, get all unique combinations of division, district, and upazila from students
WITH student_locations AS (
    SELECT 
        division,
        district,
        upazila,
        'Student' AS source_type
    FROM {{ source('raw', 'students') }}
    WHERE division IS NOT NULL
    
    UNION DISTINCT
    
    -- Also include locations from schools
    SELECT 
        division,
        district,
        upazila,
        'School' AS source_type
    FROM {{ source('raw', 'schools') }}
    WHERE division IS NOT NULL
),

-- Get distinct locations with standardized names
distinct_locations AS (
    SELECT
        division,
        district,
        upazila,
        -- Clean and standardize division names
        CASE 
            WHEN UPPER(division) LIKE 'DHAKA%' THEN 'Dhaka'
            WHEN UPPER(division) LIKE 'CHITTAGONG%' OR UPPER(division) LIKE 'CHATTOGRAM%' THEN 'Chattogram'
            WHEN UPPER(division) LIKE 'RAJSHAHI%' THEN 'Rajshahi'
            WHEN UPPER(division) LIKE 'KHULNA%' THEN 'Khulna'
            WHEN UPPER(division) LIKE 'BARISHAL%' THEN 'Barishal'
            WHEN UPPER(division) LIKE 'SYLHET%' THEN 'Sylhet'
            WHEN UPPER(division) LIKE 'RANGPUR%' THEN 'Rangpur'
            WHEN UPPER(division) LIKE 'MYMENSINGH%' THEN 'Mymensingh'
            ELSE TRIM(division)
        END AS standardized_division,
        -- Clean district names
        TRIM(district) AS cleaned_district,
        -- Clean upazila names
        TRIM(REGEXP_REPLACE(upazila, r'\s+', ' ')) AS cleaned_upazila
    FROM student_locations
    WHERE division IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY 
            division, 
            COALESCE(district, ''), 
            COALESCE(upazila, '') 
        ORDER BY source_type
    ) = 1
),

-- Add administrative hierarchy and metadata
enriched_locations AS (
    SELECT
        -- Generate a unique key for each location
        GENERATE_UUID() AS geography_key,
        
        -- Standardized location information
        standardized_division AS division_name,
        COALESCE(cleaned_district, 'Unknown') AS district_name,
        COALESCE(cleaned_upazila, 'Unknown') AS upazila_name,
        
        -- Original values for reference
        division AS original_division,
        district AS original_district,
        upazila AS original_upazila,
        
        -- Hierarchical relationships
        standardized_division AS division_id,
        CONCAT(standardized_division, '|', COALESCE(cleaned_district, 'Unknown')) AS district_id,
        CONCAT(
            standardized_division, '|', 
            COALESCE(cleaned_district, 'Unknown'), '|', 
            COALESCE(cleaned_upazila, 'Unknown')
        ) AS upazila_id,
        
        -- Geographic metadata (would be populated from a reference table in a real implementation)
        NULL AS division_population,
        NULL AS district_population,
        NULL AS upazila_population,
        NULL AS division_area_sq_km,
        NULL AS district_area_sq_km,
        NULL AS upazila_area_sq_km,
        
        -- Urban/rural classification
        CASE
            WHEN UPPER(COALESCE(cleaned_upazila, '')) LIKE '%SADAR%' 
                 OR UPPER(COALESCE(cleaned_upazila, '')) LIKE '%TOWN%' 
                 OR UPPER(COALESCE(cleaned_upazila, '')) LIKE '%CITY%' 
            THEN 'Urban'
            ELSE 'Rural'
        END AS urban_rural_classification,
        
        -- Development indicators (would come from external data)
        NULL AS poverty_rate,
        NULL AS literacy_rate,
        NULL AS hdi_score,
        
        -- Audit fields
        CURRENT_TIMESTAMP() AS dwh_created_at,
        CURRENT_TIMESTAMP() AS dwh_updated_at,
        
        -- Record source
        '{{ this }}' AS record_source
    FROM distinct_locations
)

SELECT * FROM enriched_locations
ORDER BY division_name, district_name, upazila_name
