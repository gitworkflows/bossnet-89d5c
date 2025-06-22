{{ config(
    materialized='table',
    schema='marts',
    unique_key='student_performance_key',
    tags=['marts', 'education']
) }}

WITH student_performance AS (
    SELECT
        -- Student information
        ds.student_key,
        ds.student_id,
        ds.full_name AS student_name,
        ds.standardized_gender AS gender,
        ds.age,
        ds.age_group,
        
        -- School information
        sch.school_id,
        sch.name AS school_name,
        sch.type AS school_type,
        sch.education_level,
        sch.is_rural,
        
        -- Geography
        dg.division_name,
        dg.district_name,
        dg.upazila_name,
        dg.urban_rural_classification,
        
        -- Academic context
        ar.academic_year,
        ar.term,
        ar.grade,
        ar.section,
        ar.subject_id,
        
        -- Performance metrics
        COUNT(DISTINCT ar.assessment_id) AS total_assessments,
        AVG(ar.percentage) AS avg_percentage,
        AVG(CASE WHEN ar.assessment_type = 'Exam' THEN ar.percentage END) AS avg_exam_percentage,
        AVG(CASE WHEN ar.assessment_type = 'Quiz' THEN ar.percentage END) AS avg_quiz_percentage,
        AVG(CASE WHEN ar.assessment_type = 'Assignment' THEN ar.percentage END) AS avg_assignment_percentage,
        
        -- Grade distribution
        COUNTIF(ar.standardized_grade = 'A+') AS count_a_plus,
        COUNTIF(ar.standardized_grade = 'A') AS count_a,
        COUNTIF(ar.standardized_grade = 'A-') AS count_a_minus,
        COUNTIF(ar.standardized_grade = 'B') AS count_b,
        COUNTIF(ar.standardized_grade = 'C') AS count_c,
        COUNTIF(ar.standardized_grade = 'D') AS count_d,
        COUNTIF(ar.standardized_grade = 'F') AS count_f,
        
        -- Attendance metrics (from attendance fact)
        COALESCE(att.attendance_rate, 0) AS attendance_rate,
        COALESCE(att.total_present, 0) AS total_present,
        COALESCE(att.total_absent, 0) AS total_absent,
        
        -- Current status
        CURRENT_DATE() AS as_of_date
        
    FROM {{ ref('fct_assessment_results') }} ar
    JOIN {{ ref('dim_students') }} ds 
        ON ar.student_id = ds.student_id 
        AND ar.assessment_date BETWEEN ds.effective_from AND ds.effective_to
    JOIN {{ ref('dim_schools') }} sch ON ar.school_id = sch.school_id
    JOIN {{ ref('dim_geography') }} dg 
        ON sch.division = dg.division_name
        AND sch.district = dg.district_name
        AND sch.upazila = dg.upazila_name
    
    -- Left join with attendance data
    LEFT JOIN (
        SELECT 
            student_id,
            school_id,
            academic_year,
            term,
            grade,
            section,
            COUNTIF(is_present) / COUNT(*) AS attendance_rate,
            COUNTIF(is_present) AS total_present,
            COUNTIF(NOT is_present) AS total_absent
        FROM {{ ref('fct_attendances') }}
        GROUP BY 1, 2, 3, 4, 5, 6
    ) att ON ar.student_id = att.student_id 
        AND ar.school_id = att.school_id
        AND ar.academic_year = att.academic_year
        AND ar.term = att.term
        AND ar.grade = att.grade
        AND ar.section = att.section
    
    GROUP BY 
        ds.student_key, ds.student_id, ds.full_name, ds.standardized_gender, ds.age, ds.age_group,
        sch.school_id, sch.name, sch.type, sch.education_level, sch.is_rural,
        dg.division_name, dg.district_name, dg.upazila_name, dg.urban_rural_classification,
        ar.academic_year, ar.term, ar.grade, ar.section, ar.subject_id,
        att.attendance_rate, att.total_present, att.total_absent
)

SELECT
    -- Surrogate key
    GENERATE_UUID() AS student_performance_key,
    
    -- Keys
    student_key,
    student_id,
    school_id,
    subject_id,
    
    -- Student information
    student_name,
    gender,
    age,
    age_group,
    
    -- School information
    school_name,
    school_type,
    education_level,
    is_rural,
    
    -- Location information
    division_name,
    district_name,
    upazila_name,
    urban_rural_classification,
    
    -- Academic context
    academic_year,
    term,
    grade,
    section,
    
    -- Performance metrics
    total_assessments,
    ROUND(avg_percentage, 2) AS avg_percentage,
    ROUND(avg_exam_percentage, 2) AS avg_exam_percentage,
    ROUND(avg_quiz_percentage, 2) AS avg_quiz_percentage,
    ROUND(avg_assignment_percentage, 2) AS avg_assignment_percentage,
    
    -- Grade distribution
    count_a_plus,
    count_a,
    count_a_minus,
    count_b,
    count_c,
    count_d,
    count_f,
    
    -- Attendance metrics
    ROUND(attendance_rate * 100, 2) AS attendance_percentage,
    total_present,
    total_absent,
    
    -- Performance indicators
    CASE
        WHEN avg_percentage >= 80 THEN 'Excellent'
        WHEN avg_percentage >= 65 THEN 'Good'
        WHEN avg_percentage >= 50 THEN 'Average'
        WHEN avg_percentage >= 33 THEN 'Below Average'
        ELSE 'Needs Improvement'
    END AS performance_category,
    
    -- Attendance indicators
    CASE
        WHEN attendance_rate >= 0.9 THEN 'Excellent'
        WHEN attendance_rate >= 0.8 THEN 'Good'
        WHEN attendance_rate >= 0.7 THEN 'Average'
        WHEN attendance_rate >= 0.6 THEN 'Below Average'
        ELSE 'Poor'
    END AS attendance_category,
    
    -- Timestamp
    as_of_date,
    CURRENT_TIMESTAMP() AS dwh_created_at
    
FROM student_performance
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY student_id, school_id, academic_year, term, grade, section, subject_id 
    ORDER BY as_of_date DESC
) = 1
