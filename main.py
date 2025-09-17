import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from finance_utils import load_transactions, save_transactions

# Page Configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
/* Your full original CSS here */
</style>
""", unsafe_allow_html=True)

# Load transactions
@st.cache_data
def get_transactions():
    return load_transactions()

df = get_transactions()

# Initialize session state for refresh
if 'transactions' not in st.session_state:
    st.session_state.transactions = df.copy()

# Main Header
st.markdown("""
<div class="main-header">
    <h1>💰 Personal Finance Tracker</h1>
    <p>Take control of your financial future</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Add Transaction
with st.sidebar:
    st.markdown("### 📝 Add New Transaction")
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("📅 Date", datetime.now())
        with col2:
            t_type = st.selectbox("📊 Type", ["Income", "Expense"])

        categories = ["Salary", "Freelance", "Investment", "Business", "Bonus", "Other Income"] if t_type=="Income" else ["Food & Dining", "Transportation", "Shopping", "Bills & Utilities","Healthcare", "Entertainment", "Education", "Travel", "Other Expense"]
        category = st.selectbox("🏷️ Category", categories)
        amount = st.number_input("💵 Amount (₹)", min_value=0.0, step=1.0)
        note = st.text_input("📝 Note (Optional)")

        submitted = st.form_submit_button("➕ Add Transaction")
        if submitted:
            if amount > 0:
                new_row = pd.DataFrame([[date, t_type, category, amount, note]], columns=['Date','Type','Category','Amount','Note'])
                st.session_state.transactions = pd.concat([st.session_state.transactions, new_row], ignore_index=True)
                save_transactions(st.session_state.transactions)
                st.success(f"✅ {t_type} of ₹{amount:,.2f} added successfully!")

# Sidebar - Remove Transaction
with st.sidebar:
    st.markdown("### 🗑️ Remove Transaction")
    if not st.session_state.transactions.empty:
        st.write("Select a transaction to remove:")
        remove_idx = st.selectbox(
            "Transaction Index", 
            st.session_state.transactions.index,
            format_func=lambda x: f"{x}: {st.session_state.transactions.loc[x,'Type']} {st.session_state.transactions.loc[x,'Category']} ₹{st.session_state.transactions.loc[x,'Amount']:.2f} on {st.session_state.transactions.loc[x,'Date']}"
        )
        if st.button("❌ Remove Selected Transaction"):
            st.session_state.transactions.drop(remove_idx, inplace=True)
            st.session_state.transactions.reset_index(drop=True, inplace=True)
            save_transactions(st.session_state.transactions)
            st.success("✅ Transaction removed successfully!")

# Main Dashboard Metrics
total_income = st.session_state.transactions[st.session_state.transactions['Type']=="Income"]['Amount'].sum()
total_expenses = st.session_state.transactions[st.session_state.transactions['Type']=="Expense"]['Amount'].sum()
balance = total_income - total_expenses
transaction_count = len(st.session_state.transactions)

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Balance", f"₹{balance:,.2f}")
col2.metric("📈 Total Income", f"₹{total_income:,.2f}")
col3.metric("📉 Total Expenses", f"₹{total_expenses:,.2f}")
col4.metric("📊 Transactions", f"{transaction_count}")

# Charts
if not st.session_state.transactions.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Income vs Expenses")
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Income','Expenses'],
            values=[total_income,total_expenses],
            hole=0.4,
            marker_colors=['#10b981','#ef4444']
        )])
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("🏷️ Expenses by Category")
        expense_data = st.session_state.transactions[st.session_state.transactions['Type']=="Expense"]
        if not expense_data.empty:
            category_totals = expense_data.groupby('Category')['Amount'].sum().reset_index()
            fig_bar = px.bar(category_totals, x='Category', y='Amount', color='Amount', color_continuous_scale=['#fee2e2','#FF0000'])
            fig_bar.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

# Filters
st.markdown("### 🔍 Filter Transactions")
filter_type = st.selectbox("Type Filter", ["All","Income","Expense"])
categories = ["All"] + sorted(st.session_state.transactions['Category'].unique().tolist()) if not st.session_state.transactions.empty else ["All"]
filter_category = st.selectbox("Category Filter", categories)
search_term = st.text_input("Search Notes")

filtered_df = st.session_state.transactions.copy()
if filter_type != "All":
    filtered_df = filtered_df[filtered_df['Type']==filter_type]
if filter_category != "All":
    filtered_df = filtered_df[filtered_df['Category']==filter_category]
if search_term:
    filtered_df = filtered_df[filtered_df['Note'].str.contains(search_term, case=False, na=False)]

st.markdown("### 📋 Recent Transactions")
if filtered_df.empty:
    st.info("No transactions found")
else:
    filtered_df = filtered_df.sort_values('Date', ascending=False)
    for idx, row in filtered_df.iterrows():
        type_emoji = "📈" if row['Type']=='Income' else "📉"
        type_color = "positive" if row['Type']=='Income' else "negative"
        amount_prefix = "+" if row['Type']=='Income' else "-"
        st.markdown(f"""
        <div class="transaction-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:1rem;">
                    <span style="font-size:1.5rem;">{type_emoji}</span>
                    <div>
                        <div style="font-weight:600; font-size:1.1rem; color:#374151;">{row['Category']}</div>
                        <div style="color:#6b7280; font-size:0.9rem;">{row['Note'] if row['Note'] else 'No note'}</div>
                        <div style="color:#9ca3af; font-size:0.8rem;">📅 {pd.to_datetime(row['Date']).strftime('%B %d, %Y')}</div>
                    </div>
                </div>
                <div class="{type_color}" style="font-weight:700; font-size:1.2rem;">{amount_prefix}₹{row['Amount']:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
