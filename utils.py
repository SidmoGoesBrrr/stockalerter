from polygon import RESTClient
from typing import cast
from urllib3 import HTTPResponse
import json
import pandas as pd
import datetime
import yfinance as yf
import talib
import numpy as np
import os
#import asyncio
import aiohttp
import time



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

# Function to fetch JSON data with error handling
async def fetch_json(session, url):
    """Fetch JSON response with error handling."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json",
    }
    async with session.get(url, headers=headers) as response:
        if response.status == 403:
            print(f"🚨 ERROR 403: Access Denied for URL: {url}")
            return []
        elif response.status == 401:
            print("🚨 ERROR 401: Invalid API Key!")
            return []
        elif response.status != 200:
            print(f"⚠️ ERROR {response.status}: {await response.text()}")
            return []

        return await response.json()

async def get_all_exchanges():
    """
    Fetch all supported stock exchanges dynamically using EODHD.
    Returns:
        list: A list of exchange codes.
    """
    url = f"{BASE_URL}/exchanges-list/?api_token={EODHD_API_KEY}&fmt=json"
    print("Sending request to:", url)
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)
    #Return a dict with code as key, also add the country and name
    return [{"Code": exchange["Code"], "Country": exchange["Country"], "Name": exchange["Name"]} for exchange in data]

async def get_all_stocks(session, exchange):
    """
    Fetch all stock symbols available for a given exchange using EODHD.

    Args:
        session: Shared aiohttp session for async requests.
        exchange (str): The exchange code (e.g., "NASDAQ", "NYSE", "NSE").

    Returns:
        list: A list of stock symbols.
    """
    url = f"{BASE_URL}/exchange-symbol-list/{exchange}?api_token={EODHD_API_KEY}&fmt=json"
    data = await fetch_json(session, url)
    #print the number of exchanges
    return [
            {
                "Exchange": exchange,
                "Code": stock.get("Code", "N/A"),
                "Name": stock.get("Name", "N/A"),
                "Country": stock.get("Country", "N/A"),
            }
            for stock in data
        ]
# Save progress to a file
def save_progress(completed_exchanges):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(completed_exchanges, f)

# Load progress from file
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return []

# Main function to fetch market data in batches
async def async_update_market_data():
    """
    Fetch and update market data, handling API limits (20 calls per day).
    """
    exchanges = await get_all_exchanges()  # Get list of exchanges
    completed_exchanges = load_progress()  # Load previously completed exchanges
    #get exchanges from dict as a list
    exchanges = [exchange["Code"] for exchange in exchanges]
    remaining_exchanges = [ex for ex in exchanges if ex not in completed_exchanges]

    if not remaining_exchanges:
        print("✅ All exchanges have been processed! Restarting from scratch.")
        # Reset progress
        save_progress([])
        remaining_exchanges = exchanges

    async with aiohttp.ClientSession() as session:
        while remaining_exchanges:
            batch = remaining_exchanges[:20]  # Take first 20 exchanges
            print(f"📦 Fetching stocks for batch: {batch}")

            tasks = [get_all_stocks(session, exchange) for exchange in batch]
            results = await asyncio.gather(*tasks)

            # Flatten results
            stock_data = []
            for result in results:
                print(result)
                #append the stock data, only the code and exchange
                result = [{"Exchange": stock["Exchange"], "Stock": stock["Code"]} for stock in result]
                print(result)
                stock_data.extend(result)

            # Save to CSV (append to avoid overwriting)
            df = pd.DataFrame(stock_data)
            df.to_csv(CSV_FILE_PATH, mode='a', index=False, header=not os.path.exists(CSV_FILE_PATH))

            # Update progress
            completed_exchanges.extend(batch)
            save_progress(completed_exchanges)

            print(f"✅ Completed {len(completed_exchanges)} of {len(exchanges)} exchanges.")

            # Wait 24 hours before the next batch
            print("⏳ Waiting 24 hours before the next batch...")
            time.sleep(86400)  # Sleep for 1 day


def update_market_data():
    """
    Synchronous wrapper to call async_update_market_data().
    """
    asyncio.run(async_update_market_data())  # Run the async function inside a synchronous call

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
