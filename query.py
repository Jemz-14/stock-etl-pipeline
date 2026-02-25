import pandas as pd
import sqlite3

DB_PATH = 'data/stock_data.db'

# Connect and run sample queries
conn = sqlite3.connect(DB_PATH)

print("=" * 60)
print("TEST QUERIES")
print("=" * 60)


# Query 1: Latest prices for all tickers
print("\n Latest Close Prices")
query1 = """
    SELECT ticker,date, close, daily_return, rsi
    FROM stock_data
    WHERE date = (SELECT MAX(date) FROM stock_data)
    ORDER BY ticker
"""
df1 = pd.read_sql_query(query1, conn)
print(df1)


# Query 2: Best performing stocks (last 30 days)
print("\n2. Best Performers (30d avg return):")
query2 = """
    SELECT 
        ticker,
        AVG(daily_return) as avg_return,
        AVG(volatility) as avg_volatility
    FROM stock_data
    WHERE date >= date('now', '-30 days')
    GROUP BY ticker
    ORDER BY avg_return DESC
"""

df2 = pd.read_sql_query(query2, conn)
print(df2)

# Query 3: Extreme RSI Screener (Overbought/Oversold)
print("\n3. Extreme RSI Screener (Overbought or Oversold Today):")
query3 = """
    SELECT 
        ticker, 
        date, 
        close, 
        rsi
    FROM stock_data
    WHERE date = (SELECT MAX(date) FROM stock_data)
      AND (rsi < 30 OR rsi > 70)
    ORDER BY rsi ASC
"""
df3 = pd.read_sql_query(query3, conn)
print(df3)

# Query 4: Best and Worst performing stock per month
print("\n Monthly Best and Worst performing stocks")
query4 = """
    WITH MonthlyPerformance AS (
        SELECT
            strftime('%Y-%m', date) as month,  -- FIX 1: Changed 'as date' to 'as month'
            ticker,
            SUM(daily_return) * 100 as monthly_return_pct
        FROM stock_data
        GROUP BY month, ticker
    ),
    RankedPerformers AS (                      -- FIX 2: Added the 's' to match the bottom query
        SELECT 
            month,
            ticker,
            monthly_return_pct,
            ROW_NUMBER() OVER(PARTITION BY month ORDER BY monthly_return_pct DESC) as win_rank,
            ROW_NUMBER() OVER(PARTITION BY month ORDER BY monthly_return_pct ASC) as lose_rank
        FROM MonthlyPerformance
    )
    SELECT 
        month,
        MAX(CASE WHEN win_rank = 1 THEN ticker END) as biggest_winner,
        ROUND(MAX(CASE WHEN win_rank = 1 THEN monthly_return_pct END), 2) AS win_pct,
        MAX(CASE WHEN lose_rank = 1 THEN ticker END) AS biggest_loser,
        ROUND(MAX(CASE WHEN lose_rank = 1 THEN monthly_return_pct END), 2) AS lose_pct
    FROM RankedPerformers
    GROUP BY month
    ORDER BY month DESC;
"""
df4 = pd.read_sql_query(query4, conn)
print(df4)

# Query 5: Stocks overall return for the 1 year period
print("\n5. Stocks overall return for the 1 year period:")
query5 = """
    WITH RankedDates AS (
        -- Assign a rank to the oldest date (first_row) and newest date (last_row) for each ticker
        SELECT 
            ticker,
            date,
            close,
            ROW_NUMBER() OVER(PARTITION BY ticker ORDER BY date ASC) as first_row,
            ROW_NUMBER() OVER(PARTITION BY ticker ORDER BY date DESC) as last_row
        FROM stock_data
    )
    SELECT
        FirstDay.ticker,
        FirstDay.date AS start_date,
        LastDay.date as end_date,                                
        ROUND(FirstDay.close, 2) AS start_price,                 
        ROUND(LastDay.close, 2) AS end_price,                    
        ROUND(((LastDay.close - FirstDay.close) / FirstDay.close) * 100, 2) AS percent_change
    FROM RankedDates FirstDay
    INNER JOIN RankedDates LastDay ON FirstDay.ticker = LastDay.ticker
    WHERE FirstDay.first_row = 1 AND LastDay.last_row = 1
    ORDER BY percent_change DESC                                 
"""
df5 = pd.read_sql_query(query5, conn)
print(df5)