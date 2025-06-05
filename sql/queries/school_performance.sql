-- Query: Count enrollments per school
SELECT s.school_id, s.name, COUNT(e.enrollment_id) AS total_enrollments
FROM schools s
LEFT JOIN enrollments e ON s.school_id = e.school_id
GROUP BY s.school_id, s.name
ORDER BY total_enrollments DESC;
