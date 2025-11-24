#!/usr/bin/env python3
"""
Test script to demonstrate batch categorization prompt.
Shows how the LLM would process 5 transactions at once.
"""

# Sample batch of 5 transactions
transaction_batch = [
    (0, {
        'Date': '2024-01-05',
        'Amount': '75.00',
        'Description': 'CVS Pharmacy'
    }),
    (1, {
        'Date': '2024-01-06',
        'Amount': '32.45',
        'Description': 'Chipotle Mexican Grill'
    }),
    (2, {
        'Date': '2024-01-07',
        'Amount': '120.50',
        'Description': 'Shell Gas Station'
    }),
    (3, {
        'Date': '2024-01-08',
        'Amount': '15.99',
        'Description': 'Netflix Subscription'
    }),
    (4, {
        'Date': '2024-01-09',
        'Amount': '85.50',
        'Description': 'Uber Trip'
    })
]

categories = [
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

previous_mappings = [
    {
        'date': '12/24/2024',
        'amount': '-20.12',
        'description': 'SUPREMACIA CARNICA',
        'category': 'Food & Groceries'
    },
    {
        'date': '12/24/2024',
        'amount': '-5.00',
        'description': 'OPENAI',
        'category': 'Subscriptions'
    },
    {
        'date': '12/24/2024',
        'amount': '-45.15',
        'description': 'MERCADONA JOSE M DE HARO',
        'category': 'Food & Groceries'
    },
    {
        'date': '2024-01-02',
        'amount': '120.50',
        'description': 'Shell Gas Station',
        'category': 'Transportation'
    },
    {
        'date': '2024-01-03',
        'amount': '15.99',
        'description': 'Netflix Subscription',
        'category': 'Subscriptions'
    }
]


def build_batch_llm_prompt(transaction_batch, categories, previous_mappings):
    """Build a prompt for batch categorization (up to 5 transactions at a time)."""

    # Build examples from previous mappings
    examples = ""
    if previous_mappings:
        examples = "\nHere are examples of previous categorizations:\n"
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


if __name__ == "__main__":
    print("=" * 80)
    print("BATCH CATEGORIZATION PROMPT EXAMPLE")
    print("=" * 80)
    print()

    prompt = build_batch_llm_prompt(transaction_batch, categories, previous_mappings)

    print(prompt)
    print()
    print("=" * 80)
    print("EXPECTED LLM RESPONSE FORMAT:")
    print("=" * 80)
    print("Row 0: Healthcare")
    print("Row 1: Food & Groceries")
    print("Row 2: Transportation")
    print("Row 3: Subscriptions")
    print("Row 4: Transportation")
    print()
    print("=" * 80)
    print("KEY FEATURES:")
    print("=" * 80)
    print("✓ Processes 5 transactions in a single LLM call")
    print("✓ Uses structured 'Row <idx>: <CATEGORY>' output format")
    print("✓ Includes up to 100 previous examples for context")
    print("✓ Validates categories against available list")
    print("✓ Can be extended for remaining rows if less than 5")
    print("✓ Much faster than 5 separate API calls")
