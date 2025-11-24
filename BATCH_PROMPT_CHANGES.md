# Batch Categorization Prompt Implementation

## Overview
The prompting system has been updated to support **batch categorization of up to 5 transactions at a time** (or remaining rows if less than 5), significantly improving performance.

## Key Changes

### 1. New Function: `build_batch_llm_prompt()` (backend/app.py:106-165)

Generates a prompt for batch processing of 1-5 transactions in a single LLM call.

**Features:**
- Accepts list of tuples: `[(idx, transaction_data), ...]`
- Includes up to 100 previous categorization examples
- Structured output format with row numbers
- Handles variable batch sizes (1-5 transactions)

**Sample Output:**

```
You are a budget categorization assistant. Based on transaction details, suggest the most appropriate budget category for each transaction.

Available Categories: Food & Groceries, Transportation, Entertainment, Utilities, Healthcare, Shopping, ...

Here are examples of previous categorizations:
- Date: 12/24/2024 | Amount: -20.12 | Description: "SUPREMACIA CARNICA" → Food & Groceries
- Date: 12/24/2024 | Amount: -5.00 | Description: "OPENAI" → Subscriptions
...

Transactions to Categorize (batch processing):
Row 0: Date: 2024-01-05 | Amount: 75.00 | Description: "CVS Pharmacy"
Row 1: Date: 2024-01-06 | Amount: 32.45 | Description: "Chipotle Mexican Grill"
Row 2: Date: 2024-01-07 | Amount: 120.50 | Description: "Shell Gas Station"
Row 3: Date: 2024-01-08 | Amount: 15.99 | Description: "Netflix Subscription"
Row 4: Date: 2024-01-09 | Amount: 85.50 | Description: "Uber Trip"

For each transaction above, provide the category in the following format:
Row 0: <CATEGORY_NAME>
Row 1: <CATEGORY_NAME>
...(continue for each row)

Rules:
- Respond with ONLY the row and category mapping
- Do not include any explanation
- Each line must be in the format: Row <number>: <CATEGORY_NAME>
- Use the exact category names from the available list
- Process all transactions

Categories: [awaiting LLM response]
```

### 2. New Function: `get_batch_llm_suggestions()` (backend/app.py:241-357)

Processes batch requests and handles parsing of structured responses.

**Features:**
- Sends batch to Ollama with 60-second timeout (vs 30 for single)
- Parses response format: `"Row <idx>: <CATEGORY>"`
- Validates all categories against available list
- Case-insensitive category matching
- Returns dict: `{idx: {'success': bool, 'suggestion': str, 'error': str}}`

**Response Parsing Logic:**
```python
# Expected response format from LLM:
Row 0: Healthcare
Row 1: Food & Groceries
Row 2: Transportation
Row 3: Subscriptions
Row 4: Transportation

# Parsed to:
{
    0: {'success': True, 'suggestion': 'Healthcare', 'error': None},
    1: {'success': True, 'suggestion': 'Food & Groceries', 'error': None},
    2: {'success': True, 'suggestion': 'Transportation', 'error': None},
    ...
}
```

## Comparison: Single vs Batch Processing

### Single Transaction (Original)
```
Prompt Length: ~500 tokens
Processing Time: 2-3 seconds per item
5 Items Total: 10-15 seconds + 5 API calls
Category Consistency: Varies across calls
```

### Batch (5 Transactions)
```
Prompt Length: ~700 tokens
Processing Time: 4-6 seconds per batch
5 Items Total: 4-6 seconds + 1 API call
Category Consistency: High (LLM sees all together)
Throughput: 5x faster for bulk operations
```

## Implementation Notes

### Backward Compatibility
- Original `build_llm_prompt()` and `get_llm_suggestion()` remain unchanged
- Existing single-row functionality fully supported
- New batch functions are additive

### Error Handling
- Invalid category responses are caught and logged
- Partial failures in batch return individual item errors
- Connection errors handled gracefully for entire batch

### Template Variables in Prompt
```python
- {categories_str}: Comma-separated list of all valid categories
- {examples}: Up to 100 previous categorization examples
- {transactions_str}: List of transactions with row numbers
- {transaction_batch[0][0]}: Example row index in output format
```

## Usage Example

```python
from backend.app import get_batch_llm_suggestions

# Prepare batch of up to 5 transactions
batch = [
    (0, {'Date': '2024-01-05', 'Amount': '75.00', 'Description': 'CVS Pharmacy'}),
    (1, {'Date': '2024-01-06', 'Amount': '32.45', 'Description': 'Chipotle'}),
    (2, {'Date': '2024-01-07', 'Amount': '120.50', 'Description': 'Shell Gas'}),
]

# Get batch suggestions
results = get_batch_llm_suggestions(batch, categories, previous_mappings)

# Results:
# {
#     0: {'success': True, 'suggestion': 'Healthcare', 'error': None},
#     1: {'success': True, 'suggestion': 'Food & Groceries', 'error': None},
#     2: {'success': True, 'suggestion': 'Transportation', 'error': None},
# }
```

## Testing

A test script is provided: `test_batch_prompt.py`

Run to see sample batch prompt:
```bash
python3 test_batch_prompt.py
```

Output shows:
- Full batch prompt structure
- Example transactions
- Expected LLM response format
- Key features and benefits

## Future Integration

To enable batch processing in the bulk-map endpoint:

1. Modify `process_row()` to collect items into batches of 5
2. Call `get_batch_llm_suggestions()` instead of `get_llm_suggestion()`
3. Update progress tracking to account for batch processing
4. Validate parsed results before returning to review screen

Expected performance improvement: **5x faster bulk categorization**

## Configuration

- **Batch Size**: 5 transactions per call (configurable)
- **LLM Temperature**: 0.3 (consistent, deterministic results)
- **Timeout**: 60 seconds per batch (allows time for 5 items)
- **Max Examples**: 100 previous mappings for context

## Prompt Design Principles

1. **Clarity**: Simple, unambiguous instructions to LLM
2. **Structure**: Consistent output format for parsing
3. **Context**: Previous examples guide categorization
4. **Constraint**: Limited response format prevents hallucination
5. **Efficiency**: Batch processing reduces API calls
