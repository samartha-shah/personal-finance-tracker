# main.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from finance_utils import load_transactions, save_transactions, cumulative_expense, filter_by_type

st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰", layout="centered")
st.title("💰 Automated Personal Finance Tracker")

# Load existing data
df = load_transactions()

# --- Sidebar: Add Transaction ---
st.sidebar.header("Add Transaction")
date = st.sidebar.date_input("Date")
t_type = st.sidebar.selectbox("Type", ["Income", "Expense"])
category = st.sidebar.text_input("Category")
amount = st.sidebar.number_input("Amount", min_value=0.0)
note = st.sidebar.text_input("Note")

if st.sidebar.button("Add Transaction"):
    new_row = pd.DataFrame([[date, t_type, category, amount, note]], 
                           columns=['Date', 'Type', 'Category', 'Amount', 'Note'])
    df = pd.concat([df, new_row], ignore_index=True)
    save_transactions(df)
    st.sidebar.success("Transaction added!")

# --- Main Dashboard ---
st.subheader("All Transactions")
st.dataframe(df)

# Summary
income_total = df[df['Type']=="Income"]['Amount'].sum()
expense_total = df[df['Type']=="Expense"]['Amount'].sum()
balance = income_total - expense_total

st.metric("Total Income", f"₹{income_total:.2f}")
st.metric("Total Expenses", f"₹{expense_total:.2f}")
st.metric("Current Balance", f"₹{balance:.2f}")

# --- Expense by Category (Recursive)
categories = df['Category'].unique()
expense_summary = cumulative_expense(df, categories)
st.subheader("Expense by Category")
st.bar_chart(pd.Series(expense_summary))

# --- Optional: Filter Transactions
st.subheader("Filter Transactions")
filter_choice = st.radio("Show", ["All", "Income Only", "Expense Only"])
if filter_choice != "All":
    filtered_df = filter_by_type(df, filter_choice[:-5])
    st.dataframe(filtered_df)
