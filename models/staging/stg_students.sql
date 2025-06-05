WITH raw_students AS (
    SELECT * FROM {{ source('raw', 'students') }}
)
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
    created_at
FROM raw_students;
