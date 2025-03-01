import json
import os
import pandas as pd
import schedule
import time
from utils import grab_new_data_polygon
from indicators_lib import *

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
        df = get_latest_stock_data(stock)
        # Save CSV with the date index intact (index=True)
        df.to_csv(file_path, index=True, date_format="%Y-%m-%d")
        return df
    else:
        # Read CSV and set the first column as the datetime index
        df = pd.read_csv(file_path, index_col=0)
        return df

    

def update_stock_database(stock, new_stock_data):
    file_path = f"data/{stock}_daily.csv"
    existing_data = check_database(stock)
    combined_data = new_stock_data[~new_stock_data.index.isin(existing_data.index)]
    df_combined = pd.concat([existing_data, combined_data]) 
    df_combined.to_csv(file_path, index=True, date_format="%Y-%m-%d")
    

def calculate_technical_indicators(stock):
    file_path = f"data/{stock}_daily.csv"
    df = pd.read_csv(file_path)
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
    df.to_csv(file_path, index=True, date_format="%Y-%m-%d")

# Evaluate alert conditions dynamically
def evaluate_condition(df, condition):
    pass

# Check if any alert conditions are met
def check_alerts(stock, alert_data):
    file_path = f"data/{stock}_daily.csv"
    df = pd.read_csv(file_path)
    
    if df.empty:
        print(f"⚠️ No data for {stock}, skipping alert check.")
        return

    alerts = get_all_alerts_for_stock(alert_data, stock)

    for alert in alerts:
        conditions = alert["conditions"]
        combination_logic = alert["combination_logic"]
        print("Checking alert:", alert["name"] + " for " + stock + " with conditions: " + str(conditions) + " and logic: " + str(combination_logic))

        results = []
        for condition_group in conditions:
            condition_result = evaluate_condition(df, condition_group["conditions"])
            results.append(condition_result)

        # Evaluate combination logic if present
        if combination_logic:
            logic_result = eval(combination_logic.replace("and", "and").replace("or", "or"))
        else:
            logic_result = all(results)  

        if logic_result:
            print(f"✅ ALERT TRIGGERED: {alert['name']} for {stock}")

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
        #check_alerts(stock, alert_data)

    print("✅ Daily stock check completed.")


run_daily_stock_check()

# # Schedule the script to run once a day at 9:00 AM
# schedule.every().day.at("09:00").do(run_daily_stock_check)

# # Run the scheduler
# if __name__ == "__main__":
#     while True:
#         schedule.run_pending()
#         time.sleep(60)  # Check every minute
