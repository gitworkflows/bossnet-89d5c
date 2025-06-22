{{ config(
    materialized='table',
    schema='dimensions',
    unique_key='date_id'
) }}

WITH date_series AS (
    SELECT 
        date_day,
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        EXTRACT(MONTH FROM date_day) AS month,
        EXTRACT(DAY FROM date_day) AS day,
        EXTRACT(DAYOFWEEK FROM date_day) AS day_of_week,
        EXTRACT(DAYOFYEAR FROM date_day) AS day_of_year,
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        -- Academic year (July 1 to June 30)
        CASE 
            WHEN EXTRACT(MONTH FROM date_day) >= 7 
            THEN EXTRACT(YEAR FROM date_day) || '-' || (EXTRACT(YEAR FROM date_day) + 1)
            ELSE (EXTRACT(YEAR FROM date_day) - 1) || '-' || EXTRACT(YEAR FROM date_day)
        END AS academic_year,
        -- Fiscal year (July 1 to June 30)
        CASE 
            WHEN EXTRACT(MONTH FROM date_day) >= 7 
            THEN EXTRACT(YEAR FROM date_day) + 1
            ELSE EXTRACT(YEAR FROM date_day)
        END AS fiscal_year,
        -- Academic term
        CASE 
            WHEN EXTRACT(MONTH FROM date_day) IN (1, 2, 3, 4, 5, 6) THEN 'Spring'
            WHEN EXTRACT(MONTH FROM date_day) IN (7, 8, 9, 10, 11, 12) THEN 'Fall'
        END AS academic_term,
        -- Bangladeshi public holidays (simplified)
        CASE 
            WHEN EXTRACT(MONTH FROM date_day) = 2 AND EXTRACT(DAY FROM date_day) = 21 THEN 'International Mother Language Day'
            WHEN EXTRACT(MONTH FROM date_day) = 3 AND EXTRACT(DAY FROM date_day) = 26 THEN 'Independence Day'
            WHEN EXTRACT(MONTH FROM date_day) = 4 AND EXTRACT(DAY FROM date_day) = 14 THEN 'Bengali New Year'
            WHEN EXTRACT(MONTH FROM date_day) = 12 AND EXTRACT(DAY FROM date_day) = 16 THEN 'Victory Day'
            ELSE NULL
        END AS bangladesh_holiday,
        -- Weekday indicator
        CASE 
            WHEN EXTRACT(DAYOFWEEK FROM date_day) IN (1, 7) THEN FALSE 
            ELSE TRUE 
        END AS is_weekday
    FROM (
        SELECT 
            DATE_ADD(
                DATE('{{ var("start_date", "2015-01-01") }}'), 
                INTERVAL seq DAY
            ) AS date_day
        FROM UNNEST(GENERATE_ARRAY(0, 365*10)) AS seq  -- 10 years of dates
    )
)

SELECT
    -- Surrogate key
    CAST(FORMAT_DATE('%Y%m%d', date_day) AS INT64) AS date_id,
    
    -- Date
    date_day AS full_date,
    
    -- Year
    year,
    fiscal_year,
    academic_year,
    
    -- Quarter
    quarter,
    CONCAT('Q', quarter) AS quarter_name,
    CONCAT('Q', quarter, ' ', year) AS quarter_year,
    
    -- Month
    month,
    FORMAT_DATE('%B', date_day) AS month_name,
    FORMAT_DATE('%b', date_day) AS month_short_name,
    
    -- Day
    day,
    day_of_week,
    FORMAT_DATE('%A', date_day) AS day_name,
    FORMAT_DATE('%a', date_day) AS day_short_name,
    day_of_year,
    
    -- Week
    week_of_year,
    
    -- Academic
    academic_term,
    
    -- Holiday
    bangladesh_holiday,
    
    -- Flags
    is_weekday,
    bangladesh_holiday IS NOT NULL AS is_holiday,
    
    -- Date parts for filtering
    CONCAT(CAST(year AS STRING), LPAD(CAST(month AS STRING), 2, '0')) AS year_month,
    CONCAT(academic_year, ' ', academic_term) AS academic_period,
    
    -- Date math
    DATE_DIFF(date_day, CURRENT_DATE(), DAY) AS days_from_today,
    DATE_DIFF(CURRENT_DATE(), date_day, DAY) AS days_to_today
FROM date_series
ORDER BY date_day
