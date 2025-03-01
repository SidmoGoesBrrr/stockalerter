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
    
    # Load existing data (with proper datetime index)
    existing_data = check_database(stock)
    #convert all the data to UTC
    existing_data.index = pd.to_datetime(existing_data.index, utc=True)
    new_stock_data.index = pd.to_datetime(new_stock_data.index, utc=True)
    
    print("Existing data:")
    print(existing_data.tail())
    print(existing_data.head())
    print(len(existing_data))

    print("New data:")
    print(new_stock_data.tail())
    print(new_stock_data.head())
    print(len(new_stock_data))
    #print index
    print("Index:")
    print(existing_data.index)
    

    # print("Combined data:")
    # print(len(df_combined))
    # print("Combined data:")
    # print(len(combined_data))
    # print(combined_data.head())
    # #check the difference between the two dataframes
    # print("Difference between the two dataframes:")
    # print(combined_data[~combined_data.index.duplicated(keep=False)])
    # #clear the old file and write the new data
    
    # os.remove(file_path)
    # combined_data.to_csv(file_path, index=True, date_format="%Y-%m-%d")
    

def calculate_technical_indicators(stock):
    file_path = f"data/{stock}_daily.csv"
    df = pd.read_csv(file_path)

    # # Apply technical indicators (Ensure functions exist in indicators_lib)
    # df["SMA_30"] = simple_moving_average(df, 30)
    # df["SMA_45"] = simple_moving_average(df, 45)
    # df["SMA_15"] = simple_moving_average(df, 15)
    # df["RSI_60"] = relative_strength_index(df, 60)
    # df["RSI_70"] = relative_strength_index(df, 70)

    # Save updated file with indicators
    df.to_csv(file_path, index=False)

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
        #calculate_technical_indicators(stock)

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
