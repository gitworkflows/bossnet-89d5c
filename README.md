# Bangladesh Student Data Analytics Project

## Overview

A comprehensive data analysis system for educational data in Bangladesh, integrating various data sources to provide insights into student performance, demographics, and educational trends.

## Project Structure

```
student-data-bangladesh/
├── data/                  # Data storage
│   ├── raw_data/         # Original source data
│   └── processed_data/   # Cleaned and transformed data
├── src/                  # Source code
├── notebooks/            # Jupyter notebooks
├── tests/               # Test suites
├── docs/                # Documentation
└── deploy/              # Deployment configurations
```

## Features

- Secure JWT-based authentication
- Role-based access control (Admin, Teacher, Staff, Student)
- Data collection from multiple educational sources
- Automated data processing and validation
- Statistical analysis and modeling
- Interactive visualizations and dashboards
- RESTful API with OpenAPI documentation
- Comprehensive monitoring and reporting

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/student-data-bangladesh.git
   cd student-data-bangladesh
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

5. Set up the database:
   ```bash
   # Create database in PostgreSQL
   createdb student_data_db
   
   # Run migrations
   alembic upgrade head
   
   # Or initialize database directly
   python scripts/init_db.py
   ```

6. Run the development server:
   ```bash
   python run_api.py
   ```
   The API will be available at http://localhost:8000

### API Documentation

Once the server is running, you can access:

- Interactive API documentation: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

### Authentication

1. Get an access token:
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/api/v1/auth/token' \
     -H 'accept: application/json' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'grant_type=password&username=admin&password=admin123'
   ```

2. Use the access token in subsequent requests:
   ```
   Authorization: Bearer <access_token>
   ```

### Running Tests

```bash
pytest
```

## Development

- Follow the [Contributing Guidelines](CONTRIBUTING.md)
- Check [Documentation](docs/) for detailed information
- Review [Deployment Guide](docs/deployment.md) for deployment instructions

## Architecture

- Python-based data processing pipeline
- PostgreSQL for data storage
- Redis for caching
- FastAPI for REST API
- Kubernetes for production deployment
- Prometheus/Grafana for monitoring

## Data Sources

- BANBEIS (Bangladesh Bureau of Educational Information and Statistics)
- Education Board Results
- DSHE (Directorate of Secondary and Higher Education)
- DPE (Directorate of Primary Education)
- BBS (Bangladesh Bureau of Statistics)

## Security

- Comprehensive data privacy measures
- Role-based access control
- Encrypted sensitive data
- Regular security audits

## Deployment

### Development (Docker Compose)

1. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```

2. Run database migrations:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

3. Access the API at http://localhost:8000

### Production (Recommended)

For production deployment, it's recommended to use:

1. A production-grade ASGI server like Uvicorn with Gunicorn
2. A reverse proxy like Nginx
3. Process manager like Systemd or Supervisor
4. Container orchestration with Kubernetes for high availability

See [Deployment Guide](docs/deployment.md) for detailed production deployment instructions.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | `postgresql://postgres:postgres@db:5432/student_data_db` |
| `SECRET_KEY` | Secret key for JWT tokens | `your-secret-key-change-in-production` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time in minutes | `30` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Monitoring

- Real-time performance monitoring
- Custom educational metrics
- Automated alerting system
- Regular performance reports

## Contributing

1. Fork the repository
2. Create your feature branch
3. Follow coding standards
4. Submit a pull request

See [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation

## Acknowledgments

- Ministry of Education, Bangladesh
- Educational institutions
- Contributing developers and researchers
