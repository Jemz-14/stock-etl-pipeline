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

    plt.savefig(f'{VIS_DIR}/05_correlation_matrix.png')
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

    print("\n" + "=" * 60)
    print(f"✓ VISUALIZATIONS SAVED TO: {VIS_DIR}/")
    print("=" * 60)

if __name__ == "__main__":
    main()