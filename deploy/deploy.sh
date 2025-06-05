#!/bin/bash

# Deployment script for Bangladesh Student Data Analytics

# Configuration
DOCKER_REGISTRY="your-registry.com"
PROJECT_NAME="student-analytics"
DEPLOY_ENV=$1
VERSION=$2

# Validate input
if [ -z "$DEPLOY_ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: $0 <environment> <version>"
    echo "Environments: development, staging, production"
    exit 1
fi

# Load environment variables
if [ -f ".env.$DEPLOY_ENV" ]; then
    source ".env.$DEPLOY_ENV"
else
    echo "Environment file .env.$DEPLOY_ENV not found!"
    exit 1
fi

# Function to deploy using docker-compose
deploy_compose() {
    local env=$1
    echo "Deploying to $env environment..."

    # Build and tag the image
    docker-compose build
    docker tag bdren-student-analytics:latest $DOCKER_REGISTRY/$PROJECT_NAME:$VERSION

    # Push to registry
    docker push $DOCKER_REGISTRY/$PROJECT_NAME:$VERSION

    # Deploy using appropriate compose file
    if [ "$env" == "production" ]; then
        docker-compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    docker-compose exec app python src/data_processing/run_migrations.py
}

# Function to verify deployment
verify_deployment() {
    echo "Verifying deployment..."
    local attempts=0
    local max_attempts=30

    while [ $attempts -lt $max_attempts ]; do
        if curl -s http://localhost:${PORT:-8000}/health | grep -q "ok"; then
            echo "Deployment verified successfully!"
            return 0
        fi
        attempts=$((attempts + 1))
        sleep 2
    done

    echo "Deployment verification failed!"
    return 1
}

# Main deployment sequence
echo "Starting deployment to $DEPLOY_ENV environment..."

# Backup database if production
if [ "$DEPLOY_ENV" == "production" ]; then
    echo "Creating database backup..."
    docker-compose exec db pg_dump -U $DB_USER $DB_NAME > "backups/backup_$(date +%Y%m%d_%H%M%S).sql"
fi

# Deploy
deploy_compose $DEPLOY_ENV

# Run migrations if not production (production migrations should be manual)
if [ "$DEPLOY_ENV" != "production" ]; then
    run_migrations
fi

# Verify deployment
verify_deployment

echo "Deployment completed successfully!"
