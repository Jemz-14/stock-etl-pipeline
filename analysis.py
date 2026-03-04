"""analysis.py - Generate professional financial visualizations"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import timedelta

DB_PATH = 'data/stock_data.db'
VIS_DIR = 'data/visualisations'

def fetch_data():
    """Connects to DB and loads all data into a pandas dataframe"""
    print("Loading data from database...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM stock_data", conn,parse_dates=['date'])
    conn.close()
    return df

def plot_price_trends(df):
    """ Line chart showing 90-day price movements"""
    print("Generating 90 day price trends...")

    latest_date = df['date'].max()
    cutoff_date = latest_date - timedelta(days = 90)
    recent_df = df[df['date'] >= cutoff_date]

    plt.figure(figsize=(14,7))
    sns.lineplot(data=recent_df, x='date', y='close', hue='ticker', linewidth=2)

    plt.title("90 Day Price Trends", fontsize = 16, fontweight='bold')
    plt.xlabel('Date', fontsize = 14)
    plt.ylabel('Closing Price ($)', fontsize = 14)
    plt.legend(title='Ticker',bbox_to_anchor=(1.05,1),loc='upper left')
    plt.tight_layout()

    plt.savefig(f"{VIS_DIR}/01 Day Price Trends.png")
    plt.close()

def plot_performance(df):
    """ Bar chart showing 30-day performance (green for profit red for loss)"""
    print("Generating 30 day performance chart...")

    latest_date = df['date'].max()
    cutoff_date = latest_date - timedelta(days = 30)
    recent_df = df[df['date'] >= cutoff_date]

    # Calculate return over 30 days
    performance = recent_df.groupby('ticker')['daily_return'].sum() * 100
    performance = performance.sort_values(ascending=False)

    plt.figure(figsize=(12,6))

    # Colours list, green if > 0, red if < 0
    colours = ['#2ecc71' if val >= 0 else '#e74c3c' for val in performance]

    sns.barplot(x=performance.index, y=performance.values,palette=colours)
    plt.title("30 Day Total Return (%)", fontsize = 14, fontweight='bold')
    plt.xlabel('Ticker', fontsize = 14)
    plt.ylabel('Percentage Return (%)', fontsize = 14)
    plt.axhline(0, color='black', linewidth=1)  # Adds a solid line at 0%
    plt.tight_layout()

    plt.savefig(f"{VIS_DIR}/02 30 Day Performance Chart.png")

    plt.close()

def plot_correlation_matrix(df):
    """ Heatmap showing how stocks move together"""
    print("Generating correlation matrix...")

    pivot_df = df.pivot(index='date', columns='ticker', values='daily_return')

    corr_matrix = pivot_df.corr()

    plt.figure(figsize=(10,8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5, vmin=-1, vmax=1)

    plt.title('Stock Return Correlation Matrix', fontsize=16, fontweight='bold')
    plt.tight_layout()

    plt.savefig(f'{VIS_DIR}/03_correlation_matrix.png')
    plt.close()

def plot_rsi_heatmap(df):
    """ RSI heatmap showing overbought/oversold conditions over a month"""

    latest_date = df['date'].max()
    cutoff_date = latest_date - timedelta(days = 31)
    recent_df = df[df['date'] >= cutoff_date]

    pivot_rsi = recent_df.pivot(index='ticker', columns='date', values='rsi')

    pivot_rsi.columns = pivot_rsi.columns.strftime('%m-%d')

    plt.figure(figsize=(12,6))
    sns.heatmap(pivot_rsi, cmap='RdYlGn_r', center=50, vmin=20, vmax=80,
                annot=True, fmt=".0f", linewidths=.5)

    plt.title("14-day RSI heatmap over a 30 day period (Overbought > 70, Oversold < 30)", fontsize = 14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Ticker')
    plt.tight_layout()

    plt.savefig(f"{VIS_DIR}/04_rsi_heatmap.png")
    plt.close()


def plot_market_volume_profile(df, target_ticker='SPY'):
    """ Dual-Pane Volume Profile - Price action combined with directional volume"""
    print(f"Generating Dual-Pane Volume Profile for {target_ticker}...")

    # Isolate the data for just our market proxy
    market_df = df[df['ticker'] == target_ticker].copy()

    # Look at just the last 90 days so the bars are thick and readable
    cutoff_date = market_df['date'].max() - timedelta(days=90)
    recent_df = market_df[market_df['date'] >= cutoff_date]

    # Set up a 2-row grid. Top row is 3x taller than the bottom row.
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3, 1]})

    # Top chart: Price Action
    sns.lineplot(data=recent_df, x='date', y='close', ax=ax1, color='#2c3e50', linewidth=2)
    ax1.set_title(f'{target_ticker} Market Volume Profile (Last 90 Days)', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Closing Price ($)', fontsize=12)
    ax1.set_xlabel('')  # Hide the X-axis label so it doesn't clash with the bottom chart
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Bottom chart : Directional Volume
    # Create a list of colours: Green if today's return is positive, Red if negative
    colors = ['#2ecc71' if val > 0 else '#e74c3c' for val in recent_df['daily_return']]

    ax2.bar(recent_df['date'], recent_df['volume'], color=colors, alpha=0.8)
    ax2.set_ylabel('Volume Traded', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{VIS_DIR}/04_{target_ticker}_volume_profile.png')
    plt.close()


def plot_risk_vs_return(df):
    """ Scatter plot mapping annualized volatility against performance"""
    print("Generating Risk vs Return Scatter Plot...")

    # Calculate average daily return and volatility
    summary = df.groupby('ticker').agg(
        avg_return=('daily_return', 'mean'),
        avg_volatility=('volatility', 'mean')
    ).reset_index()

    # Annualize the numbers (standard Wall Street practice: 252 trading days in a year)
    summary['annual_return'] = summary['avg_return'] * 252 * 100
    summary['annual_volatility'] = summary['avg_volatility'] * (252 ** 0.5) * 100

    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=summary, x='annual_volatility', y='annual_return', s=250, color='#3498db')

    # Add text labels to each dot so we know which stock is which
    for i, row in summary.iterrows():
        plt.text(row['annual_volatility'] + 0.3, row['annual_return'] + 0.3,
                 row['ticker'], fontsize=11, fontweight='bold')

    # Add crosshairs at 0% return
    plt.axhline(0, color='black', linestyle='--', linewidth=1)

    plt.title('Risk vs. Return Matrix (Annualized)', fontsize=16, fontweight='bold')
    plt.xlabel('Annualized Volatility (Risk) %', fontsize=14)
    plt.ylabel('Annualized Expected Return (Reward) %', fontsize=14)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()

    plt.savefig(f'{VIS_DIR}/05_risk_vs_return.png')
    plt.close()


def main():
    print("=" * 60)
    print("STOCK DATA VISUALISATION")
    print("=" * 60)

    os.makedirs(VIS_DIR, exist_ok=True)

    sns.set(style='darkgrid')

    df = fetch_data()

    plot_price_trends(df)
    plot_performance(df)
    plot_correlation_matrix(df)
    plot_rsi_heatmap(df)
    plot_market_volume_profile(df)
    plot_risk_vs_return(df)

    print("\n" + "=" * 60)
    print(f"VISUALIZATIONS SAVED TO: {VIS_DIR}/")
    print("=" * 60)



if __name__ == "__main__":
    main()