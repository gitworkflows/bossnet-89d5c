#!/bin/bash
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "Database is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    python src/data_processing/run_migrations.py
}

# Function to collect static files (if needed)
collect_static() {
    echo "Collecting static files..."
    # Add your static file collection command here if needed
}

# Main initialization sequence
init_app() {
    wait_for_db
    wait_for_redis

    if [ "$ENVIRONMENT" != "production" ]; then
        run_migrations
    fi

    collect_static
}

# Execute initialization
init_app

# Execute the main command
exec "$@"
