from polygon import RESTClient
from typing import cast
from urllib3 import HTTPResponse
import json
import pandas as pd
import datetime
import yfinance as yf
import numpy as np
import os




POLY_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://eodhd.com/api"
EODHD_API_KEY = os.getenv("EOD_API_KEY")  # Store securely in an environment variable

# Ensure the API key exists
if not POLY_API_KEY:
    raise ValueError("API key not found! Set the POLYGON_API_KEY environment variable.")

# Initialize REST Client with the secured API key
client = RESTClient(api_key=POLY_API_KEY)


# Path to CSV file for storing exchange and stock data
CSV_FILE_PATH = "cleaned_data.csv"
PROGRESS_FILE = "progress.json"

def load_market_data():
    """
    Load stock exchange and ticker data from a CSV file.

    Returns:
        pd.DataFrame: DataFrame containing exchanges and stock symbols.
    """
    if os.path.exists(CSV_FILE_PATH):
        return pd.read_csv(CSV_FILE_PATH)
    else:
        return pd.DataFrame(columns=["Symbol", "Name", "Country"])
    
# Predefined suggestions for technical indicators (Single timeframe mode)
predefined_suggestions = [
    "sma(period = )[-1]", "hma(period = )[-1]", "rsi(period = )[-1]",
    "ema(period = )[-1]", "slope_sma(period = )[-1]", "slope_ema(period = )[-1]",
    "slope_hma(period = )[-1]", "bb(period = , std_dev = , type = )[-1]",
    "macd(fast_period = , slow_period = , signal_period = , type = )[-1]", "Breakout",
    "atr(period = )[-1]", "cci(period = )[-1]", "roc(period = )[-1]", "WilliamSR(period = )[-1]",
    "psar(acceleration = , max_acceleration = )[-1]", "Close[-1]", "Open[-1]",
    "Low[-1]", "High[-1]"
]

# Predefined suggestions for multiple timeframes mode
predefined_suggestions_alt = [
    "sma(period = ,timeframe = )[-1]", "hma(period = ,timeframe = )[-1]",
    "rsi(period = ,timeframe = )[-1]", "ema(period = ,timeframe = )[-1]",
    "slope_sma(period = ,timeframe = )[-1]", "slope_ema(period = ,timeframe = )[-1]",
    "slope_hma(period = ,timeframe = )[-1]", "bb(period = , std_dev = , type = ,timeframe = )[-1]",
    "macd(fast_period = , slow_period = , signal_period = , type = ,timeframe = )[-1]", "Breakout",
    "atr(period = ,timeframe = )[-1]", "cci(period = ,timeframe = )[-1]",
    "roc(period = ,timeframe = )[-1]", "WilliamSR(period = ,timeframe = )[-1]",
    "psar(acceleration = , max_acceleration = ,timeframe = )[-1]", "Close(timeframe = )[-1]",
    "Open(timeframe = )[-1]", "Low(timeframe = )[-1]", "High(timeframe = )[-1]"
]

# Function to add blank spaces for UI formatting
def bl_sp(n):
    """Returns blank spaces for UI spacing in Streamlit."""
    return '\u200e ' * (n + 1)

# Function to fetch stock data using Polygon API
def grab_new_data_polygon(ticker, timespan = "day", multiplier = 1):

    today = datetime.datetime.today().strftime('%Y-%m-%d')
    last_year = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')

    aggs = cast(
        HTTPResponse,
        client.get_aggs(ticker=ticker, multiplier=1, timespan=timespan, from_=last_year, to=today, raw=True),
    )

    data_str = aggs.data.decode("utf-8")
    data = json.loads(data_str)
    df = pd.DataFrame(data["results"])

    df.sort_values(by="t", ascending=True, inplace=True)
    df["Date"] = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert("America/New_York")
    df["Date"] = df["Date"].dt.strftime("%d-%m-%Y %H:%M:%S %Z")

    df.rename(columns={
        "o": "Open",
        "c": "Close",
        "h": "High",
        "l": "Low",
        "v": "Volume",
        "vw": "VWAP",
        "n": "Trades"
    }, inplace=True)

    # Drop original timestamp column
    df.drop(columns=["t"], inplace=True)
    df.set_index("Date", inplace=True)

    return df
