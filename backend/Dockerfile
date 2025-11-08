FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy poetry files from root
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root --no-directory

# Copy application code
COPY backend/ ./

# Expose port
EXPOSE 5000

# Run the app
CMD ["poetry", "run", "python", "app.py"]
