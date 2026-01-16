import os
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import re
import requests
from dotenv import load_dotenv

from langfuse_tracer import get_tracer, initialize_tracing

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Langfuse tracing
initialize_tracing()
tracer = get_tracer()

# Ollama configuration
# Use host.docker.internal to reach host's Ollama from Docker container
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://host.docker.internal:11434')
OLLAMA_MODEL = 'llama3.1:8b'

# Configuration
PROGRESS_FILE = Path(__file__).parent.parent / "mapping_progress.json"
CATEGORIES_FILE = Path(__file__).parent / "categories.json"
FILE_MAPPINGS_FILE = Path(__file__).parent.parent / "file_mappings.json"


def load_categories():
    """Load categories from file"""
    if CATEGORIES_FILE.exists():
        with open(CATEGORIES_FILE, 'r') as f:
            return json.load(f)
    return []


def save_categories(categories):
    """Save categories to file"""
    with open(CATEGORIES_FILE, 'w') as f:
        json.dump(categories, f, indent=2)


def load_file_mappings():
    """Load file mappings history"""
    if FILE_MAPPINGS_FILE.exists():
        with open(FILE_MAPPINGS_FILE, 'r') as f:
            return json.load(f)
    return {"mappings": {}}


def save_file_mappings(mappings):
    """Save file mappings to file"""
    with open(FILE_MAPPINGS_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)


def get_file_mapping_hash(rows):
    """Create a hash of file contents to detect changes"""
    import hashlib
    # Use the sorted row data to create a hash
    content = json.dumps(rows, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def build_llm_prompt(transaction_data, categories, previous_mappings):
    """
    Build a prompt for the LLM to suggest a category.

    Args:
        transaction_data: Dict with transaction details (Date, Amount, Description, etc.)
        categories: List of available budget categories
        previous_mappings: List of {date, amount, description, category} examples

    Returns:
        Prompt string for the LLM
    """
    # Build examples from previous mappings (up to 100 most recent)
    examples = ""
    if previous_mappings:
        examples = "\nHere are examples of previous categorizations:\n"
        # Use up to 100 examples
        for mapping in previous_mappings[-100:]:
            date = mapping.get('date', 'N/A')
            amount = mapping.get('amount', 'N/A')
            description = mapping.get('description', '')
            category = mapping.get('category', 'N/A')
            examples += f"- Date: {date} | Amount: {amount} | Description: \"{description}\" → {category}\n"

    # Build categories list
    categories_str = ", ".join(categories)

    # Build the full prompt
    prompt = f"""You are a budget categorization assistant. Based on transaction details, suggest the most appropriate budget category.

Available Categories: {categories_str}

{examples}

Current Transaction to Categorize:
- Date: {transaction_data.get('Date', 'N/A')}
- Amount: {transaction_data.get('Amount', 'N/A')}
- Description: {transaction_data.get('Description', 'N/A')}

Based on the description, amount, and available categories, respond with ONLY the category name that best matches this transaction. Do not include any explanation, just the category name.

Category: """

    return prompt


def build_batch_llm_prompt(transaction_batch, categories, previous_mappings):
    """
    Build a prompt for batch categorization (up to 5 transactions at a time).

    Args:
        transaction_batch: List of tuples (idx, transaction_data) for up to 5 transactions
        categories: List of available budget categories
        previous_mappings: List of {date, amount, description, category} examples

    Returns:
        Prompt string for the LLM with structured batch output format
    """
    # Build examples from previous mappings (up to 100 most recent)
    examples = ""
    if previous_mappings:
        examples = "\nHere are examples of previous categorizations:\n"
        # Use up to 100 examples
        for mapping in previous_mappings[-100:]:
            date = mapping.get('date', 'N/A')
            amount = mapping.get('amount', 'N/A')
            description = mapping.get('description', '')
            category = mapping.get('category', 'N/A')
            examples += f"- Date: {date} | Amount: {amount} | Description: \"{description}\" → {category}\n"

    # Build categories list
    categories_str = ", ".join(categories)

    # Build transactions list with row indices
    transactions_str = ""
    for idx, transaction_data in transaction_batch:
        date = transaction_data.get('Date', transaction_data.get('Transaction Date', 'N/A'))
        amount = transaction_data.get('Amount', 'N/A')
        description = transaction_data.get('Description', 'N/A')
        transactions_str += f"Row {idx}: Date: {date} | Amount: {amount} | Description: \"{description}\"\n"

    # Build the full prompt for batch processing
    prompt = f"""You are a budget categorization assistant. Based on transaction details, suggest the most appropriate budget category for each transaction.

Available Categories: {categories_str}

{examples}

Transactions to Categorize (batch processing):
{transactions_str}

For each transaction above, provide the category in the following format:
Row {transaction_batch[0][0]}: <CATEGORY_NAME>
Row {transaction_batch[1][0]}: <CATEGORY_NAME>
...(continue for each row)

Rules:
- Respond with ONLY the row and category mapping
- Do not include any explanation
- Each line must be in the format: Row <number>: <CATEGORY_NAME>
- Use the exact category names from the available list
- Process all transactions

Categories: """

    return prompt


def get_llm_suggestion(transaction_data, categories, previous_mappings, trace=None):
    """
    Get a category suggestion from Ollama/Llama 3.1.

    Args:
        transaction_data: Dict with transaction details
        categories: List of available budget categories
        previous_mappings: List of previous categorizations for context
        trace: Optional Langfuse trace object for monitoring

    Returns:
        Dict with suggested category and confidence
    """
    try:
        prompt = build_llm_prompt(transaction_data, categories, previous_mappings)

        # Add span for prompt building
        if trace:
            tracer.add_span(
                trace,
                name="build_prompt",
                output_text=f"Prompt built ({len(prompt)} chars)",
                metadata={"prompt_length": len(prompt)}
            )

        response = requests.post(
            f'{OLLAMA_API_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False,
                'temperature': 0.3  # Lower temperature for more consistent results
            },
            timeout=30
        )

        if response.status_code != 200:
            if trace:
                tracer.add_span(
                    trace,
                    name="ollama_error",
                    input_text=f"Status {response.status_code}",
                    metadata={"error": True, "status_code": response.status_code}
                )
            return {
                'success': False,
                'error': f'Ollama API error: {response.status_code}',
                'suggestion': None
            }

        response_data = response.json()
        response_text = response_data.get('response', '').strip()

        # Log the LLM generation
        if trace:
            tracer.add_generation(
                trace,
                name="ollama_categorization",
                model=OLLAMA_MODEL,
                input_text=prompt,
                output_text=response_text,
                usage={
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "completion_tokens": response_data.get("eval_count", 0),
                },
                metadata={
                    "temperature": 0.3,
                    "ollama_host": OLLAMA_API_URL,
                    "transaction_description": transaction_data.get("Description", "")
                }
            )

        # Clean up the response - remove extra whitespace and quotes
        suggestion = response_text.strip().strip('"\'')

        # Validate that suggestion is one of the available categories
        if suggestion not in categories:
            # Try to find a close match (case-insensitive)
            for cat in categories:
                if cat.lower() == suggestion.lower():
                    suggestion = cat
                    break
            else:
                # No match found, return error
                if trace:
                    tracer.add_span(
                        trace,
                        name="validation_error",
                        input_text=f"Invalid category: {suggestion}",
                        output_text="Validation failed",
                        metadata={"error": True, "suggested": suggestion}
                    )
                return {
                    'success': False,
                    'error': f'LLM suggested invalid category: {suggestion}',
                    'suggestion': None
                }

        # Log successful categorization
        if trace:
            tracer.add_span(
                trace,
                name="validation_success",
                input_text=f"Validated category: {suggestion}",
                output_text="Validation passed",
                metadata={"category": suggestion}
            )

        return {
            'success': True,
            'suggestion': suggestion,
            'error': None
        }

    except requests.exceptions.ConnectionError:
        if trace:
            tracer.add_span(
                trace,
                name="connection_error",
                input_text="Ollama connection",
                output_text=f"Failed to connect to {OLLAMA_API_URL}",
                metadata={"error": True, "error_type": "ConnectionError"}
            )
        return {
            'success': False,
            'error': 'Could not connect to Ollama. Make sure Ollama is running on ' + OLLAMA_API_URL,
            'suggestion': None
        }
    except Exception as e:
        if trace:
            tracer.add_span(
                trace,
                name="unexpected_error",
                input_text=type(e).__name__,
                output_text=str(e),
                metadata={"error": True, "error_type": type(e).__name__}
            )
        return {
            'success': False,
            'error': str(e),
            'suggestion': None
        }


def get_batch_llm_suggestions(transaction_batch, categories, previous_mappings, trace=None):
    """
    Get category suggestions for a batch of transactions (up to 5 at a time).

    Args:
        transaction_batch: List of tuples (idx, transaction_data) for up to 5 transactions
        categories: List of available budget categories
        previous_mappings: List of previous categorizations for context
        trace: Optional Langfuse trace object for logging

    Returns:
        Dict with mapping of idx -> {'success': bool, 'suggestion': str or None, 'error': str or None}
    """
    results = {}

    try:
        prompt = build_batch_llm_prompt(transaction_batch, categories, previous_mappings)

        response = requests.post(
            f'{OLLAMA_API_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False,
                'temperature': 0.3  # Lower temperature for more consistent results
            },
            timeout=60  # Batch processing takes longer (60 seconds for 5 items)
        )

        if response.status_code != 200:
            error_msg = f'Ollama API error: {response.status_code}'

            # Log the failed LLM call to Langfuse
            if trace:
                tracer.add_generation(
                    trace,
                    name="batch_categorization",
                    model=OLLAMA_MODEL,
                    input_text=prompt,
                    output_text="",
                    metadata={
                        "error": True,
                        "status_code": response.status_code,
                        "batch_size": len(transaction_batch)
                    }
                )

            # Return error for all items in batch
            for idx, _ in transaction_batch:
                results[idx] = {
                    'success': False,
                    'error': error_msg,
                    'suggestion': None
                }
            return results

        response_text = response.json().get('response', '').strip()

        # Log the successful LLM call to Langfuse
        if trace:
            tracer.add_generation(
                trace,
                name="batch_categorization",
                model=OLLAMA_MODEL,
                input_text=prompt,
                output_text=response_text,
                metadata={
                    "success": True,
                    "batch_size": len(transaction_batch),
                    "response_length": len(response_text)
                }
            )

        # Log progress for this batch
        batch_indices = [idx for idx, _ in transaction_batch]
        print(f"LLM batch processed: rows {batch_indices[0]}-{batch_indices[-1]} ({len(transaction_batch)} items)", flush=True)

        # Parse batch response - expect lines in format: "Row <idx>: <CATEGORY>"
        lines = response_text.split('\n')
        parsed_suggestions = {}

        for line in lines:
            line = line.strip()
            if not line or not line.startswith('Row'):
                continue

            try:
                # Parse "Row <idx>: <CATEGORY>" format
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue

                row_part = parts[0].strip()  # "Row <idx>"
                category_part = parts[1].strip()  # "<CATEGORY>"

                # Extract row index
                row_idx = row_part.replace('Row', '').strip()
                row_idx = int(row_idx)

                # Clean up category
                suggestion = category_part.strip().strip('"\'')

                # Validate category
                if suggestion not in categories:
                    # Try case-insensitive match
                    for cat in categories:
                        if cat.lower() == suggestion.lower():
                            suggestion = cat
                            break
                    else:
                        # Invalid category, skip this one
                        parsed_suggestions[row_idx] = None
                        continue

                parsed_suggestions[row_idx] = suggestion
            except (ValueError, IndexError):
                continue

        # Build results for all items in batch
        for idx, _ in transaction_batch:
            if idx in parsed_suggestions and parsed_suggestions[idx]:
                results[idx] = {
                    'success': True,
                    'suggestion': parsed_suggestions[idx],
                    'error': None
                }
            else:
                results[idx] = {
                    'success': False,
                    'error': f'LLM did not provide valid category for row {idx}',
                    'suggestion': None
                }

        return results

    except requests.exceptions.ConnectionError:
        error_msg = 'Could not connect to Ollama. Make sure Ollama is running on ' + OLLAMA_API_URL
        for idx, _ in transaction_batch:
            results[idx] = {
                'success': False,
                'error': error_msg,
                'suggestion': None
            }
        return results
    except Exception as e:
        error_msg = str(e)
        for idx, _ in transaction_batch:
            results[idx] = {
                'success': False,
                'error': error_msg,
                'suggestion': None
            }
        return results


def validate_and_correct_category(category_name):
    """
    Validate and correct category name.
    Returns dict with:
    - original: original input
    - corrected: corrected version
    - has_corrections: boolean
    - corrections: list of corrections made
    """
    corrections = []
    corrected = category_name.strip()

    # Check for empty input
    if not corrected:
        return {
            "original": category_name,
            "corrected": corrected,
            "has_corrections": True,
            "corrections": ["Category name cannot be empty"]
        }

    # Check length
    if len(corrected) > 50:
        corrections.append(f"Truncated from {len(corrected)} to 50 characters")
        corrected = corrected[:50]

    # Capitalize properly (Title Case)
    words = corrected.split()
    capitalized_words = []
    for word in words:
        # Handle special cases like "& "
        if word == "&":
            capitalized_words.append(word)
        else:
            capitalized_words.append(word.capitalize())

    corrected_capitalized = " ".join(capitalized_words)

    if corrected != corrected_capitalized:
        corrections.append(f"Capitalization: '{corrected}' → '{corrected_capitalized}'")
        corrected = corrected_capitalized

    # Remove special characters except common ones (spaces, &, -, /)
    cleaned = re.sub(r'[^a-zA-Z0-9\s&\-/]', '', corrected)
    if cleaned != corrected:
        corrections.append(f"Removed invalid characters: '{corrected}' → '{cleaned}'")
        corrected = cleaned

    return {
        "original": category_name,
        "corrected": corrected,
        "has_corrections": len(corrections) > 0,
        "corrections": corrections
    }


def is_row_valid(row):
    """
    Check if a CSV row has the minimum required fields populated.

    Args:
        row: Dictionary representing a CSV row

    Returns:
        Boolean indicating if row is valid (has required fields)
    """
    # Check for common field names (handle variations)
    date_field = row.get('Date') or row.get('Transaction Date') or row.get('date')
    description_field = row.get('Description') or row.get('description')
    amount_field = row.get('Amount') or row.get('amount')

    # Row is valid if all required fields are present and non-empty
    if not date_field or not str(date_field).strip():
        return False
    if not description_field or not str(description_field).strip():
        return False
    if not amount_field or not str(amount_field).strip():
        return False

    return True


def load_progress():
    """Load existing progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        "file_name": None,
        "rows": {},
        "total_rows": 0,
        "last_updated": None
    }


def save_progress(progress_data):
    """Save progress to file"""
    progress_data["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of budget categories"""
    categories = load_categories()
    # Sort alphabetically (case-insensitive)
    categories.sort(key=str.lower)
    return jsonify({"categories": categories}), 200


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get current progress"""
    progress = load_progress()
    return jsonify(progress), 200


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parse CSV/Excel"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Initialize skipped count
        skipped_count = 0

        # Read file content - check extensions case-insensitively
        filename_lower = file.filename.lower()
        if filename_lower.endswith('.csv'):
            import csv
            lines = file.read().decode('utf-8').split('\n')
            reader = csv.DictReader(lines)
            all_rows = list(reader)
            # Filter out invalid rows (missing required fields)
            rows = [row for row in all_rows if is_row_valid(row)]
            skipped_count = len(all_rows) - len(rows)
            if skipped_count > 0:
                print(f"Skipped {skipped_count} incomplete row(s) from CSV", flush=True)
        elif filename_lower.endswith('.json'):
            all_rows = json.loads(file.read().decode('utf-8'))
            # Filter out invalid rows
            rows = [row for row in all_rows if is_row_valid(row)]
            skipped_count = len(all_rows) - len(rows)
            if skipped_count > 0:
                print(f"Skipped {skipped_count} incomplete row(s) from JSON", flush=True)
        else:
            return jsonify({"error": "Unsupported file format. Use CSV or JSON"}), 400

        # Get file mapping history
        file_mappings = load_file_mappings()
        file_hash = get_file_mapping_hash(rows)

        # Initialize or update progress
        progress = load_progress()
        progress["file_name"] = file.filename
        progress["total_rows"] = len(rows)

        # Check if we have previous mappings for this file
        if file.filename in file_mappings["mappings"]:
            previous_mapping = file_mappings["mappings"][file.filename]
            # Check if file content has changed
            if previous_mapping.get("file_hash") == file_hash:
                # File unchanged - restore previous mappings and skip mapped rows
                previous_rows = previous_mapping.get("rows", {})
                restored_count = 0
                for idx, row in enumerate(rows):
                    row_key = str(idx)
                    if row_key in previous_rows:
                        # Restore previous mapping
                        progress["rows"][row_key] = {
                            "data": row,
                            "category": previous_rows[row_key],
                            "mapped": True
                        }
                        restored_count += 1
                    else:
                        # New or unmapped row
                        progress["rows"][row_key] = {
                            "data": row,
                            "category": None,
                            "mapped": False
                        }
                print(f"Restored {restored_count} previously mapped rows for '{file.filename}'", flush=True)
            else:
                # File changed - reset all mappings
                file_mappings["mappings"][file.filename] = {
                    "file_hash": file_hash,
                    "rows": {}
                }
                for idx, row in enumerate(rows):
                    row_key = str(idx)
                    progress["rows"][row_key] = {
                        "data": row,
                        "category": None,
                        "mapped": False
                    }
        else:
            # New file - initialize all rows as unmapped
            file_mappings["mappings"][file.filename] = {
                "file_hash": file_hash,
                "rows": {}
            }
            for idx, row in enumerate(rows):
                row_key = str(idx)
                progress["rows"][row_key] = {
                    "data": row,
                    "category": None,
                    "mapped": False
                }

        save_progress(progress)
        save_file_mappings(file_mappings)

        response_data = {
            "success": True,
            "file_name": file.filename,
            "total_rows": len(rows),
            "progress": progress
        }

        # Build informational messages
        messages = []

        # Add restored mappings info
        if file.filename in file_mappings["mappings"]:
            previous_mapping = file_mappings["mappings"][file.filename]
            if previous_mapping.get("file_hash") == file_hash:
                restored_count = len([r for r in progress["rows"].values() if r.get("mapped")])
                if restored_count > 0:
                    messages.append(f"Restored {restored_count} previously mapped row(s)")

        # Add skipped count info if any rows were skipped
        if skipped_count > 0:
            response_data["skipped_rows"] = skipped_count
            messages.append(f"Skipped {skipped_count} incomplete row(s)")

        if messages:
            response_data["message"] = " • ".join(messages)

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/suggest-category', methods=['POST'])
def suggest_category():
    """Suggest a category using LLM based on transaction data"""
    # Create a trace for this operation
    trace = tracer.create_trace(
        name="suggest_category",
        metadata={"endpoint": "/api/suggest-category"}
    )

    try:
        data = request.json
        row_index = data.get('row_index')
        transaction_data = data.get('transaction_data', {})

        # Log the request
        if trace:
            tracer.add_span(
                trace,
                name="parse_request",
                metadata={
                    "row_index": row_index,
                    "description": transaction_data.get("Description", "")
                }
            )

        # Load categories and progress
        categories = load_categories()
        progress = load_progress()

        if not categories:
            if trace:
                tracer.add_span(
                    trace,
                    name="no_categories_error",
                    output_text="No categories available",
                    metadata={"error": True}
                )
            return jsonify({
                "error": "No categories available",
                "suggestion": None
            }), 400

        # Get previous mappings as examples (mapped rows) - include full details
        previous_mappings = []
        if progress.get("rows"):
            for row_data in progress["rows"].values():
                if row_data.get("mapped") and row_data.get("category"):
                    previous_mappings.append({
                        "date": row_data["data"].get("Date", ""),
                        "amount": row_data["data"].get("Amount", ""),
                        "description": row_data["data"].get("Description", ""),
                        "category": row_data["category"]
                    })

        if trace:
            tracer.add_span(
                trace,
                name="load_context",
                metadata={
                    "categories_count": len(categories),
                    "previous_mappings_count": len(previous_mappings)
                }
            )

        # Get LLM suggestion
        result = get_llm_suggestion(transaction_data, categories, previous_mappings, trace=trace)

        if result['success']:
            if trace:
                tracer.add_span(
                    trace,
                    name="categorization_success",
                    output_text=f"Categorized as: {result['suggestion']}",
                    metadata={"category": result['suggestion']}
                )
            return jsonify({
                "success": True,
                "suggestion": result['suggestion'],
                "row_index": row_index
            }), 200
        else:
            if trace:
                tracer.add_span(
                    trace,
                    name="categorization_failed",
                    output_text=result['error'],
                    metadata={"error": True}
                )
            return jsonify({
                "success": False,
                "error": result['error'],
                "suggestion": None
            }), 500
    except Exception as e:
        print(f"Error in suggest_category: {str(e)}", flush=True)
        if trace:
            tracer.add_span(
                trace,
                name="exception",
                input_text=type(e).__name__,
                output_text=str(e),
                metadata={"error": True, "error_type": type(e).__name__}
            )
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "suggestion": None
        }), 500
    finally:
        # Flush the trace
        if tracer.is_enabled():
            try:
                tracer.client.flush()
            except Exception:
                pass


@app.route('/api/bulk-map', methods=['POST'])
def bulk_map():
    """Bulk map all unmapped rows using AI with batch processing"""
    # Create a trace for bulk operation
    trace = tracer.create_trace(
        name="bulk_map",
        metadata={"endpoint": "/api/bulk-map"}
    )

    try:
        progress = load_progress()
        rows = progress.get("rows", {})
        categories = load_categories()

        if not categories:
            if trace:
                tracer.add_span(
                    trace,
                    name="no_categories",
                    output_text="No categories available",
                    metadata={"error": True}
                )
            return jsonify({
                "success": False,
                "error": "No categories available"
            }), 400

        # Find unmapped rows
        unmapped_indices = [
            idx for idx, row_data in rows.items()
            if not row_data.get("mapped", False)
        ]

        if not unmapped_indices:
            if trace:
                tracer.add_span(
                    trace,
                    name="all_mapped",
                    output_text="No unmapped rows",
                    metadata={"unmapped_count": 0}
                )
            return jsonify({
                "success": True,
                "message": "All items already mapped",
                "mappings": {},
                "unmapped_count": 0,
                "progress": {"current": 0, "total": 0}
            }), 200

        # Get previous mappings for context
        previous_mappings = []
        for row_data in rows.values():
            if row_data.get("mapped") and row_data.get("category"):
                previous_mappings.append({
                    "date": row_data["data"].get("Transaction Date", ""),
                    "amount": row_data["data"].get("Amount", ""),
                    "description": row_data["data"].get("Description", ""),
                    "category": row_data["category"]
                })

        if trace:
            tracer.add_span(
                trace,
                name="bulk_operation_start",
                metadata={
                    "total_unmapped": len(unmapped_indices),
                    "context_mappings": len(previous_mappings)
                }
            )

        # Process in batches of 5 rows
        mappings = {}
        batch_size = 5
        total_rows = len(unmapped_indices)
        processed_count = 0

        # Create batches of 5 rows each
        for batch_start in range(0, len(unmapped_indices), batch_size):
            batch_end = min(batch_start + batch_size, len(unmapped_indices))
            batch_indices = unmapped_indices[batch_start:batch_end]

            # Create batch of (idx, transaction_data) tuples
            transaction_batch = [
                (idx, rows[idx].get("data", {}))
                for idx in batch_indices
            ]

            # Create a trace for this batch
            batch_trace = tracer.create_trace(
                name="process_batch",
                metadata={
                    "batch_start": batch_start,
                    "batch_size": len(batch_indices),
                    "row_indices": batch_indices
                }
            )

            # Get batch suggestions using optimized batch prompt
            batch_results = get_batch_llm_suggestions(transaction_batch, categories, previous_mappings, trace=batch_trace)

            # Flush the batch trace to send it to Langfuse
            if batch_trace and tracer.is_enabled():
                try:
                    tracer.client.flush()
                except Exception as e:
                    print(f"Warning: Failed to flush batch trace: {e}", flush=True)

            # Process batch results
            for idx, result_info in batch_results.items():
                transaction_data = rows[idx].get("data", {})
                processed_count += 1

                if result_info.get('success') and result_info.get('suggestion'):
                    mappings[idx] = {
                        "data": transaction_data,
                        "suggestion": result_info['suggestion'],
                        "confirmed": False
                    }

                    # Add to previous mappings for context in future batches
                    previous_mappings.append({
                        "date": transaction_data.get("Transaction Date", ""),
                        "amount": transaction_data.get("Amount", ""),
                        "description": transaction_data.get("Description", ""),
                        "category": result_info['suggestion']
                    })
                else:
                    mappings[idx] = {
                        "data": transaction_data,
                        "suggestion": None,
                        "error": result_info.get('error', 'Unknown error'),
                        "confirmed": False
                    }

                # Log progress
                progress_pct = (processed_count / total_rows) * 100
                print(f"Bulk map progress: {processed_count}/{total_rows} ({progress_pct:.0f}%)", flush=True)

        if trace:
            tracer.add_span(
                trace,
                name="bulk_operation_complete",
                output_text=f"Generated suggestions for {len(mappings)} items",
                metadata={
                    "total_processed": len(mappings),
                    "successful": sum(1 for m in mappings.values() if m.get('suggestion')),
                    "failed": sum(1 for m in mappings.values() if not m.get('suggestion'))
                }
            )

        return jsonify({
            "success": True,
            "message": f"Generated suggestions for {len(mappings)} items",
            "mappings": mappings,
            "unmapped_count": len(unmapped_indices),
            "progress": {"current": total_rows, "total": total_rows}
        }), 200

    except Exception as e:
        print(f"Error in bulk_map: {str(e)}", flush=True)
        if trace:
            tracer.add_span(
                trace,
                name="exception",
                input_text=type(e).__name__,
                output_text=str(e),
                metadata={"error": True}
            )
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500
    finally:
        # Flush the trace
        if tracer.is_enabled():
            try:
                tracer.client.flush()
            except Exception:
                pass


@app.route('/api/add-category', methods=['POST'])
def add_category():
    """Add a new custom category"""
    data = request.json
    category_name = data.get('category_name', '').strip()

    if not category_name:
        return jsonify({"error": "Category name is required"}), 400

    # Validate and correct the category
    validation = validate_and_correct_category(category_name)

    # Load current categories
    categories = load_categories()

    # Check if category already exists (case-insensitive)
    category_lower = validation["corrected"].lower()
    for cat in categories:
        if cat.lower() == category_lower:
            return jsonify({
                "error": f"Category '{validation['corrected']}' already exists",
                "validation": validation
            }), 400

    # Return validation result for user confirmation
    return jsonify({
        "validation": validation,
        "action": "confirm" if validation["has_corrections"] else "add"
    }), 200


@app.route('/api/confirm-add-category', methods=['POST'])
def confirm_add_category():
    """Confirm and add the category after user approval"""
    data = request.json
    corrected_category = data.get('category', '').strip()

    if not corrected_category:
        return jsonify({"error": "Category name is required"}), 400

    # Load current categories
    categories = load_categories()

    # Check if category already exists
    category_lower = corrected_category.lower()
    for cat in categories:
        if cat.lower() == category_lower:
            return jsonify({"error": f"Category '{corrected_category}' already exists"}), 400

    # Add new category
    categories.append(corrected_category)
    # Sort alphabetically (case-insensitive)
    categories.sort(key=str.lower)
    save_categories(categories)

    return jsonify({
        "success": True,
        "message": f"Category '{corrected_category}' added successfully",
        "categories": categories
    }), 201


@app.route('/api/map-row', methods=['POST'])
def map_row():
    """Map a row to a category"""
    data = request.json
    row_idx = data.get('row_index')
    category = data.get('category')

    categories = load_categories()
    if category not in categories:
        return jsonify({"error": "Invalid category"}), 400

    progress = load_progress()
    row_key = str(row_idx)

    if row_key not in progress["rows"]:
        return jsonify({"error": "Row not found"}), 404

    progress["rows"][row_key]["category"] = category
    progress["rows"][row_key]["mapped"] = True

    save_progress(progress)

    # Also save to file mappings if file is set
    if progress.get("file_name"):
        file_mappings = load_file_mappings()
        file_name = progress["file_name"]

        # Get current file hash from progress or preserve existing
        rows_data = [row_data.get("data", {}) for row_data in progress["rows"].values()]
        current_file_hash = get_file_mapping_hash(rows_data)

        if file_name not in file_mappings["mappings"]:
            file_mappings["mappings"][file_name] = {
                "file_hash": current_file_hash,
                "rows": {}
            }
        else:
            # Update hash if not set
            if not file_mappings["mappings"][file_name].get("file_hash"):
                file_mappings["mappings"][file_name]["file_hash"] = current_file_hash

        file_mappings["mappings"][file_name]["rows"][row_key] = category
        save_file_mappings(file_mappings)

    return jsonify({
        "success": True,
        "row_index": row_idx,
        "category": category,
        "progress": progress
    }), 200


@app.route('/api/reset-file', methods=['POST'])
def reset_file():
    """Reset all mappings for the current file"""
    data = request.json
    file_name = data.get('file_name')

    if not file_name:
        return jsonify({"error": "file_name is required"}), 400

    # Remove file mappings
    file_mappings = load_file_mappings()
    if file_name in file_mappings["mappings"]:
        del file_mappings["mappings"][file_name]
        save_file_mappings(file_mappings)

    # Clear progress rows for this file but keep rows data
    progress = load_progress()
    if progress.get("file_name") == file_name:
        for row in progress["rows"].values():
            row["category"] = None
            row["mapped"] = False
        save_progress(progress)

    return jsonify({
        "success": True,
        "message": f"Reset all mappings for {file_name}",
        "progress": progress
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get mapping statistics"""
    progress = load_progress()
    rows = progress.get("rows", {})

    total = len(rows)
    mapped = sum(1 for row in rows.values() if row.get("mapped", False))

    category_counts = {}
    for row in rows.values():
        if row.get("mapped"):
            cat = row.get("category")
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return jsonify({
        "total_rows": total,
        "mapped_rows": mapped,
        "remaining_rows": total - mapped,
        "category_breakdown": category_counts,
        "file_name": progress.get("file_name"),
        "last_updated": progress.get("last_updated")
    }), 200


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get spending analytics by category and month"""
    try:
        progress = load_progress()
        rows = progress.get("rows", {})

        # Dictionary to store spending by month and category
        # Format: {"2024-11": {"Food & Groceries": 100.50, ...}, ...}
        spending_by_month = {}

        for row_data in rows.values():
            # Only process mapped rows
            if not row_data.get("mapped"):
                continue

            row_info = row_data.get("data", {})
            category = row_data.get("category")
            amount_str = row_info.get("Amount", "0")
            date_str = row_info.get("Transaction Date", "")
            transaction_type = row_info.get("Type", "").lower()

            # Parse amount
            try:
                amount = float(amount_str)
            except (ValueError, TypeError):
                continue

            # Skip payments/credits based on Type field or category
            # Check Type field if present (e.g., "Payment", "Credit")
            if transaction_type in ['payment', 'credit', 'refund']:
                continue

            # Skip if categorized as Payment
            if category and category.lower() == 'payment':
                continue

            # Convert to absolute value for spending
            # (handles both positive and negative expense formats)
            amount = abs(amount)

            # Skip zero amounts
            if amount == 0:
                continue

            # Parse date - expect format like "12/30/2024"
            if not date_str:
                continue

            try:
                date_parts = date_str.split('/')
                if len(date_parts) == 3:
                    month = date_parts[0]
                    day = date_parts[1]
                    year = date_parts[2]
                    month_key = f"{year}-{month:0>2}"  # Format as "2024-12"
                else:
                    continue
            except:
                continue

            # Initialize month if not exists
            if month_key not in spending_by_month:
                spending_by_month[month_key] = {}

            # Initialize category if not exists
            if category not in spending_by_month[month_key]:
                spending_by_month[month_key][category] = 0

            # Add to spending
            spending_by_month[month_key][category] += amount

        # Calculate totals by category across all months
        category_totals = {}
        for month_data in spending_by_month.values():
            for category, amount in month_data.items():
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += amount

        # Sort months chronologically
        sorted_months = sorted(spending_by_month.keys())
        sorted_spending = {month: spending_by_month[month] for month in sorted_months}

        return jsonify({
            "success": True,
            "spending_by_month": sorted_spending,
            "category_totals": category_totals,
            "months": sorted_months
        }), 200

    except Exception as e:
        print(f"Error in get_analytics: {str(e)}", flush=True)
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
