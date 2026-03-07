"""dashboard.py - Interactive Streamlit Web App"""
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit import sidebar

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

# Data Range filter
st.sidebar.markdown("### Date range")
min_date = df['date'].min()
max_date = df['date'].max()

start_date = st.sidebar.date_input(
    "Start Date",
    value=max_date - pd.Timedelta(days=30), # Defaults to a 30-day lookback
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)
sidebar.markdown("### Volume Profile settings")
volume_ticker = st.sidebar.selectbox(
    "Select Single Asset for Volume Analysis:",
    options=available_tickers,
    index=available_tickers.index('SPY') if 'SPY' in available_tickers else 0
)

# Apply filters to data frame
filtered_df = df[
    (df['ticker'].isin(selected_tickers)) &
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

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

st.subheader(f"📊 Total Return ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")

if not filtered_df.empty:
    # Calculate performance for each selected ticker
    performance_data = []
    for ticker in selected_tickers:
        t_df = filtered_df[filtered_df['ticker'] == ticker].sort_values('date')
        if not t_df.empty:
            first_close = t_df['close'].iloc[0]
            last_close = t_df['close'].iloc[-1]
            pct_change = ((last_close - first_close) / first_close) * 100
            performance_data.append({'Ticker': ticker, 'Return': pct_change})

    perf_df = pd.DataFrame(performance_data).sort_values(by='Return', ascending=False)
    fig_perf, ax_perf = plt.subplots(figsize=(12, 5))

    # Dynamic color mapping (Green if >= 0, Red if < 0)
    colours = ['#2ecc71' if val >= 0 else '#e74c3c' for val in perf_df['Return']]

    sns.barplot(data=perf_df, x='Ticker', y='Return', palette=colours, ax=ax_perf)

    # Formatting
    ax_perf.axhline(0, color='black', linewidth=1)
    ax_perf.set_ylabel('Percentage Return (%)')
    ax_perf.set_xlabel('Ticker')
    ax_perf.grid(True, axis='y', linestyle=':', alpha=0.6)

    st.pyplot(fig_perf)
else:
    st.warning("No data available for the selected date range.")

st.divider()

st.subheader(f"{volume_ticker} Volume Profile & Price Action")
st.markdown("Tracking of volume of an asset over a specified period")

# Filter data specifically for single ticker using global data range
vol_df = df[
    (df['ticker'] == volume_ticker) &
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

if not vol_df.empty:
    # Create a 2-row figure, with the top row 3x taller than the bottom row
    fig_vol, (ax_price, ax_vol) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]},
                                               sharex=True)

    # Top Chart: Price action
    ax_price.plot(vol_df['date'], vol_df['close'], color='#2c3e50', linewidth=1.5)
    ax_price.set_ylabel('Price ($)')
    ax_price.grid(True, linestyle=':', alpha=0.6)

    # Bottom Chart: Directional Volume
    vol_colors = ['#2ecc71' if val >= 0 else '#e74c3c' for val in vol_df['daily_return']]
    ax_vol.bar(vol_df['date'], vol_df['volume'], color=vol_colors, alpha=0.8)
    ax_vol.set_ylabel('Volume traded')
    ax_vol.set_xlabel('Date')
    ax_vol.grid(True, linestyle=':', alpha=0.6)

    # Format layout to prevent overlapping labels
    plt.xticks(rotation=45)
    fig_vol.tight_layout()

    # Render in Streamlit
    st.pyplot(fig_vol)

else:
    st.warning(f"No volume data available for {volume_ticker} in this date range.")

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