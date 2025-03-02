import json
import os
import pandas as pd
import schedule
import time
from utils import grab_new_data_polygon
from webhook_alerts import send_stock_alert
from indicators_lib import *
import datetime

# Load alert data from JSON file
def load_alert_data():
    with open("alerts.json", "r") as file:
        return json.load(file)



# Get all unique stock tickers from alert data
def get_all_stocks(alert_data):
    return list(set([alert['ticker'] for alert in alert_data]))

# Get all alerts related to a specific stock
def get_all_alerts_for_stock(alert_data, stock):
    return [alert for alert in alert_data if alert['ticker'] == stock]

# Fetch the latest stock data
def get_latest_stock_data(stock):
    df = grab_new_data_polygon(stock, timespan="day", multiplier=1)
    return df



# Load or create the historical database for a stock
def check_database(stock):
    file_path = f"data/{stock}_daily.csv"

    if not os.path.exists(file_path):
        print(f"📥 No existing data for {stock}, fetching new data...")
        df = get_latest_stock_data(stock)
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

    

def update_stock_database(stock, new_stock_data):
    file_path = f"data/{stock}_daily.csv"
    
    # Load existing data
    existing_data = check_database(stock)

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


def calculate_technical_indicators(stock):
    file_path = f"data/{stock}_daily.csv"
    df = pd.read_csv(file_path)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    original_columns = df.columns.tolist()

    # Identify columns that follow the indicator pattern (e.g. SMA_45)
    indicator_cols = [
        col for col in original_columns
        if '_' in col and col.split('_')[0].upper() in 
           {'SMA', 'EMA', 'HMA', 'SLOPE_SMA', 'SLOPE_EMA', 'SLOPE_HMA',
            'RSI', 'ATR', 'CCI', 'BBANDS', 'ROC', 'WILLR', 'MACD', 'SAR'}
    ]
    
    # Process each indicator column
    for col in indicator_cols:
        parts = col.split('_')
        indicator_name = parts[0].upper()
        try:
            timeperiod = int(parts[1])
        except ValueError:
            # Skip if the timeframe part is not a valid integer
            continue

        if indicator_name == 'SMA':
            df[col] = SMA(df, timeperiod)
        elif indicator_name == 'EMA':
            df[col] = EMA(df, timeperiod)
        elif indicator_name == 'HMA':
            df[col] = HMA(df, timeperiod)
        elif indicator_name == 'SLOPE_SMA':
            df[col] = SLOPE_SMA(df, timeperiod)
        elif indicator_name == 'SLOPE_EMA':
            df[col] = SLOPE_EMA(df, timeperiod)
        elif indicator_name == 'SLOPE_HMA':
            df[col] = SLOPE_HMA(df, timeperiod)
        elif indicator_name == 'RSI':
            df[col] = RSI(df, timeperiod)
        elif indicator_name == 'ATR':
            df[col] = ATR(df, timeperiod)
        elif indicator_name == 'CCI':
            df[col] = CCI(df, timeperiod)
        elif indicator_name == 'ROC':
            df[col] = ROC(df, timeperiod)
        elif indicator_name == 'WILLR':
            df[col] = WILLR(df, timeperiod)
        elif indicator_name == 'BBANDS':
            # Defaults: standard deviation 2, and choosing the 'middle' band.
            std_dev_val = 2
            line_type = 'middle'
            df[col] = BBANDS(df, timeperiod, std_dev_val, line_type)
        elif indicator_name == 'MACD':
            # Defaults for MACD: fast=12, slow=26, signal=9, and using 'line' type.
            fast_period = 12
            slow_period = 26
            signal_period = 9
            line_type = 'line'
            df[col] = MACD(df, fast_period, slow_period, signal_period, line_type)
        elif indicator_name == 'SAR':
            # Defaults for SAR
            acceleration = 0.02
            max_acceleration = 0.2
            df[col] = SAR(df, acceleration, max_acceleration)

    # Reassemble the DataFrame so that all original (non-indicator) columns like Volume are preserved.
    non_indicator_cols = [col for col in original_columns if col not in indicator_cols]
    df = df[non_indicator_cols + indicator_cols]
    
    # Save updated file with indicators
    df.to_csv(file_path, index=False, date_format="%Y-%m-%d")

# Evaluate alert conditions dynamically
def evaluate_indicator_condition(condition_str, df):
    """
    Evaluates an indicator condition string of the format 'sma(period = 30)[-1]'
    and returns the value from the corresponding column in the dataframe at the specified index.
    """
    try:
        # Remove spaces and make lowercase for uniform processing
        cs = condition_str.replace(" ", "").lower()
        # Extract the indicator name (e.g., "sma")
        func_name = cs.split("(")[0]
        # Extract the period value from within the parentheses, e.g., "period=30"
        inside = cs[cs.find("(") + 1: cs.find(")")]
        period = int(inside.split("=")[1])
        # Extract the index value from the square brackets, e.g., "[-1]" or "[-2]"
        index_start = cs.find("[")
        index_end = cs.find("]")
        if index_start == -1 or index_end == -1 or index_end < index_start:
            print(f"[Alert Check] No valid index found in condition '{condition_str}', defaulting to -1.")
            idx = -1
        else:
            idx_str = cs[index_start + 1:index_end]
            idx = int(idx_str)
        # Construct the expected column name (e.g., "SMA_30")
        col_name = f"{func_name.upper()}_{period}"
        if col_name not in df.columns:
            print(f"[Alert Check] Column '{col_name}' not found in dataframe.")
            return None
        # Return the value from the specified row for that indicator column
        return df.iloc[idx][col_name]
    except Exception as e:
        print(f"[Alert Check] Error evaluating condition '{condition_str}': {e}")
        return None
    
def send_alert(stock, alert, condition_str, df):
    """
    Sends a Discord alert via webhook when an alert condition is met.
    
    Parameters:
      - stock: Stock ticker (e.g., 'AAPL')
      - alert: The alert dict from alerts.json
      - condition_str: The condition string that triggered the alert (e.g., "sma(period = 30)[-1]")
      - df: The stock dataframe (used for evaluating the condition and obtaining the current price)
    """
    # Ensure the condition_str is actually a string
    if not isinstance(condition_str, str):
        print(f"[Alert Check] Provided condition is not a string: {condition_str}")
        return

    # Evaluate the condition to get the triggered value using the index extracted from the condition string
    triggered_value = evaluate_indicator_condition(condition_str, df)
    triggered_value = round(triggered_value, 2) if triggered_value is not None else None
    if triggered_value is None:
        print(f"[Alert Check] Could not evaluate condition '{condition_str}' for {stock}.")
        return

    # Use the latest closing price as the current price
    current_price = df.iloc[-1]['Close']
    webhook_url = "https://discord.com/api/webhooks/1333550802505175061/gaHiFHU2-nEiK4Niz5kyJY0YcDTCMXxpwsE5gbVeFdwJ8shW8yWMXxjpZtu8Hap0WefE"
    
    # Send the alert via Discord
    send_stock_alert(webhook_url, alert["name"], stock, condition_str, triggered_value,current_price)
    print(f"[Alert Triggered] '{alert['name']}' for {stock}: condition '{condition_str}' evaluated to {triggered_value} at {datetime.datetime.now()}.")
    #TODO: Update the last_triggered field in alerts.json

def check_alerts(stock, alert_data):
    
    file_path = f"data/{stock}_daily.csv"
    df = pd.read_csv(file_path)
    
    if df.empty:
        print(f"[Alert Check] No data for {stock}, skipping alert check.")
        return

    # Filter alerts for this stock (case-insensitive ticker match)
    alerts = [alert for alert in alert_data if alert['ticker'].upper() == stock.upper()]
    
    for alert in alerts:
        condition_groups = alert.get("conditions", [])
        combination_logic = alert.get("combination_logic", "").strip().lower()
        group_results = []
        
        for group in condition_groups:
            cond_list = group.get("conditions", [])
            if len(cond_list) != 3:
                print(f"[Alert Check] Invalid condition format in alert '{alert['name']}'. Skipping this group.")
                group_results.append(False)
                continue
            
            lhs_str, operator, rhs_str = cond_list
            lhs_value = evaluate_indicator_condition(lhs_str, df)
            rhs_value = evaluate_indicator_condition(rhs_str, df)
            
            if lhs_value is None or rhs_value is None:
                print(f"[Alert Check] Could not evaluate condition in alert '{alert['name']}'.")
                group_results.append(False)
                continue

            # Evaluate the condition based on the operator
            if operator == "==":
                result = lhs_value == rhs_value
            elif operator == "!=":
                result = lhs_value != rhs_value
            elif operator == ">":
                result = lhs_value > rhs_value
            elif operator == "<":
                result = lhs_value < rhs_value
            elif operator == ">=":
                result = lhs_value >= rhs_value
            elif operator == "<=":
                result = lhs_value <= rhs_value
            else:
                print(f"[Alert Check] Unsupported operator '{operator}' in alert '{alert['name']}'.")
                result = False

            group_results.append(result)
            print(f"[Alert Check] '{alert['name']}': Evaluated condition '{lhs_str} {operator} {rhs_str}' with values {lhs_value} {operator} {rhs_value} -> {result}")

        # Combine the results based on the combination logic ("or" vs. default "and")
        if combination_logic == "or":
            alert_triggered = any(group_results)
        else:
            alert_triggered = all(group_results)

        if alert_triggered:
            # For demonstration, use the lhs_value from the last evaluated condition as the triggered value
            send_alert(stock, alert, lhs_str, df)
            
        else:
            print(f"[Alert Check] '{alert['name']}' not triggered for {stock}.")

# Main function to run daily
def run_daily_stock_check():
    print("📈 Running daily stock check...")
    
    alert_data = load_alert_data()
    stocks = get_all_stocks(alert_data)
    
    for stock in stocks:
        print(f"🔄 Processing {stock}...")

        # Fetch and update stock data
        new_stock_data = get_latest_stock_data(stock)
        update_stock_database(stock, new_stock_data)
        
        # Calculate indicators
        calculate_technical_indicators(stock)

        # Check for alerts
        check_alerts(stock, alert_data)

    print("✅ Daily stock check completed.")


run_daily_stock_check()

# # Schedule the script to run once a day at 9:00 AM
# schedule.every().day.at("09:00").do(run_daily_stock_check)

# # Run the scheduler
# if __name__ == "__main__":
#     while True:
#         schedule.run_pending()
#         time.sleep(60)  # Check every minute
