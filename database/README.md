# Database Setup

This directory contains scripts for setting up and initializing the database for the Student Performance Dashboard.

## Prerequisites

- PostgreSQL 13+
- Python 3.10+
- psql command-line tool
- Python packages: `python-dotenv`

## Setup Instructions

1. **Install PostgreSQL**
   - [Download and install PostgreSQL](https://www.postgresql.org/download/)
   - Make sure the `psql` command-line tool is in your PATH

2. **Create a Database**
   ```bash
   createdb -U postgres student_data_db
   ```

3. **Set Up Environment Variables**
   Copy the `.env` file from the project root and update the database credentials:
   ```bash
   cp ../.env.example ../.env
   ```
   
   Update the following variables in `.env`:
   ```
   POSTGRES_SERVER=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=student_data_db
   ```

4. **Install Python Dependencies**
   ```bash
   pip install python-dotenv
   ```

5. **Initialize the Database**
   Run the initialization script:
   ```bash
   python init_db.py
   ```
   
   This will:
   - Create all necessary tables
   - Insert sample data
   - Create useful views

## Database Schema

The database includes the following tables:

- `classes`: Information about classes
- `students`: Student information
- `subjects`: Available subjects
- `teachers`: Teacher information
- `courses`: Course offerings (links subjects to classes and teachers)
- `grades`: Student grades for courses

## Sample Data

The database is populated with sample data including:

- 6 classes (1A, 1B, 2A, 2B, 3A, 3B)
- 5 subjects (Math, English, Science, Bangla, Social Studies)
- 5 teachers
- 20 students (distributed across classes)
- Grades for all students in their respective classes

## Views

1. `student_performance_view`: Aggregated student performance data
2. `class_performance_view`: Aggregated class performance data

## Connecting to the Database

Use the following connection string in your application:

```
postgresql://username:password@localhost:5432/student_data_db
```

## Troubleshooting

- **Connection Issues**: Ensure PostgreSQL is running and the credentials in `.env` are correct
- **Permission Denied**: Make sure the database user has the necessary permissions
- **Script Errors**: Check the logs for specific error messages

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
