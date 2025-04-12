from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import pytz
import pandas as pd
from backend import check_alerts
from utils import *
from indicators_lib import *
import time
import logging

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# Clear any existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# File handler: logs all messages (DEBUG and above) to a file.
file_handler = logging.FileHandler("update_stocks.log")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler: logs only minimal info (INFO and above) to the console.
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logger.info("Starting update_stocks script.")

# Attempt to load the CSV data
try:
    exchange_info = pd.read_csv("market_data.csv")
    logger.debug("CSV 'market_data.csv' loaded successfully.")
    logger.debug("CSV Columns: %s", exchange_info.columns.tolist())
except Exception as e:
    logger.error("Failed to load CSV file: %s", e)
    exit(1)

scheduler = BlockingScheduler(timezone=pytz.timezone("America/New_York"))

code_to_country = {
    "US": "USA",
    "AUS": "Australia",
    "BE": "Belgium",
    "IE": "Ireland",
    "PT": "Portugal",
    "FR": "France",
    "TR": "Turkey",
    "UK": "UK",
    "MX": "Mexico",
    "MI": "Italy",
    "DK": "Denmark",
    "FI": "Finland",
    "NO": "Norway",
    "CZ": "Czech Republic",
    "SW": "Switzerland",
    "ES": "Spain",
    "JP": "Japan",
    "AT": "Austria",
    "PL": "Poland",
    "DE": "Germany",
    "CA": "Canada",
    "GR": "Greece",
    "HU": "Hungary",
    "NL": "Netherlands"
}

def run_daily_stock_check_for_market(market_code):
    logger.info("Executing daily check for market '%s'.", market_code)
    today = datetime.datetime.now(pytz.timezone("America/New_York"))
    logger.debug("Today is %s %s", today.strftime("%Y-%m-%d %H:%M:%S"), today.strftime("%A"))
    
    if today.weekday() >= 5:
        logger.info("Weekend detected (%s). Skipping data fetch for %s.", today.strftime('%A'), market_code)
        return

    log_to_discord("\n")
    log_to_discord(f"📈 Running daily check for {market_code}...")
    
    alert_data = load_alert_data()
    logger.debug("Loaded alert data: %s", alert_data)

    market_alerts = [alert for alert in alert_data if alert.get("exchange") == market_code and alert.get("timeframe") == "1d"]
    logger.info("Found %d alerts for market '%s'.", len(market_alerts), market_code)
    
    stocks = {alert.get("ticker") for alert in market_alerts}
    logger.debug("Unique stocks to process for market '%s': %s", market_code, stocks)

    if not stocks:
        log_to_discord(f"⚠️ No stocks to process today for {market_code}.")
        return

    log_to_discord(f"📊 Processing {len(stocks)} stocks for {market_code}...")
    for stock in stocks:
        log_to_discord(f"🔄 Updating {stock}... with new data")
        logger.info("Updating stock: %s", stock)

        new_stock_data = get_latest_stock_data(stock, market_code, timespan="day")
        if new_stock_data.empty:
            log_to_discord(f"❌ No new data for {stock}.")
            logger.warning("No new data returned for stock: %s", stock)
            continue

        update_stock_database(stock, new_stock_data, timeframe="daily")
        check_alerts(stock, alert_data, "daily")

    log_to_discord(f"✅ Completed daily check for {market_code}.")
    flush_logs_to_discord()

def run_weekly_stock_check():
    logger.info("Executing weekly stock check.")
    today = datetime.datetime.now(pytz.timezone("America/New_York"))
    logger.debug("Today is %s %s", today.strftime("%Y-%m-%d %H:%M:%S"), today.strftime("%A"))
    
    if today.weekday() != 4:
        logger.info("Weekly check is scheduled only for Fridays. Today is %s.", today.strftime('%A'))
        return

    log_to_discord("\n")
    log_to_discord("📈 Running weekly stock check...")
    
    alert_data = load_alert_data()
    logger.debug("Loaded alert data for weekly check: %s", alert_data)

    stocks = get_all_stocks(alert_data, "1wk")
    logger.debug("Stocks to process for weekly check: %s", stocks)
    
    if not stocks:
        log_to_discord("⚠️ No weekly alerts to process today.")
        return

    log_to_discord(f"📊 Processing {len(stocks)} weekly stocks...")
    for stock in stocks:
        exchange_for_stock = get_stock_exchange(alert_data, stock)
        log_to_discord(f"🔄 Processing weekly data for {stock}...")
        logger.info("Processing weekly stock: %s on exchange '%s'", stock, exchange_for_stock)

        new_stock_data = get_latest_stock_data(stock, exchange_for_stock, timespan="week")
        if new_stock_data.empty:
            log_to_discord(f"❌ No new weekly data for {stock}.")
            logger.warning("No new weekly data returned for stock: %s", stock)
            continue

        update_stock_database(stock, new_stock_data, timeframe="weekly")
        check_alerts(stock, alert_data, "weekly")

    log_to_discord("✅ Weekly stock check completed.")
    flush_logs_to_discord()

# Global variable to keep track of markets that have already been scheduled.
scheduled_markets = set()

logger.debug("code_to_country mapping: %s", code_to_country)
logger.debug("Sample of loaded exchange_info data:")
logger.debug("\n%s", exchange_info.head().to_string())

# Initial scheduling for daily market-specific checks
alert_data = load_alert_data()
logger.debug("Initially loaded alert data: %s", alert_data)

daily_alerts = [alert for alert in alert_data if alert.get("timeframe") == "1d"]
logger.info("Found %d daily alerts.", len(daily_alerts))
markets = {alert.get("exchange") for alert in daily_alerts}
logger.debug("Unique markets extracted for daily alerts: %s", markets)
for market_code in markets:
    country_name = code_to_country.get(market_code, market_code)
    
    try:
        closing_time_str = exchange_info.loc[exchange_info["Country"] == country_name, "Closing Time (EST)"].iloc[0]
        logger.debug("For market '%s' (Country: %s), closing time string is: %s", market_code, country_name, closing_time_str)
    except Exception as e:
        logger.error("Unable to retrieve closing time for market '%s' (Country: %s): %s", market_code, country_name, e)
        continue

    try:
        closing_dt = datetime.datetime.strptime(closing_time_str.replace(" EST", ""), "%I:%M %p")
        logger.debug("Parsed closing_dt for market '%s': %s", market_code, closing_dt)
    except Exception as e:
        logger.error("Could not parse closing time for market '%s': %s", market_code, e)
        continue

    close_hour, close_min = closing_dt.hour, closing_dt.minute
    offset = 15 if market_code == "US" else 20
    run_hour = close_hour + ((close_min + offset) // 60)
    run_minute = (close_min + offset) % 60

    logger.info("Scheduling daily job for market '%s' at %d:%02d", market_code, run_hour, run_minute)
    scheduler.add_job(run_daily_stock_check_for_market, 'cron', args=[market_code],
                      day_of_week='mon-fri', hour=run_hour, minute=run_minute)
    scheduled_markets.add(market_code)

# Schedule weekly check (Friday after US market close)
logger.info("Scheduling weekly check job for Fridays at 16:15.")
scheduler.add_job(run_weekly_stock_check, 'cron', day_of_week='fri', hour=16, minute=15)

# Function to dynamically add daily jobs for markets not already scheduled.
def dynamic_market_scheduler():
    logger.debug("Running dynamic market scheduler...")
    alert_data = load_alert_data()
    new_markets = {alert.get("exchange") for alert in alert_data if alert.get("timeframe") == "1d"}
    logger.debug("dynamic_market_scheduler: found markets: %s", new_markets)
    for market in new_markets:
        if market not in scheduled_markets:
            logger.info("Dynamic scheduling: Adding daily job for new market: %s", market)
            country_name = code_to_country.get(market, market)
            try:
                closing_time_str = exchange_info.loc[exchange_info["Country"] == country_name, "Closing Time (EST)"].iloc[0]
                logger.debug("For dynamic market '%s' (Country: %s), closing time string is: %s", market, country_name, closing_time_str)
            except Exception as e:
                logger.error("Unable to retrieve closing time for dynamic market '%s' (Country: %s): %s", market, country_name, e)
                continue

            try:
                closing_dt = datetime.datetime.strptime(closing_time_str.replace(" EST", ""), "%I:%M %p")
                logger.debug("Parsed closing_dt for dynamic market '%s': %s", market, closing_dt)
            except Exception as e:
                logger.error("Could not parse closing time for dynamic market '%s': %s", market, e)
                continue

            close_hour, close_min = closing_dt.hour, closing_dt.minute
            offset = 15 if market == "US" else 20
            run_hour = close_hour + ((close_min + offset) // 60)
            run_minute = (close_min + offset) % 60
            logger.info("Dynamically scheduling daily job for market '%s' at %d:%02d", market, run_hour, run_minute)
            scheduler.add_job(run_daily_stock_check_for_market, 'cron', args=[market],
                              day_of_week='mon-fri', hour=run_hour, minute=run_minute)
            scheduled_markets.add(market)
    logger.debug("Dynamic market scheduler complete. Scheduled markets are now: %s", scheduled_markets)

# Schedule the dynamic market scheduler to run every minute
scheduler.add_job(dynamic_market_scheduler, 'interval', minutes=1)

logger.info("Scheduled Jobs:")
scheduler.print_jobs()



logger.info("Starting scheduler...")
try:
    logger.info("⏰ Scheduler running. Press Ctrl+C to exit.")
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    logger.info("🛑 Scheduler shutting down.")
    scheduler.shutdown()
3