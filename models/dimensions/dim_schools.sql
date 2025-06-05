WITH raw_schools AS (
    SELECT * FROM {{ source('raw', 'schools') }}
)
SELECT
    school_id,
    name,
    division,
    district,
    upazila,
    type,
    education_level,
    is_rural,
    geo_location,
    contact_info,
    created_at
FROM raw_schools;
