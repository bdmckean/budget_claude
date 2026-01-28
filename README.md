# Budget Planner

A budget planning app that helps you categorize and analyze your spending. Built with Claude Code, Python Flask backend, and React frontend.

## Features

- **File Upload**: Upload CSV or JSON files with transaction data
- **Interactive Mapping**: Map each transaction row to a budget category
- **Progress Saving**: Automatically saves progress to `mapping_progress.json` in the repo
- **Resume Support**: If interrupted, simply upload the same file again to continue from where you left off
- **Real-time Stats**: View category breakdown and mapping progress
- **Docker Ready**: Run the entire app with Docker Compose

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed

### Running the App

```bash
# Start both frontend and backend
docker-compose up --build

# The app will be available at:
# Frontend: http://localhost:3002
# Backend: http://localhost:5001/api
```

### Development without Docker

#### Backend Setup
```bash
# Install dependencies
poetry install

# Run the Flask app
cd backend
poetry run python app.py
# Backend will be available at http://localhost:5000
```

#### Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Run the React app
npm start
# Frontend will open at http://localhost:3000
```

## How to Use

1. **Upload a File**: Click "Choose File" and select a CSV or JSON file with transaction data
2. **Map Transactions**: For each row, select the appropriate budget category from the options
3. **Track Progress**: View the progress bar and category breakdown in the sidebar
4. **Resume Later**: If you need to stop, simply upload the same file again to continue mapping

## Project Structure

```
budget_claude/
├── backend/
│   ├── app.py              # Flask application
│   ├── .env                # Environment variables
│   ├── Dockerfile          # Docker configuration for backend
│   └── requirements (via Poetry)
├── frontend/
│   ├── public/
│   │   └── index.html      # HTML template
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── components/     # React components
│   │   └── index.js        # React entry point
│   ├── package.json        # npm dependencies
│   └── Dockerfile          # Docker configuration for frontend
├── docker-compose.yml      # Docker Compose configuration
├── pyproject.toml         # Poetry configuration
└── mapping_progress.json   # Progress tracking file (auto-generated)
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/categories` - Get available budget categories
- `GET /api/progress` - Get current mapping progress
- `POST /api/upload` - Upload a CSV/JSON file
- `POST /api/map-row` - Map a row to a category
- `GET /api/stats` - Get mapping statistics

## Budget Categories

- Food & Groceries
- Transportation
- Entertainment
- Utilities
- Healthcare
- Shopping
- Subscriptions
- Savings
- Investments
- Other

## File Format

### CSV Format
```
Date,Amount,Description
2024-01-01,25.50,Grocery Store
2024-01-02,45.00,Gas Station
```

### JSON Format
```json
[
  {"Date": "2024-01-01", "Amount": "25.50", "Description": "Grocery Store"},
  {"Date": "2024-01-02", "Amount": "45.00", "Description": "Gas Station"}
]
```

## License

MIT
