"""load.py - Load transformed data into database"""

import pandas as pd
import sqlite3
from glob import glob
import os
from datetime import datetime
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sqlite3.register_adapter(np.int64, int)
sqlite3.register_adapter(np.float64, float)

INPUT_DIR = 'data/processed'
DB_PATH = 'data/stock_data.db' #SQL lite database file

def create_database():
    """Create database and table if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                daily_return REAL,
                sma_20 REAL,
                sma_50 REAL,
                rsi REAL,
                volatility REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date)
            )
        ''')

    cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_date 
            ON stock_data(ticker, date)
        ''')

    cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date 
            ON stock_data(date)
        ''')

    conn.commit()
    conn.close()
    logger.info("Database and table created")

def load_latest_transformed_file():
    files = glob(f"{INPUT_DIR}/transformed_data_*.csv")

    if not files:
        raise FileNotFoundError(f"No transformed files found in {INPUT_DIR}")

    latest_file = max(files, key=os.path.getctime)
    logger.info(f"Loading: {latest_file}")
    return pd.read_csv(latest_file)

def clean_data(df):
    """ Clean data before inserting into database"""
    # Convert Date to a clean string format (SQLite prefers string dates)
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    # Force columns to object type so None isn't converted back to NaN
    df = df.astype(object)

    # Replace NaN and infinity with native Python None (NULL in SQL)
    df = df.replace([float('inf'), float('-inf')], None)
    df = df.where(pd.notnull(df), None)

    return df

def insert_data(df):
    conn = sqlite3.connect(DB_PATH)

    """ Insert data into database"""
    column_mapping = {
        'Ticker': 'ticker',
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        'Daily_Return': 'daily_return',
        'SMA_20': 'sma_20',
        'SMA_50': 'sma_50',
        'RSI': 'rsi',
        'Volatility': 'volatility'
    }
    df = df.rename(columns=column_mapping)

    # Select only columns that exist in the database
    db_columns = list(column_mapping.values())
    df = df[db_columns]

    # Insert with REPLACE to handle duplicates
    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            conn.execute(f'''
                   INSERT OR REPLACE INTO stock_data 
                   ({', '.join(db_columns)})
                   VALUES ({', '.join(['?'] * len(db_columns))})
               ''', tuple(row))
            inserted += 1
        except Exception as e:
            logger.info(f"Skipped row: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    return inserted, skipped

def main():
    logger.info("=" * 60)
    logger.info("STOCK DATA LOAD")
    logger.info("=" * 60)

    create_database()

    # Load transformed data
    logger.info("\nLoading transformed data...")
    df = load_latest_transformed_file()
    logger.info(f"Loaded: {len(df)} rows")

    # Clean data
    logger.info("\nCleaning data...")
    df = clean_data(df)
    logger.info(f"Data cleaned")

    # Insert data in database
    logger.info("\nInserting data...")
    inserted, skipped = insert_data(df)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("LOAD COMPLETE")
    logger.info(f"  • Inserted: {inserted:,} rows")
    logger.info(f"  • Skipped: {skipped} rows")
    logger.info(f"  • Database: {DB_PATH}")
    logger.info("=" * 60)

    # Verify data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock_data")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT ticker) FROM stock_data")
    tickers = cursor.fetchone()[0]
    conn.close()

    logger.info(f"\nDatabase Stats:")
    logger.info(f"  • Total records: {total:,}")
    logger.info(f"  • Unique tickers: {tickers}")

if __name__ == "__main__":
    main()