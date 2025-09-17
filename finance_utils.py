import os
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Load transactions
# -----------------------------
def load_transactions(file_path='data/transactions.csv'):
    """
    Load transactions from CSV. Creates file if missing or empty.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    expected_cols = ['Date', 'Type', 'Category', 'Amount', 'Note']
    
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(file_path, index=False)
        return df
    
    try:
        df = pd.read_csv(file_path)
        df = validate_and_clean_data(df, expected_cols)
        return df
    except Exception as e:
        logger.error(f"Error loading transactions: {e}")
        return pd.DataFrame(columns=expected_cols)

# -----------------------------
# Save transactions
# -----------------------------
def save_transactions(df, file_path='data/transactions.csv'):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if os.path.exists(file_path):
        backup_path = file_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
    df.to_csv(file_path, index=False)

# -----------------------------
# Add transaction
# -----------------------------
def add_transaction(date, t_type, category, amount, note=''):
    df = load_transactions()
    new_row = {'Date': date, 'Type': t_type, 'Category': category, 'Amount': amount, 'Note': note}
    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
    save_transactions(df)
    return df

# -----------------------------
# Remove transaction
# -----------------------------
def remove_transaction(index):
    df = load_transactions()
    if index in df.index:
        df = df.drop(index)
        df = df.reset_index(drop=True)
        save_transactions(df)
    return df

# -----------------------------
# Validate & clean data
# -----------------------------
def validate_and_clean_data(df, expected_cols):
    if list(df.columns) != expected_cols:
        df = pd.DataFrame(columns=expected_cols)
    if df.empty:
        return df
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['Date'].notna()]
    df['Type'] = df['Type'].where(df['Type'].isin(['Income', 'Expense']), 'Expense')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df[df['Amount'].notna() & (df['Amount'] >= 0)]
    df['Category'] = df['Category'].fillna('Other')
    df['Note'] = df['Note'].fillna('')
    df = df.sort_values('Date', ascending=False).reset_index(drop=True)
    return df

# -----------------------------
# Monthly summary
# -----------------------------
def get_monthly_summary(df):
    if df.empty: return pd.DataFrame()
    df_copy = df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Date'])
    df_copy['Month'] = df_copy['Date'].dt.to_period('M')
    monthly_summary = df_copy.groupby(['Month','Type'])['Amount'].sum().reset_index()
    monthly_pivot = monthly_summary.pivot(index='Month', columns='Type', values='Amount').fillna(0)
    if 'Income' not in monthly_pivot.columns: monthly_pivot['Income'] = 0
    if 'Expense' not in monthly_pivot.columns: monthly_pivot['Expense'] = 0
    monthly_pivot['Balance'] = monthly_pivot['Income'] - monthly_pivot['Expense']
    return monthly_pivot.reset_index()

# -----------------------------
# Category analysis
# -----------------------------
def get_category_analysis(df, transaction_type='Expense'):
    filtered_df = df[df['Type'] == transaction_type]
    if filtered_df.empty: return pd.DataFrame()
    summary = filtered_df.groupby('Category').agg({'Amount':['sum','mean','count'],'Date':['min','max']}).reset_index()
    summary.columns = ['Category','Total','Average','Count','First_Date','Last_Date']
    total_amount = summary['Total'].sum()
    summary['Percentage'] = (summary['Total']/total_amount*100).round(2)
    return summary.sort_values('Total', ascending=False)

# -----------------------------
# Recursive cumulative expense
# -----------------------------
def cumulative_expense(df, categories=None, index=0, totals=None):
    if categories is None:
        expense_data = df[df['Type'] == 'Expense'] if not df.empty else pd.DataFrame()
        categories = expense_data['Category'].unique().tolist() if not expense_data.empty else []
    if totals is None:
        totals = {cat: 0.0 for cat in categories}
    if index >= len(df):
        return totals
    row = df.iloc[index]
    if row['Type'] == 'Expense' and row['Category'] in totals:
        totals[row['Category']] += float(row['Amount'])
    return cumulative_expense(df, categories, index+1, totals)

# -----------------------------
# Filter utilities
# -----------------------------
filter_by_type = lambda df, t: df[df['Type'] == t] if not df.empty and t in ['Income','Expense'] else pd.DataFrame()
filter_by_category = lambda df, cat: df[df['Category'] == cat] if not df.empty else pd.DataFrame()
filter_by_date_range = lambda df, start_date, end_date: df[(df['Date'] >= start_date) & (df['Date'] <= end_date)] if not df.empty else pd.DataFrame()

# -----------------------------
# Trend analysis
# -----------------------------
def get_trend_analysis(df, days=30):
    if df.empty: return {}
    df_copy = df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Date'])
    end_date = df_copy['Date'].max()
    start_date = end_date - timedelta(days=days)
    recent_data = df_copy[(df_copy['Date'] >= start_date) & (df_copy['Date'] <= end_date)]
    if recent_data.empty: return {}
    total_income = recent_data[recent_data['Type']=='Income']['Amount'].sum()
    total_expenses = recent_data[recent_data['Type']=='Expense']['Amount'].sum()
    net_flow = total_income - total_expenses
    daily_income = total_income / days
    daily_expenses = total_expenses / days
    top_categories = recent_data[recent_data['Type']=='Expense'].groupby('Category')['Amount'].sum().sort_values(ascending=False).head(5).to_dict()
    return {
        'period_days': days,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_flow': net_flow,
        'daily_income_avg': daily_income,
        'daily_expenses_avg': daily_expenses,
        'top_expense_categories': top_categories,
        'transaction_count': len(recent_data)
    }

# -----------------------------
# Financial health score
# -----------------------------
def get_financial_health_score(df):
    if df.empty: return 0
    total_income = df[df['Type']=='Income']['Amount'].sum()
    total_expenses = df[df['Type']=='Expense']['Amount'].sum()
    if total_income == 0: return 0
    savings_rate = ((total_income-total_expenses)/total_income)*100
    if savings_rate>=20: return 100
    elif savings_rate>=10: return 80
    elif savings_rate>=0: return 60
    else: return 20

# -----------------------------
# JSON export/import
# -----------------------------
def export_to_json(df, file_path='data/transactions_export.json'):
    if df.empty: return False
    df_copy = df.copy()
    df_copy['Date'] = df_copy['Date'].dt.strftime('%Y-%m-%d')
    transactions_dict = df_copy.to_dict('records')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(transactions_dict, f, indent=2, ensure_ascii=False)
    return True

def import_from_json(file_path='data/transactions_export.json'):
    if not os.path.exists(file_path): return pd.DataFrame()
    with open(file_path, 'r', encoding='utf-8') as f:
        transactions_data = json.load(f)
    df = pd.DataFrame(transactions_data)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
    return df
