-- Foreign key: enrollments.student_id -> students.student_id
ALTER TABLE enrollments
ADD CONSTRAINT fk_enrollment_student
FOREIGN KEY (student_id)
REFERENCES students(student_id)
ON DELETE CASCADE;

-- Foreign key: enrollments.school_id -> schools.school_id
ALTER TABLE enrollments
ADD CONSTRAINT fk_enrollment_school
FOREIGN KEY (school_id)
REFERENCES schools(school_id)
ON DELETE CASCADE;
