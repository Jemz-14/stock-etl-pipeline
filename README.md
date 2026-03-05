# 📈 End-to-End Stock Market ETL & Analytics Pipeline

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Wrangling-150458.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)
![Seaborn](https://img.shields.io/badge/Seaborn-Data%20Viz-4C72B0.svg)

## 📌 Project Overview
An automated, production-ready ETL (Extract, Transform, Load) pipeline that fetches daily market data, calculates key technical indicators, loads the data into a relational database, and generates institutional-grade visualizations. 

I built this pipeline to automate quantitative analysis for a broader equity portfolio. Instead of manually scanning charts, this pipeline automatically flags overbought/oversold conditions, visualizes true capital flow (Dollar Volume), and maps the annualized risk-adjusted returns of target assets.

## 🏗️ Pipeline Architecture

The pipeline is orchestrated by a master `run_pipeline.py` script featuring automated logging, executing the following workflow:

1. **Extract (`extract.py`)**: Pulls the last 365 days of historical price and volume data for 10 target tickers via the Yahoo Finance API.
2. **Transform (`transform.py`)**: Cleans the data, handles missing values, and engineers new features using Pandas:
   * Daily Percentage Returns
   * 20-day and 50-day Simple Moving Averages (SMA)
   * 14-day Relative Strength Index (RSI)
   * 20-day Rolling Volatility
3. **Load (`load.py`)**: Inserts the transformed data into a local `SQLite` database (`stock_data.db`) using an Upsert (`INSERT OR REPLACE`) strategy to prevent duplication.
4. **Analyze (`analysis.py` & `query.py`)**: Executes complex SQL queries to screen for setups and generates automated Matplotlib/Seaborn visualizations.

## 📊 Analytical Output & Visualizations

The pipeline automatically renders the following reports:

### 1. Directional Market Volume Profile
*Visualizes true institutional capital flow by mapping price action directly over colour-coded daily volume (Green = Positive Return, Red = Negative Return) using a market proxy (SPY).*
![Volume Profile](data/visualisations/04_SPY_volume_profile.png)

### 2. Risk vs. Return Matrix
*Applies standard quantitative finance formulas (252 trading days) to map annualized portfolio volatility against expected returns, allowing for instant risk-adjusted performance screening.*
![Risk vs Return](data/visualisations/05_risk_vs_return.png)

### 3. Momentum Screener (14-Day RSI)
*A dynamic heatmap identifying overbought (>70) and oversold (<30) market conditions across the portfolio.*
![RSI Heatmap](data/visualisations/04_rsi_heatmap.png)

## 💻 Advanced SQL Implementation
Beyond Python transformations, the database is queried using advanced SQL techniques to track market performance. Example from `query.py` utilizing **Common Table Expressions (CTEs)** and **Window Functions**:

```sql
WITH MonthlyPerformance AS (
    SELECT
        strftime('%Y-%m', date) as month,  
        ticker,
        SUM(daily_return) * 100 as monthly_return_pct
    FROM stock_data
    GROUP BY month, ticker
),
RankedPerformers AS (                      
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
    MAX(CASE WHEN lose_rank = 1 THEN ticker END) AS biggest_loser
FROM RankedPerformers
GROUP BY month
ORDER BY month DESC;



## 🚀 How to Run
**1. Clone the repository**
```bash
git clone [https://github.com/Jemz-14/stock-etl-pipeline.git](https://github.com/Jemz-14/stock-etl-pipeline.git)
cd stock-etl-pipeline

**2. Install dependencies**
```bash
pip install -r requirements.txt

**3. Execute Pipeline
```bash
python run_pipeline.py