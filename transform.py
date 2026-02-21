"""
transform.py - Stock Data Transformation
Calculates technical indicators and derived metrics
"""

import pandas as pd
import numpy as np
import os
from glob import glob
from datetime import datetime

INPUT_DIR = 'data/raw'
OUTPUT_DIR = 'data/processed'
SMA_PERIOD = [20,50] # Simple moving average
RSI_PERIOD = 14 # Standard period for RSI being 14 candles
VOLATILITY_WINDOW = 20 # 20 day rolling volatility

def calculate_returns(df):
    """ Calculate daily percentage returns"""
    df = df.sort_values(['Ticker','Date'])
    df['Daily return'] = df.groupby('Ticker')['Close'].pct_change()
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
    df['RSI'] = df.groupby('Ticker', group_keys=False).apply(rsi_for_ticker).values
    df['RSI'] = df['RSI'].round(2)
    return df