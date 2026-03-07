"""dashboard.py - Interactive Streamlit Web App"""
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns


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

st.divider()

st.subheader("Portfolio Analytics")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Asset Correlation Matrix")
    st.markdown("Identifies redundant risk exposure across selected assets.")

    pivot_df = filtered_df.pivot(index='date', columns='ticker', values='daily_return')
    corr_matrix = pivot_df.corr()

    fig_corr, ax_corr = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f',
                linewidths=.5, vmin=-1, vmax=1, ax=ax_corr)

    # Render the plot in Streamlit
    st.pyplot(fig_corr)

with col2:
    st.markdown("#### Risk vs Return (Annualised)")
    st.markdown("Maps historical volatility against expected payout.")

    summary = filtered_df.groupby('ticker').agg(
        avg_return=('daily_return', 'mean'),
        avg_volatility=('volatility', 'mean')
    ).reset_index()

    summary['annual_return'] = summary['avg_return'] * 252 * 100
    summary['annual_volatility'] = summary['avg_volatility'] * (252 ** 0.5) * 100

    fig_risk, ax_risk = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=summary, x='annual_volatility', y='annual_return',
                    s=200, color='#3498db', ax=ax_risk)

    for i, row in summary.iterrows():
        ax_risk.text(row['annual_volatility'] + 0.5, row['annual_return'] + 0.5,
                     row['ticker'], fontsize=10, fontweight='bold')

    # Add crosshairs at 0% return
    ax_risk.axhline(0, color='black', linestyle='--', linewidth=1)
    ax_risk.set_xlabel('Annualized Volatility (Risk) %')
    ax_risk.set_ylabel('Annualized Expected Return %')
    ax_risk.grid(True, linestyle=':', alpha=0.6)

    # Render the plot in Streamlit
    st.pyplot(fig_risk)