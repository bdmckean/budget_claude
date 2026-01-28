# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Budget Planner is a full-stack application for categorizing and analyzing financial transactions. It uses Flask (Python) backend with React frontend, and integrates with Ollama (local LLM) for AI-powered transaction categorization.

## Development Commands

### Running the Application

**With Docker (recommended):**
```bash
docker-compose up --build
# Frontend: http://localhost:3002
# Backend: http://localhost:5001/api
```

**Local development:**
```bash
# Backend
poetry install
poetry run python backend/app.py

# Frontend (in separate terminal)
cd frontend
npm install
npm start
```

### Testing
```bash
# Run batch prompt test
python test_batch_prompt.py

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Python formatting and linting
poetry run black backend/
poetry run flake8 backend/
```

## Architecture

### Backend (Flask API)

**Main Application: `backend/app.py`**
- Core Flask application with CORS enabled
- Persistent state stored in JSON files at project root:
  - `mapping_progress.json` - Current session state (rows, mappings, file info)
  - `file_mappings.json` - Historical mappings across all files
  - `backend/categories.json` - Available budget categories
- Key endpoints:
  - `/api/upload` - Upload CSV/JSON, validate rows, restore previous mappings
  - `/api/suggest-category` - Single transaction categorization via LLM
  - `/api/bulk-map` - Batch categorization (processes 5 transactions at a time)
  - `/api/map-row` - Confirm user mapping
  - `/api/analytics` - Spending analysis by category and month

**LLM Integration:**
- Uses Ollama API (llama3.1:8b model) for categorization
- Two prompt strategies:
  - `build_llm_prompt()` - Single transaction (2-3 seconds)
  - `build_batch_llm_prompt()` - Batch of up to 5 transactions (4-6 seconds total, 5x faster)
- Both prompts include up to 100 previous categorization examples for context learning
- Temperature: 0.3 (consistent, deterministic results)

**Langfuse Tracing: `backend/langfuse_tracer.py`**
- Optional LLM observability integration
- Traces all categorization operations with:
  - Full prompt/response (truncated intelligently for large content)
  - Token usage and latency
  - Validation and error tracking
- Gracefully degrades when not configured (check .env for LANGFUSE_PUBLIC_KEY)
- Flush traces after operations to ensure they're sent to Langfuse server

**File Hash System:**
- `get_file_mapping_hash()` creates SHA256 hash of file contents
- Detects if re-uploaded file has changed
- Restores previous mappings for unchanged files

### Frontend (React)

**Component Structure:**
- `App.js` - Main orchestration, state management, API calls
- `FileUpload.js` - CSV/JSON upload handler
- `MappingInterface.js` - Row-by-row categorization UI
- `ReviewScreen.js` - Bulk categorization review interface
- `Analytics.js` - Spending visualization by month/category
- `Stats.js` - Progress and category breakdown sidebar

**State Management:**
- All state managed in App.js (no Redux)
- Progress tracked locally and synced with backend
- API proxy configured in package.json for local dev

### Data Flow

1. **Upload Phase:**
   - User uploads CSV/JSON file
   - Backend validates rows (must have Date, Amount, Description)
   - Backend calculates file hash and checks for previous mappings
   - If file unchanged, restores previous progress
   - Skips incomplete rows (logged in backend console)

2. **Categorization Phase:**
   - **Manual:** User selects category per row (traditional flow)
   - **AI Suggestion:** Click "Suggest" → calls `/api/suggest-category`
   - **Bulk AI:** Click "AI Categorize All" → calls `/api/bulk-map`
     - Backend batches unmapped rows into groups of 5
     - Each batch gets single LLM call with structured prompt
     - Returns suggestions for user review
     - User must confirm each suggestion before it's saved

3. **Learning System:**
   - Every confirmed mapping adds to `previous_mappings` context
   - LLM sees recent examples in future prompts
   - Improves consistency within a session

4. **Analytics Phase:**
   - `/api/analytics` aggregates mapped transactions
   - Groups by month (format: "YYYY-MM")
   - Excludes Payment/Credit/Refund types
   - Converts amounts to absolute values

## Key Patterns

### Batch Processing (5 at a time)
The system uses optimized batch processing for bulk operations:
- Batches of 5 rows per LLM call (vs 1 row per call)
- Structured response format: `Row <idx>: <CATEGORY>`
- 60-second timeout per batch (vs 30 for single)
- Parsing logic validates all categories against available list
- See `BATCH_PROMPT_CHANGES.md` for detailed implementation

### Error Handling
- LLM connection errors: Graceful degradation, user-friendly messages
- Invalid category responses: Logged but not saved, user sees error
- Incomplete CSV rows: Skipped silently, count returned in upload response
- Langfuse tracing failures: Silent (prints to console, doesn't break app)

### File State Management
- Progress auto-saves on every confirmed mapping
- File hash prevents accidental data loss on re-upload
- Reset endpoint (`/api/reset-file`) clears mappings but preserves row data

## Environment Configuration

**Backend `.env` file (not in repo):**
```bash
# Ollama (Required for AI features)
OLLAMA_API_URL=http://host.docker.internal:11434  # Docker
# OLLAMA_API_URL=http://localhost:11434  # Local
OLLAMA_MODEL=llama3.1:8b

# Langfuse (Optional - for LLM tracing)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3001
```

**Docker Networking:**
- Backend uses `host.docker.internal` to reach host's Ollama
- Frontend proxies API requests to backend via port 5001

## File Formats

**CSV Requirements:**
```csv
Date,Amount,Description
12/30/2024,-45.50,Gas Station
01/02/2025,25.00,Grocery Store
```

**JSON Format:**
```json
[
  {
    "Transaction Date": "12/30/2024",
    "Amount": "-45.50",
    "Description": "Gas Station"
  }
]
```

**Field Variations Supported:**
- Date fields: `Date`, `Transaction Date`, `date`
- Amount: `Amount`, `amount`
- Description: `Description`, `description`

## Testing Considerations

- Sample data: `sample_transactions.csv` (included)
- Test incomplete rows: `test_incomplete_rows.csv`
- Backend runs on port 5000 locally, 5001 in Docker
- Frontend runs on port 3000 locally, 3002 in Docker
- Ensure Ollama is running before testing AI features: `ollama serve`

## Common Development Tasks

**Adding a new category:**
- Edit `backend/categories.json` directly, or
- Use frontend "Add Category" button (validates and auto-corrects)

**Modifying LLM prompts:**
- Single: `build_llm_prompt()` in backend/app.py:70-113
- Batch: `build_batch_llm_prompt()` in backend/app.py:116-175

**Debugging LLM issues:**
- Check Langfuse dashboard at http://localhost:3001
- Look for traces: `suggest_category`, `bulk_map`, `process_batch`
- Review prompt/response, token usage, errors

**Changing batch size:**
- Modify `batch_size = 5` in `/api/bulk-map` endpoint (backend/app.py:923)
- Update timeout proportionally (currently 60s for 5 items)

## Known Limitations

- No user authentication (single-user system)
- Progress files stored locally (not multi-user safe)
- Ollama must be running locally or accessible via network
- Large files (>10k rows) may be slow in batch processing
- CSV parsing expects standard format (commas, quoted strings)
