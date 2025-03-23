import json
import os
import pandas as pd
#import schedule
import time
from utils import *
from indicators_lib import *
import datetime

# Main function to run daily
def run_daily_stock_check():
    print("📈 Running daily stock check...")
    
    alert_data = load_alert_data()
    stocks = get_all_stocks(alert_data, "1d")
    print(f"📊 Found {len(stocks)} stocks to process.")
    for stock in stocks:
        print(f"🔄 Processing {stock}...")

        # Fetch and update stock data
        exchange_for_stock = get_stock_exchange(alert_data, stock)
        new_stock_data = get_latest_stock_data(stock,exchange_for_stock,timespan="day")
        update_stock_database(stock, new_stock_data,timeframe="daily")
        
        # Calculate indicators
        calculate_technical_indicators(stock,"daily")

        # Check for alerts
        check_alerts(stock, alert_data, "daily")

    print("✅ Daily stock check completed.")


def run_weekly_stock_check():
    print("📈 Running weekly stock check...")
    
    alert_data = load_alert_data()
    stocks = get_all_stocks(alert_data, "1wk")
    print(f"📊 Found {len(stocks)} stocks to process.")
    for stock in stocks:
        print(f"🔄 Processing {stock}...")

        # Fetch and update stock data
        exchange_for_stock = get_stock_exchange(alert_data, stock)
        new_stock_data = get_latest_stock_data(stock,exchange_for_stock,timespan="week")
        update_stock_database(stock, new_stock_data,timeframe="weekly")
        
        # Calculate indicators
        calculate_technical_indicators(stock,"weekly")

        # Check for alerts
        check_alerts(stock, alert_data, "weekly")

    print("✅ Weekly stock check completed.")


run_weekly_stock_check()


# # Schedule the script to run once a day at 9:00 AM
# schedule.every().day.at("09:00").do(run_daily_stock_check)

# # Run the scheduler
# if __name__ == "__main__":
#     while True:
#         schedule.run_pending()
#         time.sleep(60)  # Check every minute
