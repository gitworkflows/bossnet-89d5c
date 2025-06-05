-- Unique constraint: students name + date_of_birth
ALTER TABLE students
ADD CONSTRAINT unique_student_name_dob
UNIQUE (name, date_of_birth);

-- Check constraint: gender must be 'Male', 'Female', or 'Other'
ALTER TABLE students
ADD CONSTRAINT check_gender
CHECK (gender IN ('Male', 'Female', 'Other'));
