import os
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
PROGRESS_FILE = Path(__file__).parent.parent / "mapping_progress.json"
BUDGET_CATEGORIES = [
    "Food & Groceries",
    "Transportation",
    "Entertainment",
    "Utilities",
    "Healthcare",
    "Shopping",
    "Subscriptions",
    "Savings",
    "Investments",
    "Other"
]


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
    return jsonify({"categories": BUDGET_CATEGORIES}), 200


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
        # Read file content
        if file.filename.endswith('.csv'):
            import csv
            lines = file.read().decode('utf-8').split('\n')
            reader = csv.DictReader(lines)
            rows = list(reader)
        elif file.filename.endswith('.json'):
            rows = json.loads(file.read().decode('utf-8'))
        else:
            return jsonify({"error": "Unsupported file format. Use CSV or JSON"}), 400

        # Initialize or update progress
        progress = load_progress()
        progress["file_name"] = file.filename
        progress["total_rows"] = len(rows)

        # Initialize rows if not already mapped
        for idx, row in enumerate(rows):
            row_key = str(idx)
            if row_key not in progress["rows"]:
                progress["rows"][row_key] = {
                    "data": row,
                    "category": None,
                    "mapped": False
                }

        save_progress(progress)

        return jsonify({
            "success": True,
            "file_name": file.filename,
            "total_rows": len(rows),
            "progress": progress
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/map-row', methods=['POST'])
def map_row():
    """Map a row to a category"""
    data = request.json
    row_idx = data.get('row_index')
    category = data.get('category')

    if category not in BUDGET_CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400

    progress = load_progress()
    row_key = str(row_idx)

    if row_key not in progress["rows"]:
        return jsonify({"error": "Row not found"}), 404

    progress["rows"][row_key]["category"] = category
    progress["rows"][row_key]["mapped"] = True

    save_progress(progress)

    return jsonify({
        "success": True,
        "row_index": row_idx,
        "category": category,
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
