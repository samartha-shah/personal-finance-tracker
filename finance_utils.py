# finance_utils.py
import os
import pandas as pd

# -----------------------------
# Load Transactions
# -----------------------------
def load_transactions(file_path='data/transactions.csv'):
    """
    Load the transactions from CSV.
    If the file is missing or empty, create it with proper headers.
    """
    # Ensure the folder exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # If file missing or empty → create with headers
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        df = pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Note'])
        df.to_csv(file_path, index=False)
    else:
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Note'])
            df.to_csv(file_path, index=False)

        # Safety check: ensure correct columns
        expected_cols = ['Date', 'Type', 'Category', 'Amount', 'Note']
        if list(df.columns) != expected_cols:
            df = pd.DataFrame(columns=expected_cols)
            df.to_csv(file_path, index=False)

    return df


# -----------------------------
# Save Transactions
# -----------------------------
def save_transactions(df, file_path='data/transactions.csv'):
    """
    Save the transaction DataFrame to CSV.
    """
    df.to_csv(file_path, index=False)


# -----------------------------
# Recursive Function
# -----------------------------
def cumulative_expense(df, categories, index=0, totals=None):
    """
    Recursively calculate total expenses for each category.
    """
    if totals is None:
        totals = {cat: 0 for cat in categories}

    if index >= len(df):
        return totals

    row = df.iloc[index]
    if row['Type'] == 'Expense':
        totals[row['Category']] += row['Amount']

    return cumulative_expense(df, categories, index + 1, totals)


# -----------------------------
# Lambda Function
# -----------------------------
# Filter transactions quickly by type
filter_by_type = lambda df, t: df[df['Type'] == t]
