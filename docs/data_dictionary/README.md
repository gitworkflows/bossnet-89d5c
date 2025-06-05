# Data Dictionary

This directory contains comprehensive documentation about the data structures and definitions used in the Bangladesh Student Data Analysis project.

## Data Categories

### 1. Student Demographics
- student_id (STRING): Unique identifier for each student
- name (STRING): Student's full name
- date_of_birth (DATE): Student's date of birth
- gender (ENUM): Student's gender ['Male', 'Female', 'Other']
- address (OBJECT): Student's residential address
  - division (STRING): Administrative division
  - district (STRING): District name
  - upazila (STRING): Upazila/Thana name
  - union (STRING): Union name
- guardian_info (OBJECT): Guardian's information
  - name (STRING): Guardian's name
  - relationship (STRING): Relationship with student
  - contact (STRING): Contact number

### 2. Academic Performance
- academic_year (STRING): Academic year (e.g., '2024-2025')
- grade_level (INTEGER): Current grade/class level
- subjects (ARRAY): List of subjects with performance metrics
  - subject_name (STRING): Name of the subject
  - marks (FLOAT): Marks obtained
  - grade_point (FLOAT): Grade point for the subject
  - teacher_id (STRING): Subject teacher's identifier
- gpa (FLOAT): Grade Point Average
- attendance_rate (FLOAT): Percentage of attendance

### 3. Institution Details
- institution_id (STRING): Unique identifier for the institution
- name (STRING): Institution name
- eiin (STRING): Educational Institution Identification Number
- category (ENUM): Institution category ['Primary', 'Secondary', 'Higher_Secondary']
- location (OBJECT): Institution's location details
  - coordinates (ARRAY): [latitude, longitude]
  - division (STRING): Administrative division
  - district (STRING): District name
- facilities (ARRAY): Available facilities
- staff_count (INTEGER): Total number of staff
- student_count (INTEGER): Total number of students

### 4. Enrollment Statistics
- enrollment_id (STRING): Unique enrollment identifier
- academic_year (STRING): Academic year
- grade_level (INTEGER): Grade/class level
- enrollment_date (DATE): Date of enrollment
- status (ENUM): Current status ['Active', 'Transferred', 'Graduated', 'Dropped']

### 5. Socioeconomic Indicators
- household_income (FLOAT): Monthly household income
- parent_education (ENUM): Highest education level of parents
- scholarship_status (BOOLEAN): Whether receiving any scholarship
- transport_mode (ENUM): Mode of transport to school
- distance_to_school (FLOAT): Distance from residence to school (km)

## Data Sources

### BANBEIS Data
Files and fields sourced from Bangladesh Bureau of Educational Information and Statistics

### Education Board Data
Examination results and academic performance metrics

### DSHE Data
Secondary and higher secondary institution-specific data

### DPE Data
Primary education statistics and metrics

### BBS Data
Demographic and socioeconomic indicators

## Data Quality Standards
- All dates must be in ISO format (YYYY-MM-DD)
- Geographic coordinates must be in decimal degrees
- Missing values should be explicitly marked as NULL
- Numerical grades should be rounded to 2 decimal places
- Monetary values should be in BDT (Bangladesh Taka)

## Update Frequency
- Academic performance: Quarterly updates
- Enrollment data: Annual updates
- Institution details: Annual updates
- Demographic data: As changes occur
- Socioeconomic data: Annual updates

## Data Privacy
- All personal identifiable information (PII) must be encrypted
- Access to student records requires appropriate authorization
- Data sharing must comply with education board guidelines
- Regular data audits for privacy compliance
