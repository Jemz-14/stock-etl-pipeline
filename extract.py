"""
extract.py - Stock Data Extraction Script
Fetches historical stock data from Yahoo Finance and saves to CSV
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Configuration
TICKERS = ['SPY', 'QQQ', 'NVDA', 'MSFT', 'AMZN', 'JPM', 'JNJ', 'XOM', 'TSLA', 'V']
RAW_DIR = Path('data/raw')
LOOKBACK_DAYS = 365 # 1 year of historical data


''' Creates output directory if it does not exist'''
def setup_directories():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Directory ready: {RAW_DIR}")


def fetch_stock_data(ticker: str, start_date: str, end_date: str):
    """
    Fetches historical stock data for a single ticker.
    """
    try:
        print(f"Fetching {ticker} stock data from Yahoo Finance...", end = " ", flush = True)

        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            print(f"No data found for {ticker}.")
            return None
        # Cleans up columns to prevent yahoo from giving us other columns
        target_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df =df[target_cols].copy()

        # Flatten + normalise data
        df.reset_index(inplace=True)

        # Converts date to simple date
        df['Date'] = df['Date'].dt.date

        # Add identifier
        df['Ticker'] = ticker
        df = df[['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']] # Better readability

        print(f"{len(df)} stock data found for {ticker}.")

        return df
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def main():
    """Main function"""
    print("=" * 60)
    print("STOCK DATA EXTRACTION PIPELINE")
    print("=" * 60)

    setup_directories()

    end_data_obj = datetime.now()
    start_date_obj = end_data_obj - timedelta(days=LOOKBACK_DAYS)

    start_str = start_date_obj.strftime("%Y-%m-%d")
    end_str = end_data_obj.strftime("%Y-%m-%d")

    print(f"\nDate Range: {start_str} to {end_str}")
    print(f"Targeting: {len(TICKERS)} stocks\n")

    all_data = []

    for ticker in TICKERS:
        df = fetch_stock_data(ticker, start_str, end_str)
        if df is not None:
            all_data.append(df)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True) #important to do so indexes don't stack and we create new ones

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = RAW_DIR / f"stock_data_{timestamp}.csv"
        
        # Also save a 'latest.csv' for easier access in the next phase
        latest_file = RAW_DIR / "stock_data_latest.csv"

        combined_df.to_csv(output_file,index=False)
        combined_df.to_csv(latest_file,index=False)

        print("\n" + "=" * 60)
        print(f"Extraction successful")
        print(f" • Total Rows: {len(combined_df):,}")
        print(f" • Unique Tickers: {combined_df['Ticker'].nunique()}")
        print(f" • Saved to: {output_file}")
        print(f" • Updated:  {latest_file}")
        print("=" * 60)

        print("\nSample Data:")
        print(combined_df.head())
    
    else:
        print("Failed to extract data")

if __name__ == "__main__":
    main()















