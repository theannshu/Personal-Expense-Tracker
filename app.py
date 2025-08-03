import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# --- Title ---
st.title("💰 Personal Expense Tracker")

# --- Data Persistence ---
DATA_FILE = "expense_data.csv"

# --- Load or Initialize Data ---
@st.cache_data
def load_data():
    """Load data from CSV, or create an empty DataFrame if file doesn't exist."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])
    return df

df = load_data()

# --- FIX #1: MERGE OLD DATA ---
# This line merges any old 'Travel' and 'Transport' entries into a single category.
df['Category'] = df['Category'].replace(['Travel', 'Transport'], 'Travel & Transport')


# --- Sidebar for Inputs ---
st.sidebar.header("➕ Add New Expense")
with st.sidebar.form("add_form", clear_on_submit=True):
    exp_date = st.date_input("Date", date.today())
    
    # --- FIX #2: UPDATE INPUT OPTIONS ---
    # The category list is now updated and simplified.
    category = st.selectbox("Category", ["Food", "Rent", "Travel & Transport", "Shopping", "Bills", "Entertainment", "Other"])
    
    amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01)
    description = st.text_input("Description (Optional)")
    
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        new_data = pd.DataFrame([[exp_date, category, amount, description]], columns=df.columns)
        df = pd.concat([df, new_data], ignore_index=True)
        # Ensure the combined category is saved correctly
        df['Category'] = df['Category'].replace(['Travel', 'Transport'], 'Travel & Transport')
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("✅ Expense added!")
        st.cache_data.clear()
        st.rerun()

# --- Sidebar for Deletion ---
if not df.empty:
    st.sidebar.header("❌ Delete Expense")
    st.sidebar.dataframe(
        df.sort_values("Date", ascending=False).head(5).reset_index(drop=True),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="₹%.2f"),
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD")
        }
    )
    all_indices = list(df.index)
    index_to_delete = st.sidebar.selectbox("Select row index to delete", options=[""] + all_indices)
    if st.sidebar.button("Delete Selected Expense"):
        if index_to_delete != "":
            df = df.drop(int(index_to_delete)).reset_index(drop=True)
            df.to_csv(DATA_FILE, index=False)
            st.sidebar.success(f"🗑️ Deleted row {index_to_delete}")
            st.cache_data.clear()
            st.rerun()
        else:
            st.sidebar.warning("Please select a row index to delete.")

# --- Main Page ---
st.header("📊 Expense Summary")
if df.empty:
    st.warning("⚠️ No expense data yet. Please add an expense using the sidebar.")
else:
    # --- Filters ---
    category_filter = st.multiselect(
        "Filter by Category", 
        options=df["Category"].unique(), 
        default=list(df["Category"].unique())
    )
    df["Date"] = pd.to_datetime(df["Date"], format='mixed')
    start_date = st.date_input("Start Date", df["Date"].min().date())
    end_date = st.date_input("End Date", df["Date"].max().date())

    filtered_df = df[
        (df["Category"].isin(category_filter)) &
        (df["Date"].dt.date >= start_date) &
        (df["Date"].dt.date <= end_date)
    ]

    if filtered_df.empty:
        st.info("No data available for the selected filters.")
    else:
        # --- KPIs ---
        total_spent = filtered_df["Amount"].sum()
        top_category = filtered_df.groupby("Category")["Amount"].sum().idxmax()
        col1, col2 = st.columns(2)
        col1.metric("💸 Total Spent", f"₹ {total_spent:,.2f}")
        col2.metric("🏆 Top Category", top_category)
        
        st.markdown("---")

        # --- Visualizations ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Monthly Expense Totals")
            monthly_totals_df = filtered_df.copy()
            monthly_totals_df["Month"] = monthly_totals_df["Date"].dt.to_period("M").astype(str)
            monthly_summary = monthly_totals_df.groupby("Month")["Amount"].sum().reset_index()
            fig_bar = px.bar(
                monthly_summary, x="Month", y="Amount", text_auto=True, title="Monthly Expense Trend"
            )
            fig_bar.update_traces(textposition="outside", texttemplate='₹%{y:,.0f}')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.markdown("#### Expenses by Category")
            category_summary = filtered_df.groupby("Category")["Amount"].sum().reset_index()
            fig_pie = px.pie(
                category_summary, names="Category", values="Amount", title="Category-wise Distribution", hole=0.3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.markdown("---")

        # --- Data Table ---
        st.markdown("#### 📋 List of Expenses")
        st.dataframe(
            filtered_df.sort_values("Date", ascending=False).reset_index(drop=True), 
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="₹%.2f"),
                "Date": st.column_config.DateColumn(format="YYYY-MM-DD")
            }
        )