-- Migration: Add foreign key relationships to enrollments
ALTER TABLE enrollments
ADD CONSTRAINT fk_enrollment_student
FOREIGN KEY (student_id)
REFERENCES students(student_id)
ON DELETE CASCADE;

ALTER TABLE enrollments
ADD CONSTRAINT fk_enrollment_school
FOREIGN KEY (school_id)
REFERENCES schools(school_id)
ON DELETE CASCADE;
