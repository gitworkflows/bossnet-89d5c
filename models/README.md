# Bangladesh Education Data Warehouse

This directory contains the dbt models for the Bangladesh Education Data Warehouse project. The data model follows the dimensional modeling approach with the following layers:

## Model Structure

### 1. Staging Layer (`staging/`)
- Raw data loaded from source systems with minimal transformations
- Naming convention: `stg_*.sql`
- Schema: `staging`

### 2. Dimensions (`dimensions/`)
- Conformed dimensions used across the data warehouse
- Includes slowly changing dimensions (SCD) where appropriate
- Naming convention: `dim_*.sql`
- Schema: `dimensions`

### 3. Facts (`facts/`)
- Fact tables containing business metrics and measures
- Organized by business process
- Naming convention: `fct_*.sql`
- Schema: `facts`

### 4. Marts (`marts/`)
- Business-facing data marts for specific analytical use cases
- Organized by business domain
- Schema: `marts`

## Key Dimensions

### dim_students
- Tracks student information with SCD Type 2 support
- Includes demographic and contact information
- Links to geographic dimensions

### dim_schools
- School master data
- Location and contact information
- School characteristics

### dim_time
- Date dimension with calendar and fiscal periods
- Supports academic calendar specific to Bangladesh
- Includes Bangladeshi public holidays

### dim_geography
- Hierarchical location data (Division > District > Upazila)
- Standardized location names and codes
- Geographic attributes and classifications

## Key Fact Tables

### fct_enrollments
- Tracks student enrollments in schools
- Includes enrollment status and academic information
- Links to student, school, and time dimensions

### fct_attendances
- Daily student attendance records
- Tracks presence, absences, and reasons
- Supports attendance rate calculations

## Naming Conventions

- **Tables/Views**: `[prefix]_[entity]_[context]`
  - `dim_` for dimensions
  - `fct_` for fact tables
  - `stg_` for staging tables
  - `marts_` for data marts

- **Columns**:
  - `_id` for natural/business keys
  - `_key` for surrogate keys
  - `_at` for timestamps
  - `_date` for dates
  - `is_` for boolean flags
  - `total_` for aggregated measures

## Getting Started

1. Install dbt and configure your profiles.yml
2. Run `dbt deps` to install dependencies
3. Run `dbt run` to build the models
4. Run `dbt test` to validate the data
5. Generate documentation with `dbt docs generate` and `dbt docs serve`

## Best Practices

- Always document new models in `schema.yml`
- Add tests for critical business logic
- Use incremental models for large fact tables
- Follow the established naming conventions
- Keep transformations idempotent
