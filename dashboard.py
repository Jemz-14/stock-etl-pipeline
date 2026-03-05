"""dashboard.py - Interactive Streamlit Web App"""
import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Stock Analysis Terminal", page_icon="📈", layout="wide")


# Data Loader (Cached so it doesn't query the DB every time you click a button)
@st.cache_data
def load_db():
    conn = sqlite3.connect('data/stock_data.db')
    df = pd.read_sql_query("SELECT * FROM stock_data", conn)
    conn.close()

    # Ensure date is a proper datetime object
    df['date'] = pd.to_datetime(df['date'])
    return df

# Main app layout
st.title("Stock Analysis Terminal")
st.markdown("Interactive portfolio tracking, momentum screening, and risk-adjusted performance analysis.")
st.divider()

df = load_db()


# Sidebar Configuration
st.sidebar.header("⚙️ Terminal Controls")

# Ticker multi select filter
available_tickers = sorted(df['ticker'].unique())
selected_tickers = st.sidebar.multiselect("Select ticker", options=available_tickers,
    default=['SPY', 'QQQ', 'NVDA', 'TSLA']) # Default selection so the screen isn't empty

# Apply filters to data frame
filtered_df = df[df['ticker'].isin(selected_tickers)]

# Dashboard content
st.subheader("Data overview")
st.write(f"Currently tracking **{len(filtered_df):,}** daily records for the selected assets.")

# Display the raw data as a sanity check
st.dataframe(
    filtered_df.sort_values(['date', 'ticker'], ascending=[False, True]),
    use_container_width=True,
    height=250
)

