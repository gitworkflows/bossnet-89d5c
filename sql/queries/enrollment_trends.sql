-- Query: Enrollment trends over time by division
SELECT s.division, DATE_TRUNC('year', e.enrollment_date) AS year, COUNT(*) AS enrollments
FROM enrollments e
JOIN schools s ON e.school_id = s.school_id
GROUP BY s.division, year
ORDER BY s.division, year;
