-- Query: Count students by gender and division
SELECT s.division, st.gender, COUNT(*) AS student_count
FROM students st
JOIN enrollments e ON st.student_id = e.student_id
JOIN schools s ON e.school_id = s.school_id
GROUP BY s.division, st.gender
ORDER BY s.division, st.gender;
