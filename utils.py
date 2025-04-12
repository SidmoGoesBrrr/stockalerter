from polygon import RESTClient
from typing import cast
from urllib3 import HTTPResponse
import json
import pandas as pd
import datetime
from datetime import timezone
import yfinance as yf
import numpy as np
import os
import uuid
from indicators_lib import *
import requests
import time
import operator


MAX_DISCORD_MESSAGE_LENGTH = 2000
POLY_API_KEY = os.getenv("POLYGON_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_URL_LOGGING = os.getenv("WEBHOOK_URL_LOGGING")
LOG_BUFFER = []


# Ensure the API key exists
if not POLY_API_KEY:
    raise ValueError("API key not found! Set the POLYGON_API_KEY environment variable.")

# Initialize REST Client with the secured API key
client = RESTClient(api_key=POLY_API_KEY)


# Path to CSV file for storing exchange and stock data
CSV_FILE_PATH = "cleaned_data.csv"

# Path to CSV file for storing stock alerts
ALERTS_FILE_PATH = "alerts.json"

# Function to load stock exchange and ticker data from a CSV file
def load_market_data():
    if os.path.exists(CSV_FILE_PATH):
        return pd.read_csv(CSV_FILE_PATH)
    else:
        return pd.DataFrame(columns=["Symbol", "Name", "Country"])
    
# Predefined suggestions for technical indicators (Single timeframe mode)
predefined_suggestions = [
    "sma(period = )[-1]", 
    "hma(period = )[-1]", 
    "rsi(period = )[-1]",
    "ema(period = )[-1]", 
    "slope_sma(period = )[-1]", 
    "slope_ema(period = )[-1]",
    "slope_hma(period = )[-1]", 
    "bb(period = , std_dev = , type = )[-1]",
    "macd(fast_period = , slow_period = , signal_period = , type = )[-1]", 
    "breakout",
    "atr(period = )[-1]", 
    "cci(period = )[-1]", 
    "roc(period = )[-1]", 
    "williamsr(period = )[-1]",
    "Close[-1]", 
    "Open[-1]",
    "Low[-1]", 
    "High[-1]"
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

inverse_map = {'>': '<=', '<': '>=', '==': '!=', '!=': '==', '>=': '<', '<=': '>'}

# Function to add blank spaces for UI formatting
def bl_sp(n):
    """Returns blank spaces for UI spacing in Streamlit."""
    return '\u200e ' * (n + 1)



# Function to log messages to Discord
def log_to_discord(message: str):
    global LOG_BUFFER
    LOG_BUFFER.append(message)

# Function to split a long message into multiple code blocks
def split_message(message, max_length):
    lines = message.split("\n")
    chunks = []
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 < max_length - 6:  # 6 for code block fences
            current_chunk += line + "\n"
        else:
            chunks.append(f"```{current_chunk.strip()}```")
            current_chunk = line + "\n"
    if current_chunk:
        chunks.append(f"```{current_chunk.strip()}```")
    
    return chunks

# Function to flush log buffer to Discord
def flush_logs_to_discord():
    global LOG_BUFFER
    if not LOG_BUFFER:
        return

    full_message = "\n".join(LOG_BUFFER)
    messages = split_message(full_message, MAX_DISCORD_MESSAGE_LENGTH)

    for msg in messages:
        payload = {"content": msg}
        try:
            response = requests.post(WEBHOOK_URL_LOGGING, json=payload)
            response.raise_for_status()
            time.sleep(5)  # Delay to respect rate limits
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Discord message: {e}")
            break  # Exit on failure to prevent flooding

    LOG_BUFFER.clear()  # Clear buffer after successful sends

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


# Function to fetch stock data using Polygon API, works for international stocks too
def grab_new_data_yfinance(ticker, timespan = "1d", period = "1y"):
    df_yfinance = yf.download(ticker, period=period, interval=timespan,auto_adjust=True,multi_level_index=False,progress=False)
    # Calculate VWAP and store only VWAP in Yahoo Finance DataFrame
    # Helper function to ensure the column is a Series
    def get_series(column):
        series = df_yfinance[column]
        if isinstance(series, pd.DataFrame):
            # If the DataFrame has only one column, squeeze it to a Series.
            series = series.squeeze()
        return series

    df_yfinance["Typical Price"] = (get_series("High") + get_series("Low") + get_series("Close")) / 3
    df_yfinance["TP * Volume"] = df_yfinance["Typical Price"] * df_yfinance["Volume"]
    df_yfinance["Cumulative TP * Volume"] = df_yfinance["TP * Volume"].cumsum()
    df_yfinance["Cumulative Volume"] = df_yfinance["Volume"].cumsum()
    df_yfinance["VWAP"] = df_yfinance["Cumulative TP * Volume"] / df_yfinance["Cumulative Volume"]
    df_yfinance.index = df_yfinance.index.strftime("%d-%m-%Y 00:00:00 EDT")
    df = df_yfinance[["Volume", "VWAP", "Open", "Close", "High", "Low"]].copy()
    df[["VWAP", "Open", "Close", "High", "Low"]] = df[["VWAP", "Open", "Close", "High", "Low"]].round(3)

    return df



#Save an alert with multiple entry conditions as a JSON object in alerts.csv
def save_alert(name,entry_conditions_list, combination_logic, ticker, stock_name, exchange,timeframe,last_triggered, action):
    alert_id = str(uuid.uuid4())  
    # Load existing alerts if the JSON file exists
    try:
        with open(ALERTS_FILE_PATH, "r") as file:
            alerts = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        alerts = []  
    
    #if conditions are empty, return an error
    if not entry_conditions_list or ticker == "" or stock_name == "" or entry_conditions_list[0].get("conditions",[]) == []:
        raise ValueError("Entry conditions cannot be empty.")
    
    for alert in alerts:
        if alert["stock_name"] == stock_name and alert["ticker"] == ticker and alert["conditions"] == entry_conditions_list and alert["combination_logic"] == combination_logic and alert["exchange"] == exchange and alert["timeframe"] == timeframe:
            raise ValueError("Alert already exists with the same data fields.")

    new_alert = {
        "alert_id": alert_id,
        "name": name,  # Added name field
        "stock_name": stock_name,
        "ticker": ticker,
        "conditions": entry_conditions_list,
        "combination_logic": combination_logic,
        "last_triggered": last_triggered,
        "action": action,
        "timeframe": timeframe,
        "exchange": exchange
    }

    

    # Append the new alert
    alerts.append(new_alert)

    # Save back to the file
    with open(ALERTS_FILE_PATH, "w") as file:
        json.dump(alerts, file, indent=4)

    print(f"Alert {alert_id} saved successfully.")


## FOR update_stocks.py ONLY
# Load alert data from JSON file
def load_alert_data():
    with open("alerts.json", "r") as file:
        return json.load(file)


# Get all unique stock tickers from alert data
def get_all_stocks(alert_data,timeframe):
    return list(set([alert['ticker'] for alert in alert_data if alert['timeframe'] == timeframe]))

#get exchange of a stock
def get_stock_exchange(alert_data, stock):
    return [alert['exchange'] for alert in alert_data if alert['ticker'] == stock][0]

# Get all alerts related to a specific stock
def get_all_alerts_for_stock(alert_data, stock):
    return [alert for alert in alert_data if alert['ticker'] == stock]

# Fetch the latest stock data
def get_latest_stock_data(stock, exchange, timespan):
    if exchange == "US":
        df = grab_new_data_polygon(stock, timespan=timespan, multiplier=1)
    else:
        if timespan == "day":
            timespan_yfinance = "1d"
        elif timespan == "week":
            timespan_yfinance = "1wk"
        df = grab_new_data_yfinance(stock, timespan=timespan_yfinance, period="1y")
    return df


# Load or create the historical database for a stock
def check_database(stock,timeframe):
    file_path = f"data/{stock}_{timeframe}.csv"

    if not os.path.exists(file_path):
        print(f"📥 No existing data for {stock}, fetching new data...")
        exchange = get_stock_exchange(load_alert_data(), stock)
        timeframe = "day" if timeframe == "daily" else "week"
        df = get_latest_stock_data(stock, exchange,timeframe)
        df.reset_index(inplace=True)  # Move Date index to a column
        df.insert(0, "index", range(1, len(df) + 1))
        df.to_csv(file_path, index=False, date_format="%Y-%m-%d")
        return df

    else:
        df = pd.read_csv(file_path)
        # Drop any extra unnamed columns that may have been added in previous runs
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        # Ensure that if an "index" column exists, it is of integer type; if not, create one.
        if 'index' in df.columns:
            df['index'] = df['index'].astype(int)
        else:
            df.insert(0, "index", range(1, len(df) + 1))
        return df

    

def update_stock_database(stock, new_stock_data,timeframe):
    file_path = f"data/{stock}_{timeframe}.csv"
    
    # Load existing data
    existing_data = check_database(stock,timeframe)

    # Ensure new_stock_data has the same structure
    new_stock_data.reset_index(inplace=True)  # Convert Date index to column
    new_stock_data = new_stock_data[~new_stock_data["Date"].isin(existing_data["Date"])]

    df_combined = pd.concat([existing_data, new_stock_data])
    df_combined.reset_index(drop=True, inplace=True)
        
    # Regenerate the "index" column to be consistent
    df_combined['index'] = range(1, len(df_combined) + 1)
    cols = df_combined.columns.tolist()
    if 'index' in cols:
        cols.insert(0, cols.pop(cols.index('index')))
    df_combined = df_combined[cols]
    
    # Save the combined data consistently without using pandas' default index
    df_combined.to_csv(file_path, index=False, date_format="%Y-%m-%d")
    
    return df_combined

    
def send_alert(stock, alert, condition_str, df):
    # Ensure the condition_str is actually a string
    if not isinstance(condition_str, str):
        print(f"[Alert Check] Provided condition is not a string: {condition_str}")
        return

    current_price = df.iloc[-1]['Close']
    # Add action to the alert
    action = alert['action']
    timeframe = alert['timeframe']
    # Send the alert via Discord
    send_stock_alert(WEBHOOK_URL, timeframe, alert["name"], stock, condition_str,current_price, action)
    log_to_discord(f"[Alert Triggered] '{alert['name']}' for {stock}: condition '{condition_str}' at {datetime.datetime.now()}.")


def send_stock_alert(webhook_url, timeframe,alert_name, ticker, triggered_condition, current_price, action):
    # Change the color based on the action
    color = 0x00ff00 if action == "Buy" else 0xff0000
    timeframe = "Daily" if timeframe == "1d" else "Weekly"
    embed = {
        "title": f"📈 {timeframe} Alert Triggered: {alert_name} ({ticker})",
        "description": f"The condition **{triggered_condition}** was triggered. \n Action: {action}",
        "fields": [
            {
                "name": "Current Price",
                "value": f"${current_price:.2f}",
                "inline": True
            }
        ],
        "color": color,  # Default green color.
        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
        }

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("Alert sent successfully!")
        else:
            print(f"Failed to send alert. HTTP Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")




ops = {
    '>': operator.gt,
    '<': operator.lt,
    '==': operator.eq,
    '>=': operator.ge,
    '<=': operator.le,
    '!=': operator.ne
}

supported_indicators = {
    "sma": SMA,
    "ema": EMA,
    "hma": HMA,
    "slope_sma": SLOPE_SMA,
    "slope_ema": SLOPE_EMA,
    "slope_hma": SLOPE_HMA,
    "rsi": RSI,
    "atr": ATR,
    "cci": CCI,
    "bb": BBANDS,
    "roc": ROC,
    "williamsr": WILLR,
    "macd": MACD,
    "psar": SAR
}

period_and_input = ['sma','ema','rsi','hma','slope_sma','slope_ema','slope_hma','roc']

period_only = ['sma','ema','rsi','hma','slope_sma','slope_ema','slope_hma','roc', 'atr', 'cci', 'willr', 'bbands']