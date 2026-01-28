# Budget Planner

An AI-powered budget planning app that automatically categorizes and analyzes your spending using local LLMs. Built with Claude Code, Python Flask backend, React frontend, and Ollama for intelligent transaction categorization.

> **📊 Technical Comparison**: See detailed architecture comparison with budget_cursor (FastAPI implementation) at [github.com/bdmckean/code_off](https://github.com/bdmckean/code_off)

## ✨ Key Features

### 🤖 AI-Powered Auto-Categorization
- **Smart Suggestions**: Uses Ollama with Llama 3.1 to automatically suggest categories for transactions
- **Learns from History**: Improves suggestions based on your previous categorizations
- **Batch Processing**: Processes up to 5 transactions at once for 5x faster categorization
- **Context-Aware**: Analyzes transaction description, amount, and date for accurate suggestions

### 📊 Budget Management
- **File Upload**: Support for CSV and JSON transaction files
- **Interactive Mapping**: Review and adjust AI suggestions with easy-to-use interface
- **Progress Saving**: Automatically saves progress to `mapping_progress.json`
- **Resume Support**: Continue from where you left off when uploading the same file
- **Dynamic Categories**: Add custom categories on-the-fly during mapping
- **Review Screen**: Review all mappings before finalizing

### 📈 Analytics & Insights
- **Real-time Stats**: View category breakdown and mapping progress
- **Analytics Dashboard**: Detailed spending analysis with charts and trends
- **Category Insights**: Track spending patterns across categories

### 🔍 LLM Monitoring (Optional)
- **Langfuse Integration**: Monitor LLM performance and token usage
- **Prompt Tracking**: Track and optimize categorization prompts
- **Performance Metrics**: Analyze response times and accuracy

### 🐳 Docker Ready
- **One-Command Deploy**: Run the entire stack with Docker Compose
- **Local LLM Support**: Configured to work with local Ollama instance

## Quick Start with Docker

### Prerequisites
- **Docker and Docker Compose** installed
- **Ollama** installed and running ([Install guide](https://ollama.ai))
- **Llama 3.1 model** downloaded: `ollama pull llama3.1:8b`

### Setup

1. **Configure Ollama** (if using Docker):
   ```bash
   # Ollama should be running on your host machine
   ollama serve
   ```

2. **Set up environment variables** (optional for basic usage):
   ```bash
   cd backend
   cp .env.example .env  # If available, or create .env

   # Edit .env with your configuration:
   # OLLAMA_API_URL=http://host.docker.internal:11434
   # OLLAMA_MODEL=llama3.1:8b
   ```

3. **Start the application**:
   ```bash
   # From the project root
   docker-compose up --build

   # The app will be available at:
   # Frontend: http://localhost:3000
   # Backend: http://localhost:5000/api
   ```

4. **First-time setup**: The app will create `mapping_progress.json` and `file_mappings.json` automatically

### Development without Docker

#### Prerequisites
- Python 3.9+
- Node.js and npm
- Poetry (`pip install poetry`)
- Ollama installed and running with `llama3.1:8b` model

#### Backend Setup
```bash
# Install dependencies
poetry install

# Set up environment variables
cd backend
cp .env.example .env  # Or create .env manually

# Edit backend/.env with required variables:
# OLLAMA_API_URL=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b
#
# Optional - for Langfuse monitoring:
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_HOST=http://localhost:3001

# Start Ollama (in another terminal)
ollama serve

# Run the Flask app
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
2. **AI Categorization**:
   - Click "Get AI Suggestion" for intelligent category recommendations
   - Or use "Bulk AI Categorize" to process multiple transactions at once (5x faster!)
   - The AI learns from your previous categorizations for better accuracy
3. **Review & Adjust**: Accept AI suggestions or manually select categories from the dropdown
4. **Add Custom Categories**: Create new categories on-the-fly if needed
5. **Track Progress**: View real-time progress bar and category breakdown in the sidebar
6. **Review Screen**: Review all your mappings before finalizing
7. **Analytics**: View detailed spending insights in the Analytics dashboard
8. **Resume Anytime**: Progress is auto-saved - upload the same file to continue later

## Project Structure

```
budget_claude/
├── backend/
│   ├── app.py                  # Flask application with LLM integration
│   ├── langfuse_tracer.py      # Langfuse tracing module for LLM monitoring
│   ├── categories.json         # Dynamic category storage
│   ├── .env                    # Environment variables (create from .env.example)
│   └── Dockerfile              # Docker configuration for backend
├── frontend/
│   ├── public/
│   │   └── index.html          # HTML template
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   ├── App.css             # Main styles
│   │   ├── components/
│   │   │   ├── FileUpload.js       # File upload component
│   │   │   ├── MappingInterface.js # Transaction mapping UI with AI
│   │   │   ├── ReviewScreen.js     # Review all mappings
│   │   │   ├── Stats.js            # Real-time statistics
│   │   │   └── Analytics.js        # Analytics dashboard
│   │   └── index.js            # React entry point
│   ├── package.json            # npm dependencies
│   └── Dockerfile              # Docker configuration for frontend
├── docker-compose.yml          # Docker Compose configuration
├── pyproject.toml              # Poetry configuration with dependencies
├── mapping_progress.json       # Progress tracking (auto-generated)
├── file_mappings.json          # File mapping history (auto-generated)
├── README.md                   # This file
├── LANGFUSE_INTEGRATION.md     # Langfuse setup and monitoring guide
├── BATCH_PROMPT_CHANGES.md     # Batch processing implementation details
└── SETUP.md                    # Detailed setup instructions
```

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check endpoint
- `GET /api/categories` - Get available budget categories
- `POST /api/add-category` - Add a new custom category
- `POST /api/confirm-add-category` - Confirm adding a new category

### File & Progress Management
- `POST /api/upload` - Upload a CSV/JSON file for processing
- `GET /api/progress` - Get current mapping progress for uploaded file
- `POST /api/reset-file` - Reset progress for current file

### Transaction Mapping
- `POST /api/map-row` - Manually map a transaction to a category
- `POST /api/suggest-category` - Get AI suggestion for a single transaction
- `POST /api/bulk-map` - Batch process multiple transactions with AI (5 at a time)

### Analytics & Stats
- `GET /api/stats` - Get real-time mapping statistics
- `GET /api/analytics` - Get detailed analytics and spending insights

## Budget Categories

### Default Categories
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

**Note**: You can add custom categories dynamically during the mapping process!

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

## Environment Variables

Create a `backend/.env` file with the following variables:

### Required (for AI features)
```bash
# Ollama Configuration
OLLAMA_API_URL=http://host.docker.internal:11434  # Use localhost:11434 for local dev
OLLAMA_MODEL=llama3.1:8b
```

### Optional (for LLM monitoring)
```bash
# Langfuse Tracing
LANGFUSE_PUBLIC_KEY=pk-lf-your-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-here
LANGFUSE_HOST=http://localhost:3001
```

See `LANGFUSE_INTEGRATION.md` for detailed setup instructions for LLM monitoring.

## AI Features & How It Works

### Intelligent Categorization
The app uses Ollama with Llama 3.1 to provide context-aware categorization suggestions:

1. **Context Building**: Analyzes transaction description, amount, and date
2. **Learning from History**: Uses up to 100 previous categorizations as examples
3. **Smart Prompting**: Constructs prompts that guide the LLM for accurate suggestions
4. **Validation**: Ensures suggested categories match your available categories

### Batch Processing
Process 5 transactions at once for 5x faster categorization:
- Single transaction: ~2-3 seconds per item
- Batch processing: ~4-6 seconds for 5 items
- Maintains consistency across similar transactions
- See `BATCH_PROMPT_CHANGES.md` for implementation details

### Performance
- **Local LLM**: All processing happens locally with Ollama (privacy-friendly)
- **No Cloud Costs**: Uses your own hardware, no API fees
- **Customizable**: Works with any Ollama-compatible model

## LLM Monitoring with Langfuse (Optional)

Track and optimize your LLM performance:
- Monitor token usage and costs
- Analyze prompt effectiveness
- Track response times and latency
- Debug categorization issues
- View detailed traces of AI decisions

**Setup**: See `LANGFUSE_INTEGRATION.md` for complete setup guide.

## Additional Documentation

- **[LANGFUSE_INTEGRATION.md](LANGFUSE_INTEGRATION.md)** - Complete guide to LLM monitoring setup
- **[BATCH_PROMPT_CHANGES.md](BATCH_PROMPT_CHANGES.md)** - Batch processing implementation details
- **[SETUP.md](SETUP.md)** - Detailed setup instructions

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if not running
ollama serve

# Verify model is downloaded
ollama list
```

### AI Suggestions Not Working
1. Ensure Ollama is running: `ollama serve`
2. Check the model is downloaded: `ollama pull llama3.1:8b`
3. Verify environment variables in `backend/.env`
4. Check backend logs for errors

### Docker Issues
```bash
# Ensure Ollama is accessible from Docker
# Use host.docker.internal instead of localhost in OLLAMA_API_URL

# Restart containers
docker-compose down
docker-compose up --build
```

## Technologies Used

- **Backend**: Python 3.9+, Flask, Flask-CORS
- **Frontend**: React, JavaScript
- **LLM**: Ollama with Llama 3.1 (8B parameters)
- **Monitoring**: Langfuse (optional)
- **Package Management**: Poetry (Python), npm (JavaScript)
- **Containerization**: Docker & Docker Compose

## License

MIT
