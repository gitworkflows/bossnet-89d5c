WITH raw_enrollments AS (
    SELECT * FROM {{ source('raw', 'enrollments') }}
)
SELECT
    enrollment_id,
    student_id,
    school_id,
    enrollment_year,
    grade,
    status,
    dropout_reason,
    transfer_school_id,
    created_at
FROM raw_enrollments;
