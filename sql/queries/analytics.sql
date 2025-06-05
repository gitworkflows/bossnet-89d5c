-- Sample Analytics Queries

-- Students by division & gender
SELECT division, gender, COUNT(*) AS student_count
FROM students
GROUP BY division, gender;

-- Dropout rates by region
SELECT s.division, COUNT(*) FILTER (WHERE e.status = 'dropout')::FLOAT / COUNT(*) AS dropout_rate
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
GROUP BY s.division;

-- School-wise performance aggregates
SELECT e.school_id, s.name, COUNT(*) AS total_enrollments
FROM enrollments e
JOIN schools s ON e.school_id = s.school_id
GROUP BY e.school_id, s.name;

-- Yearly enrollment trends
SELECT enrollment_year, COUNT(*) AS total_enrollments
FROM enrollments
GROUP BY enrollment_year
ORDER BY enrollment_year;
