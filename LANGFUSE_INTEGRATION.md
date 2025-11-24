# Langfuse Integration - budget_claude

This document describes the Langfuse tracing integration for the budget_claude application.

## Overview

The budget_claude application now includes comprehensive tracing of all LLM (Large Language Model) operations using Langfuse. This allows monitoring, debugging, and analysis of:

- Transaction categorization requests
- LLM prompts and responses
- Token usage and performance metrics
- Error tracking and debugging
- Batch processing operations

## What Was Added

### 1. Environment Configuration

**File: `backend/.env`**

Added Langfuse and Ollama configuration variables:
```bash
# Langfuse Tracing Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=http://localhost:3001

# Ollama Configuration
OLLAMA_API_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1:8b
```

### 2. Tracing Module

**File: `backend/langfuse_tracer.py`**

A new module that provides:
- `LangfuseTracer` class: Main interface for Langfuse integration
- `get_tracer()`: Get the global tracer instance
- `initialize_tracing()`: Initialize tracing at app startup

**Key Methods:**
- `create_trace()`: Create a new trace for monitoring operations
- `add_generation()`: Log LLM API calls
- `add_span()`: Log non-LLM operations (data processing, validation, etc.)
- `trace_llm_call()`: Decorator for automatic tracing

**Features:**
- Graceful degradation: Works without Langfuse if not configured
- Automatic error handling: Won't break the app if tracing fails
- Environment-based configuration: Uses .env variables

### 3. Updated Dependencies

**File: `pyproject.toml`**

Added langfuse dependency:
```toml
langfuse = "^2.0.0"
```

Install with:
```bash
poetry install
```

### 4. Integrated Tracing in Flask App

**File: `backend/app.py`**

#### Initialization
```python
from langfuse_tracer import get_tracer, initialize_tracing

# At app startup
initialize_tracing()
tracer = get_tracer()
```

#### Updated Endpoints

**`GET /api/suggest-category`** - Single transaction categorization
- Creates a trace for the request
- Logs: request parsing, category loading, LLM call details, validation results
- Traces any errors encountered

**`POST /api/bulk-map`** - Batch transaction categorization
- Creates a parent trace for the bulk operation
- Creates sub-traces for each row processing
- Logs: operation start, individual row processing, completion stats

#### Updated LLM Function

**`get_llm_suggestion()`**
- Added optional `trace` parameter
- Logs prompt building, LLM response, token usage
- Logs validation results and errors
- Includes transaction description in metadata

## How Tracing Works

### Single Transaction Categorization

When you call `/api/suggest-category`:

```
Trace: suggest_category
├── Span: parse_request (metadata: row_index, description)
├── Span: load_context (metadata: categories_count, mappings_count)
├── Span: build_prompt (metadata: prompt_length)
├── Generation: ollama_categorization (LLM call)
│   ├── Input: Full prompt
│   ├── Output: LLM response
│   └── Usage: prompt_tokens, completion_tokens
├── Span: validation_success (or validation_error)
└── Span: categorization_success (or categorization_failed)
```

### Bulk Categorization

When you call `/api/bulk-map`:

```
Trace: bulk_map
├── Span: bulk_operation_start (metadata: unmapped_count)
├── Trace: process_row (for each row)
│   ├── Span: build_prompt
│   ├── Generation: ollama_categorization
│   └── Span: validation_success/error
└── Span: bulk_operation_complete (stats: total, successful, failed)
```

## Metadata Included in Traces

Each trace includes contextual metadata:

- **Row Data**: Transaction description, date, amount
- **Model Info**: Model name, temperature, parameters
- **Tokens**: Prompt and completion token counts
- **Performance**: Latency, processing time
- **Status**: Success/failure, error types
- **Context**: Number of example mappings, categories available

## Error Tracking

Errors are automatically captured with:
- Error type
- Error message
- Stack trace context
- Request/operation details

This helps debug issues and understand failure patterns.

## Configuration Steps

### 1. Setup Langfuse Server

Ensure the shared Langfuse server is running (see `/path/to/budget_tracing/README.md`):

```bash
cd ../budget_tracing
docker-compose up -d
```

### 2. Generate API Keys

1. Open http://localhost:3001
2. Sign up with any email/password
3. Create a project named "budget_claude"
4. Generate API keys (Public and Secret)

### 3. Update .env File

Edit `backend/.env` with your keys:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-abc123...
LANGFUSE_SECRET_KEY=sk-lf-xyz789...
LANGFUSE_HOST=http://localhost:3001
```

### 4. Install Dependencies

```bash
poetry install
```

### 5. Start the Application

```bash
python backend/app.py
```

Or with the startup script:
```bash
./start.sh
```

## Accessing Traces

### In Langfuse Dashboard

1. Open http://localhost:3001
2. Select "budget_claude" project
3. Click "Traces" in the sidebar
4. You'll see traces as they come in:
   - `suggest_category` - Single categorizations
   - `bulk_map` - Batch operations
   - `process_row` - Individual rows in batch

### Trace Details

Each trace shows:
- **Timeline**: Chronological view of all operations
- **Token Usage**: Prompt and completion tokens
- **Latency**: How long each operation took
- **Metadata**: Transaction info, model parameters, etc.
- **Status**: Success/failure indicators

### Filtering

Filter traces by:
- Trace name (suggest_category, bulk_map, etc.)
- Time range
- Status (success/failed)
- Model used
- Custom metadata fields

## Performance Considerations

### Overhead

Tracing has minimal overhead:
- ~5-10ms per trace creation
- Non-blocking: Traces are sent asynchronously
- Won't slow down your application

### Graceful Degradation

If Langfuse is not available:
- Application works normally
- Errors are logged to console
- No traces are created, but functionality is preserved

### Disabling Tracing

To disable tracing without changing code:
- Remove `LANGFUSE_PUBLIC_KEY` from `.env`
- The tracer will detect this and disable itself
- No performance impact

## Example: Reading Traces

### Via Langfuse Dashboard

1. Navigate to http://localhost:3001
2. Open the "budget_claude" project
3. Click on a trace (e.g., "suggest_category")
4. View the detailed timeline:

```
suggest_category (450ms total)
├── parse_request (2ms)
├── load_context (25ms)
├── ollama_categorization (418ms)
│   Prompt tokens: 245
│   Completion tokens: 3
│   Model: llama3.1:8b
└── validation_success (5ms)
```

### Via API

Langfuse provides REST APIs to query traces programmatically. See https://docs.langfuse.com/

## Troubleshooting

### Traces Not Appearing

**Problem**: Traces not showing in Langfuse dashboard

**Solutions**:
1. Check API keys in `.env`:
   ```bash
   echo $LANGFUSE_PUBLIC_KEY
   echo $LANGFUSE_SECRET_KEY
   ```

2. Verify Langfuse is running:
   ```bash
   curl http://localhost:3001/api/health
   ```

3. Check application logs for errors:
   ```bash
   tail -f logs/app.log
   ```

4. Verify correct project is selected in dashboard

### Langfuse Connection Errors

**Problem**: "Could not connect to Langfuse"

**Solutions**:
1. Ensure Langfuse server is running:
   ```bash
   docker-compose ps  # from budget_tracing directory
   ```

2. Check LANGFUSE_HOST in `.env`:
   ```bash
   # If running locally:
   LANGFUSE_HOST=http://localhost:3001
   ```

3. Check firewall/network connectivity:
   ```bash
   curl -v http://localhost:3001/api/health
   ```

### High Latency on LLM Calls

**Problem**: LLM calls taking longer than expected

**Use traces to debug**:
1. Open the trace in Langfuse
2. Check token counts (high tokens = longer processing)
3. Verify Ollama is running: `ollama serve`
4. Check system resources: `top`, `Activity Monitor`

## Next Steps

1. **Monitor Performance**: Watch Langfuse dashboard for patterns
2. **Optimize Prompts**: Use trace data to refine prompts
3. **Track Costs**: Monitor token usage over time
4. **Set Alerts**: Configure alerts for high error rates
5. **Analyze Patterns**: Identify categories that need improvement

## Integration with budget_cursor

The same tracing setup can be applied to budget_cursor. See `/path/to/budget_tracing/INTEGRATION_GUIDE.md` for details.

## Documentation

- **Langfuse Docs**: https://docs.langfuse.com/
- **Budget Tracing Setup**: See `../budget_tracing/README.md`
- **Integration Guide**: See `../budget_tracing/INTEGRATION_GUIDE.md`

## Support

For issues or questions:
1. Check Langfuse documentation: https://docs.langfuse.com/
2. Review traces in the Langfuse dashboard
3. Check application logs in `logs/` directory
4. Review the integration code in `backend/langfuse_tracer.py`
