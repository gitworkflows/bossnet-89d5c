-- Lookup Tables for Education Data Platform

CREATE TABLE grades (
    grade_code VARCHAR PRIMARY KEY,
    grade_name VARCHAR
);

CREATE TABLE divisions (
    division_code VARCHAR PRIMARY KEY,
    division_name VARCHAR
);

CREATE TABLE districts (
    district_code VARCHAR PRIMARY KEY,
    district_name VARCHAR,
    division_code VARCHAR REFERENCES divisions(division_code)
);

CREATE TABLE upazilas (
    upazila_code VARCHAR PRIMARY KEY,
    upazila_name VARCHAR,
    district_code VARCHAR REFERENCES districts(district_code)
);

CREATE TABLE dropout_reasons (
    reason_code VARCHAR PRIMARY KEY,
    description VARCHAR
);
