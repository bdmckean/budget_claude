# Setup Guide

## Option 1: Run with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Available ports: 3000 (frontend), 5000 (backend)

### Steps
1. Clone the repository and navigate to the project directory
2. Run the following command:
   ```bash
   docker-compose up --build
   ```
3. Open your browser and go to `http://localhost:3000`
4. Your backend API will be available at `http://localhost:5000/api`

### Stopping the App
```bash
docker-compose down
```

### Viewing Logs
```bash
docker-compose logs -f
```

## Option 2: Run Locally (Development)

### Prerequisites
- Python 3.9+
- Node.js 18+
- Poetry (for Python dependency management)

### Backend Setup

1. Install Python dependencies:
   ```bash
   poetry install
   ```

2. Start the Flask backend:
   ```bash
   poetry run python backend/app.py
   ```

   The backend will be available at `http://localhost:5000/api`

### Frontend Setup

1. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the React development server:
   ```bash
   npm start
   ```

   The frontend will open automatically at `http://localhost:3000`

## Testing the App

### Using the Sample File
A sample transactions file is included: `sample_transactions.csv`

1. Open the app at `http://localhost:3000`
2. Click "Choose File" and select `sample_transactions.csv`
3. Start mapping transactions to categories
4. Your progress is automatically saved to `mapping_progress.json`

### Creating Your Own Test File
Create a CSV or JSON file with your transaction data:

**CSV Format:**
```csv
Date,Amount,Description
2024-01-01,25.50,Grocery Store
2024-01-02,45.00,Gas Station
2024-01-03,100.00,Monthly Subscription
```

**JSON Format:**
```json
[
  {"Date": "2024-01-01", "Amount": "25.50", "Description": "Grocery Store"},
  {"Date": "2024-01-02", "Amount": "45.00", "Description": "Gas Station"}
]
```

## Key Features

### Progress Saving
- All mapping progress is automatically saved to `mapping_progress.json` in the root directory
- This file is committed to git, allowing you to track progress across sessions
- If interrupted, upload the same file again to resume from where you left off

### Progress File Structure
```json
{
  "file_name": "transactions.csv",
  "total_rows": 10,
  "rows": {
    "0": {
      "data": {"Date": "...", "Amount": "...", "Description": "..."},
      "category": "Food & Groceries",
      "mapped": true
    },
    "1": {
      "data": {"Date": "...", "Amount": "...", "Description": "..."},
      "category": null,
      "mapped": false
    }
  },
  "last_updated": "2024-01-01T12:00:00.000000"
}
```

## Troubleshooting

### Port Already in Use
If port 3000 or 5000 is already in use:

**Docker:**
Edit `docker-compose.yml` and change the ports:
```yaml
ports:
  - "3001:3000"  # Change 3000 to another port
  - "5001:5000"  # Change 5000 to another port
```

**Local:**
Start the backend on a different port:
```bash
FLASK_ENV=development poetry run python -c "from backend.app import app; app.run(port=5001)"
```

And update the API URL in the React frontend (in `frontend/src/App.js`).

### CORS Issues
The backend is configured with Flask-CORS to allow requests from the frontend. If you see CORS errors:
1. Ensure both services are running
2. Check that the API URL in the frontend matches the backend URL
3. In Docker, ensure services are on the same network (they are by default)

### File Upload Issues
- Ensure the file is in CSV or JSON format
- For CSV files, ensure they have a header row with column names
- File size should be reasonable (tested up to 10,000+ rows)

## Development Tips

### Modifying the Backend
- Edit `backend/app.py` to add new API endpoints
- No restart needed with Docker (volume mounts watch for changes)
- For local development, restart with `poetry run python backend/app.py`

### Modifying the Frontend
- Edit files in `frontend/src/`
- Changes hot-reload automatically in development mode
- Run `npm run build` to create a production build

### Adding Budget Categories
Edit the `BUDGET_CATEGORIES` list in `backend/app.py`:
```python
BUDGET_CATEGORIES = [
    "Food & Groceries",
    "Transportation",
    # ... add more categories here
]
```

## Next Steps

Consider these enhancements:
- Add CSV export of categorized transactions
- Implement a suggestion engine (ML-based category suggestions)
- Add transaction search and filtering
- Create visualizations of spending by category
- Add multi-file handling
- Implement user authentication for multiple users
