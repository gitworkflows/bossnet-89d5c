# Student Performance Dashboard

An interactive dashboard for analyzing student performance metrics.

## Features

- Interactive filters for class, gender, and performance thresholds
- Visualizations including histograms, box plots, and trend analysis
- Data table with sorting and filtering capabilities
- Responsive design that works on different screen sizes

## Prerequisites

- Python 3.10+
- PostgreSQL database
- Required Python packages (install using `pip install -r requirements.txt`)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd BossNET-1/dashboards/student_performance
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the database connection:
   - Copy `.env.example` to `.env`
   - Update the database connection string in `.env`

4. Run the dashboard:
   ```bash
   streamlit run app.py
   ```

5. Open your browser and navigate to `http://localhost:8501`

## Development

### Project Structure

- `app.py` - Main dashboard application
- `requirements.txt` - Python dependencies
- `README.md` - This file

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
DATABASE_URL=postgresql://username:password@localhost:5432/student_data_db
```

### Running Tests

```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
