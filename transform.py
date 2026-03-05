"""
transform.py - Stock Data Transformation
Calculates technical indicators and derived metrics
"""

import pandas as pd
import numpy as np
import os
from glob import glob
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_DIR = 'data/raw'
OUTPUT_DIR = 'data/processed'
SMA_PERIOD = [20,50] # Simple moving average
RSI_PERIOD = 14 # Standard period for RSI being 14 candles
VOLATILITY_WINDOW = 20 # 20 day rolling volatility


def clean_data(df):
    """Handles missing values and duplicated rows."""
    logger.info("Cleaning raw data...")
    initial_rows = len(df)
    df = df.drop_duplicates(subset =['Ticker','Date'], keep = 'first')
    dupes_dropped = initial_rows - len(df)

    df = df.ffill().dropna()
    logger.info(f"Done, dropped {dupes_dropped} duplicate rows.")
    return df


def calculate_returns(df):
    """ Calculate daily percentage returns"""
    df = df.sort_values(['Ticker','Date'])
    df['Daily_Return'] = df.groupby('Ticker')['Close'].pct_change()
    df['Daily_Return'] = df['Daily_Return'].round(4)

    return df

def calculate_sma(df, periods):
    """ Calculates SMA for a given period"""
    df = df.sort_values(['Ticker', 'Date'])
    for period in periods:
        df[f'SMA_{period}'] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(window=period, min_periods=1).mean())
    return df

def calculate_rsi(df, periods = 14):
    """
    Calculates RSI for a 14 day period
    RSI > 70 = Stock is overbought
    RSI < 30 = Stock is oversold
    """

    df = df.sort_values(['Ticker', 'Date'])

    def rsi_for_ticker(group):
        delta = group['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain/loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    df['RSI'] = df.groupby('Ticker', group_keys=False).apply(rsi_for_ticker, include_groups=False).values
    df['RSI'] = df['RSI'].round(2)
    return df

def calculate_volatility(df, window = 20):
    """ Calculates rolling volatility (std dev of returns"""
    df = df.sort_values(['Ticker', 'Date'])
    df['Volatility'] = df.groupby('Ticker')['Daily_Return'].transform( lambda x: x.rolling(window=window, min_periods=1).std())
    return df

def main():
    logger.info("=" * 60)
    logger.info("STOCK DATA TRANSFORMATION PIPELINE")
    logger.info("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    input_file = f"{INPUT_DIR}/stock_data_latest.csv"
    if not os.path.exists(input_file):
        logger.info("Error: Cannot find {input_file}, make sure to run extract.py first")
        return

    logger.info(f"Loading raw data from :{input_file}")
    df = pd.read_csv(input_file)

    logger.info("\n Applying transformations...")
    df = clean_data(df)

    df = calculate_returns(df)
    df = calculate_sma(df, SMA_PERIOD)
    df = calculate_rsi(df, RSI_PERIOD)
    df = calculate_volatility(df, VOLATILITY_WINDOW)
    logger.info("All indicators calculated")

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = f"{OUTPUT_DIR}/transformed_data_{timestamp}.csv"
    latest_file = f"{OUTPUT_DIR}/transformed_data_latest.csv"
    df.to_csv(output_file, index=False)
    df.to_csv(latest_file, index=False)

    logger.info("\n" + "=" * 60)
    logger.info("TRANSFORMATION SUCCESSFUL")
    logger.info(f"Total Rows: {len(df):,}")
    logger.info(f"New Columns Added: Daily_Return, SMA_20, SMA_50, RSI, Volatility")
    logger.info(f"Saved to: {latest_file}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()