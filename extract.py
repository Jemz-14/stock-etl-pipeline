"""
extract.py - Stock Data Extraction Script
Fetches historical stock data from Yahoo Finance and saves to CSV
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TICKERS = ['SPY', 'QQQ', 'NVDA', 'MSFT', 'AMZN', 'JPM', 'JNJ', 'XOM', 'TSLA', 'V']
RAW_DIR = Path('data/raw')
LOOKBACK_DAYS = 365 # 1 year of historical data


''' Creates output directory if it does not exist'''
def setup_directories():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directory ready: {RAW_DIR}")


def fetch_stock_data(ticker: str, start_date: str, end_date: str):
    """
    Fetches historical stock data for a single ticker.
    """
    try:
        logger.info(f"Fetching {ticker} stock data from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            logger.info(f"No data found for {ticker}.")
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

        logger.info(f"{len(df)} stock data found for {ticker}.")

        return df
    except Exception as e:
        logger.info(f"Error fetching {ticker}: {e}")
        return None

def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("STOCK DATA EXTRACTION PIPELINE")
    logger.info("=" * 60)

    setup_directories()

    end_data_obj = datetime.now()
    start_date_obj = end_data_obj - timedelta(days=LOOKBACK_DAYS)

    start_str = start_date_obj.strftime("%Y-%m-%d")
    end_str = end_data_obj.strftime("%Y-%m-%d")

    logger.info(f"\nDate Range: {start_str} to {end_str}")
    logger.info(f"Targeting: {len(TICKERS)} stocks\n")

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

        logger.info("\n" + "=" * 60)
        logger.info(f"Extraction successful")
        logger.info(f" • Total Rows: {len(combined_df):,}")
        logger.info(f" • Unique Tickers: {combined_df['Ticker'].nunique()}")
        logger.info(f" • Saved to: {output_file}")
        logger.info(f" • Updated:  {latest_file}")
        logger.info("=" * 60)

        logger.info("\nSample Data:")
        logger.info(combined_df.head())
    
    else:
        logger.info("Failed to extract data")

if __name__ == "__main__":
    main()















