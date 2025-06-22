{{ config(
    materialized='table',
    schema='marts',
    unique_key='equity_metric_key',
    tags=['marts', 'equity']
) }}

WITH student_metrics AS (
    -- Base metrics at the student level
    SELECT
        -- Geography
        dg.division_name,
        dg.district_name,
        dg.upazila_name,
        dg.urban_rural_classification,
        
        -- Student demographics
        ds.gender,
        ds.age_group,
        ds.socioeconomic_status,
        ds.has_disability,
        
        -- School characteristics
        sch.type AS school_type,
        sch.is_rural,
        sch.education_level,
        
        -- Academic context
        ar.academic_year,
        ar.grade,
        
        -- Performance metrics
        AVG(ar.percentage) AS avg_performance,
        COUNT(DISTINCT ar.student_id) AS student_count,
        
        -- Attendance metrics
        AVG(att.attendance_rate) AS avg_attendance_rate,
        
        -- Equity indicators
        CASE 
            WHEN ds.gender = 'Female' THEN 1 
            ELSE 0 
        END AS is_female,
        
        CASE 
            WHEN ds.socioeconomic_status IN ('Low', 'Very Low') THEN 1 
            ELSE 0 
        END AS is_low_income,
        
        CASE 
            WHEN ds.has_disability THEN 1 
            ELSE 0 
        END AS has_disability_flag,
        
        CASE 
            WHEN dg.urban_rural_classification = 'Rural' THEN 1 
            ELSE 0 
        END AS is_rural_area
        
    FROM {{ ref('fct_assessment_results') }} ar
    JOIN {{ ref('dim_students') }} ds 
        ON ar.student_id = ds.student_id 
        AND ar.assessment_date BETWEEN ds.effective_from AND ds.effective_to
    JOIN {{ ref('dim_schools') }} sch ON ar.school_id = sch.school_id
    JOIN {{ ref('dim_geography') }} dg 
        ON sch.division = dg.division_name
        AND sch.district = dg.district_name
        AND sch.upazila = dg.upazila_name
    
    -- Join with attendance data
    LEFT JOIN (
        SELECT 
            student_id,
            school_id,
            academic_year,
            term,
            grade,
            section,
            COUNTIF(is_present) / COUNT(*) AS attendance_rate
        FROM {{ ref('fct_attendances') }}
        GROUP BY 1, 2, 3, 4, 5, 6
    ) att ON ar.student_id = att.student_id 
        AND ar.school_id = att.school_id
        AND ar.academic_year = att.academic_year
        AND ar.term = att.term
        AND ar.grade = att.grade
    
    WHERE ar.assessment_type = 'Exam'  -- Focus on major assessments
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
),

-- Calculate equity metrics
equity_analysis AS (
    SELECT
        -- Grouping dimensions
        division_name,
        district_name,
        upazila_name,
        urban_rural_classification,
        school_type,
        education_level,
        academic_year,
        grade,
        
        -- Overall metrics
        SUM(student_count) AS total_students,
        AVG(avg_performance) AS overall_avg_performance,
        AVG(avg_attendance_rate) AS overall_attendance_rate,
        
        -- Gender equity
        SAFE_DIVIDE(
            SUM(CASE WHEN gender = 'Female' THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN gender = 'Female' THEN student_count ELSE 0 END), 0)
        ) AS female_avg_performance,
        
        SAFE_DIVIDE(
            SUM(CASE WHEN gender = 'Male' THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN gender = 'Male' THEN student_count ELSE 0 END), 0)
        ) AS male_avg_performance,
        
        -- Socioeconomic equity
        SAFE_DIVIDE(
            SUM(CASE WHEN is_low_income = 1 THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN is_low_income = 1 THEN student_count ELSE 0 END), 0)
        ) AS low_income_avg_performance,
        
        SAFE_DIVIDE(
            SUM(CASE WHEN is_low_income = 0 THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN is_low_income = 0 THEN student_count ELSE 0 END), 0)
        ) AS non_low_income_avg_performance,
        
        -- Disability equity
        SAFE_DIVIDE(
            SUM(CASE WHEN has_disability_flag = 1 THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN has_disability_flag = 1 THEN student_count ELSE 0 END), 0)
        ) AS with_disability_avg_performance,
        
        SAFE_DIVIDE(
            SUM(CASE WHEN has_disability_flag = 0 THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN has_disability_flag = 0 THEN student_count ELSE 0 END), 0)
        ) AS without_disability_avg_performance,
        
        -- Urban/rural equity
        SAFE_DIVIDE(
            SUM(CASE WHEN is_rural_area = 1 THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN is_rural_area = 1 THEN student_count ELSE 0 END), 0)
        ) AS rural_avg_performance,
        
        SAFE_DIVIDE(
            SUM(CASE WHEN is_rural_area = 0 THEN avg_performance * student_count ELSE 0 END),
            NULLIF(SUM(CASE WHEN is_rural_area = 0 THEN student_count ELSE 0 END), 0)
        ) AS urban_avg_performance,
        
        -- Counts for each group
        SUM(CASE WHEN gender = 'Female' THEN student_count ELSE 0 END) AS female_count,
        SUM(CASE WHEN gender = 'Male' THEN student_count ELSE 0 END) AS male_count,
        SUM(CASE WHEN is_low_income = 1 THEN student_count ELSE 0 END) AS low_income_count,
        SUM(CASE WHEN has_disability_flag = 1 THEN student_count ELSE 0 END) AS with_disability_count,
        SUM(CASE WHEN is_rural_area = 1 THEN student_count ELSE 0 END) AS rural_count
        
    FROM student_metrics
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)

-- Final calculation of equity gaps and indicators
SELECT
    -- Surrogate key
    GENERATE_UUID() AS equity_metric_key,
    
    -- Grouping dimensions
    division_name,
    district_name,
    upazila_name,
    urban_rural_classification,
    school_type,
    education_level,
    academic_year,
    grade,
    
    -- Overall metrics
    total_students,
    ROUND(overall_avg_performance, 2) AS overall_avg_performance,
    ROUND(overall_attendance_rate * 100, 2) AS overall_attendance_rate,
    
    -- Gender equity metrics
    ROUND(female_avg_performance, 2) AS female_avg_performance,
    ROUND(male_avg_performance, 2) AS male_avg_performance,
    ROUND(male_avg_performance - female_avg_performance, 2) AS gender_gap,
    
    -- Socioeconomic equity metrics
    ROUND(low_income_avg_performance, 2) AS low_income_avg_performance,
    ROUND(non_low_income_avg_performance, 2) AS non_low_income_avg_performance,
    ROUND(non_low_income_avg_performance - low_income_avg_performance, 2) AS income_gap,
    
    -- Disability equity metrics
    ROUND(with_disability_avg_performance, 2) AS with_disability_avg_performance,
    ROUND(without_disability_avg_performance, 2) AS without_disability_avg_performance,
    ROUND(without_disability_avg_performance - with_disability_avg_performance, 2) AS disability_gap,
    
    -- Urban/rural equity metrics
    ROUND(rural_avg_performance, 2) AS rural_avg_performance,
    ROUND(urban_avg_performance, 2) AS urban_avg_performance,
    ROUND(urban_avg_performance - rural_avg_performance, 2) AS urban_rural_gap,
    
    -- Group counts
    female_count,
    male_count,
    low_income_count,
    with_disability_count,
    rural_count,
    
    -- Equity indicators (1 = equitable, 0 = not equitable)
    CASE 
        WHEN ABS(male_avg_performance - female_avg_performance) <= 5 THEN 1 
        ELSE 0 
    END AS is_gender_equitable,
    
    CASE 
        WHEN ABS(non_low_income_avg_performance - low_income_avg_performance) <= 5 THEN 1 
        ELSE 0 
    END AS is_income_equitable,
    
    CASE 
        WHEN ABS(without_disability_avg_performance - with_disability_avg_performance) <= 5 THEN 1 
        ELSE 0 
    END AS is_disability_equitable,
    
    CASE 
        WHEN ABS(urban_avg_performance - rural_avg_performance) <= 5 THEN 1 
        ELSE 0 
    END AS is_location_equitable,
    
    -- Timestamp
    CURRENT_DATE() AS as_of_date,
    CURRENT_TIMESTAMP() AS dwh_created_at
    
FROM equity_analysis
-- Only include groups with sufficient data
WHERE total_students >= 10
  AND female_count >= 5
  AND male_count >= 5
  AND (low_income_count >= 5 OR low_income_count IS NULL)
  AND (with_disability_count >= 3 OR with_disability_count IS NULL)
  AND (rural_count >= 5 OR rural_count = 0)  -- Allow all urban or all rural
