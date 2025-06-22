-- Create database (uncomment if needed)
-- CREATE DATABASE student_data_db;
-- \c student_data_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    academic_year VARCHAR(9) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    class_id INTEGER REFERENCES classes(class_id),
    enrollment_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id SERIAL PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    subject_code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    specialization VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS courses (
    course_id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(subject_id),
    class_id INTEGER REFERENCES classes(class_id),
    teacher_id UUID REFERENCES teachers(teacher_id),
    academic_year VARCHAR(9) NOT NULL,
    semester VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grades (
    grade_id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(student_id),
    course_id INTEGER REFERENCES courses(course_id),
    grade DECIMAL(5,2) NOT NULL CHECK (grade >= 0 AND grade <= 100),
    grade_date DATE NOT NULL,
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_students_class ON students(class_id);
CREATE INDEX idx_grades_student ON grades(student_id);
CREATE INDEX idx_grades_course ON grades(course_id);
CREATE INDEX idx_courses_teacher ON courses(teacher_id);

-- Insert sample data
-- Insert classes
INSERT INTO classes (class_name, grade_level, academic_year) VALUES
('Class 1A', 1, '2024-2025'),
('Class 1B', 1, '2024-2025'),
('Class 2A', 2, '2024-2025'),
('Class 2B', 2, '2024-2025'),
('Class 3A', 3, '2024-2025'),
('Class 3B', 3, '2024-2025');

-- Insert subjects
INSERT INTO subjects (subject_name, subject_code, description) VALUES
('Mathematics', 'MATH-101', 'Basic Mathematics'),
('English', 'ENG-101', 'English Language and Literature'),
('Science', 'SCI-101', 'General Science'),
('Bangla', 'BAN-101', 'Bangla Language and Literature'),
('Social Studies', 'SOC-101', 'Social Studies and Civics');

-- Insert teachers
INSERT INTO teachers (first_name, last_name, email, phone, hire_date, specialization) VALUES
('Rahman', 'Khan', 'rkhan@school.edu', '+8801712345678', '2020-01-15', 'Mathematics'),
('Fatima', 'Ahmed', 'fahmed@school.edu', '+8801812345678', '2019-05-20', 'English'),
('Karim', 'Islam', 'kislam@school.edu', '+8801912345678', '2021-02-10', 'Science'),
('Ayesha', 'Begum', 'abegum@school.edu', '+8801612345678', '2018-08-01', 'Bangla'),
('Kamal', 'Hossain', 'khossain@school.edu', '+8801512345678', '2022-03-15', 'Social Studies');

-- Insert students (sample data for 20 students)
DO $$
DECLARE
    class_ids INTEGER[];
    first_names TEXT[] := ARRAY['Aarav', 'Aisha', 'Arjun', 'Diya', 'Ishaan', 'Kavya', 'Rahul', 'Priya', 'Vivaan', 'Ananya', 'Vihaan', 'Anika', 'Aditya', 'Saanvi', 'Kabir', 'Aadhya', 'Vivaan', 'Anaya', 'Ayaan', 'Pari'];
    last_names TEXT[] := ARRAY['Khan', 'Ahmed', 'Islam', 'Chowdhury', 'Rahman', 'Hossain', 'Ali', 'Akter', 'Siddique', 'Begum', 'Uddin', 'Sultana', 'Karim', 'Akhtar', 'Malik', 'Bano', 'Sarker', 'Jahan', 'Miah', 'Khatun'];
    genders TEXT[] := ARRAY['Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female'];
    i INTEGER;
    class_idx INTEGER;
    class_count INTEGER;
    class_id_val INTEGER;
    enrollment_date_val DATE;
BEGIN
    -- Get all class IDs
    SELECT array_agg(class_id) INTO class_ids FROM classes;
    class_count := array_length(class_ids, 1);
    
    -- Insert 20 sample students
    FOR i IN 1..20 LOOP
        -- Distribute students across classes
        class_idx := ((i-1) % class_count) + 1;
        class_id_val := class_ids[class_idx];
        
        -- Generate enrollment date (within the last 3 years)
        enrollment_date_val := CURRENT_DATE - (random() * 1095)::INTEGER;
        
        -- Insert student
        INSERT INTO students (
            first_name,
            last_name,
            date_of_birth,
            gender,
            email,
            phone,
            address,
            class_id,
            enrollment_date
        ) VALUES (
            first_names[i],
            last_names[i],
            (CURRENT_DATE - (random() * 3650 + 3650)::INTEGER)::DATE, -- Age between 10-20
            genders[i],
            LOWER(first_names[i] || '.' || last_names[i] || '@student.school.edu'),
            '+8801' || (5 + (random() * 5))::INTEGER::TEXT || 
              LPAD((random() * 9999999)::INTEGER::TEXT, 7, '0'),
            'House ' || i || ', Road ' || (i % 10 + 1) || ', Dhaka',
            class_id_val,
            enrollment_date_val
        );
    END LOOP;
END $$;

-- Insert courses
INSERT INTO courses (subject_id, class_id, teacher_id, academic_year, semester)
SELECT 
    s.subject_id,
    c.class_id,
    t.teacher_id,
    '2024-2025' as academic_year,
    CASE WHEN random() > 0.5 THEN 'Spring' ELSE 'Fall' END as semester
FROM 
    (SELECT generate_series(1, 5) as subject_num) sub
CROSS JOIN 
    (SELECT class_id FROM classes) c
CROSS JOIN LATERAL (
    SELECT subject_id 
    FROM subjects 
    ORDER BY subject_id 
    LIMIT 1 OFFSET (sub.subject_num - 1) % 5
) s
CROSS JOIN LATERAL (
    SELECT teacher_id 
    FROM teachers 
    ORDER BY teacher_id 
    LIMIT 1 OFFSET (sub.subject_num - 1) % 5
) t;

-- Insert grades for students in each course
DO $$
DECLARE
    student_record RECORD;
    course_record RECORD;
    grade_val DECIMAL(5,2);
    grade_date_val DATE;
BEGIN
    -- For each student
    FOR student_record IN SELECT student_id, class_id FROM students
    LOOP
        -- For each course in the student's class
        FOR course_record IN 
            SELECT course_id, subject_id 
            FROM courses 
            WHERE class_id = student_record.class_id
        LOOP
            -- Generate a grade between 40 and 100, with most between 60-90
            grade_val := 40 + (random() * 60)::DECIMAL(5,2);
            IF grade_val > 90 THEN
                grade_val := 90 + (random() * 10)::DECIMAL(5,2);
            ELSIF grade_val < 60 THEN
                grade_val := 40 + (random() * 20)::DECIMAL(5,2);
            END IF;
            
            -- Generate a grade date within the academic year
            grade_date_val := '2024-01-01'::DATE + (random() * 300)::INTEGER;
            
            -- Insert grade
            INSERT INTO grades (student_id, course_id, grade, grade_date)
            VALUES (student_record.student_id, course_record.course_id, grade_val, grade_date_val);
        END LOOP;
    END LOOP;
END $$;

-- Create a view for student performance
CREATE OR REPLACE VIEW student_performance_view AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.class_name,
    s.gender,
    s.enrollment_date,
    AVG(g.grade) as avg_grade,
    COUNT(DISTINCT g.course_id) as courses_taken,
    COUNT(CASE WHEN g.grade >= 80 THEN 1 END) as a_grades
FROM 
    students s
JOIN 
    grades g ON s.student_id = g.student_id
JOIN 
    classes c ON s.class_id = c.class_id
GROUP BY 
    s.student_id, s.first_name, s.last_name, c.class_name, s.gender, s.enrollment_date;

-- Create a view for class performance
CREATE OR REPLACE VIEW class_performance_view AS
SELECT 
    c.class_id,
    c.class_name,
    COUNT(DISTINCT s.student_id) as total_students,
    AVG(g.grade) as avg_grade,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY g.grade) as median_grade,
    COUNT(DISTINCT CASE WHEN g.grade >= 80 THEN s.student_id END) as top_performers,
    COUNT(DISTINCT CASE WHEN g.grade < 40 THEN s.student_id END) as needs_improvement
FROM 
    classes c
LEFT JOIN 
    students s ON c.class_id = s.class_id
LEFT JOIN 
    grades g ON s.student_id = g.student_id
GROUP BY 
    c.class_id, c.class_name;
