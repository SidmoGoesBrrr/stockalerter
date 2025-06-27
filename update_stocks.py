import datetime
import logging

import pandas as pd
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

from backend import check_alerts
from indicators_lib import *
from utils import *

# Toggle debug mode
IS_DEBUG = True

# Create timezone-aware formatter for EST
class ESTFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp, pytz.timezone("America/New_York"))
        return dt

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

# Set up logger
logger = logging.getLogger("StockUpdater")
log_level = logging.DEBUG if IS_DEBUG else logging.INFO
logger.setLevel(log_level)

# Clear any existing handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Define formatter with EST
formatter = ESTFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# File handler (always logs everything)
file_handler = logging.FileHandler("update_stocks.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler (respects debug toggle)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("Starting update_stocks script...")

# Load CSV

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
    successes, failures = [], []

    for stock in stocks:


        log_to_discord(f"🔄 Updating {stock}... with new data")
        logger.info("Updating stock: %s", stock)

        new_stock_data = get_latest_stock_data(stock, market_code, timespan="day")
        if new_stock_data.empty:
            failures.append(stock)
            continue
        else:
            successes.append(stock)

        update_stock_database(stock, new_stock_data, timeframe="daily")
        check_alerts(stock, alert_data, "daily")
    logger.info("📈 Summary for %s — Success: %s, Failed: %s", market_code, successes, failures)

    log_to_discord(f"✅ Completed daily check for {market_code}.")
    flush_logs_to_discord()

def run_weekly_stock_check_for_market(market_code):
    logger.info("Executing weekly check for market '%s'.", market_code)
    today = datetime.datetime.now(pytz.timezone("America/New_York"))
    logger.debug("Today is %s %s", today.strftime("%Y-%m-%d %H:%M:%S"), today.strftime("%A"))

    # Run only on Friday (weekday==4)
    if today.weekday() != 4:
        logger.info("Today is not Friday. Skipping weekly data fetch for %s.", market_code)
        return

    log_to_discord("\n")
    log_to_discord(f"📈 Running weekly check for {market_code}...")

    alert_data = load_alert_data()
    logger.debug("Loaded alert data for weekly check: %s", alert_data)

    market_weekly_alerts = [alert for alert in alert_data if alert.get("exchange") == market_code and alert.get("timeframe") == "1wk"]
    logger.info("Found %d weekly alerts for market '%s'.", len(market_weekly_alerts), market_code)

    stocks = {alert.get("ticker") for alert in market_weekly_alerts}
    logger.debug("Unique stocks to process for weekly market '%s': %s", market_code, stocks)

    if not stocks:
        log_to_discord(f"⚠️ No stocks to process this week for {market_code}.")
        return

    log_to_discord(f"📊 Processing {len(stocks)} stocks for weekly check in {market_code}...")
    for stock in stocks:
        log_to_discord(f"🔄 Updating weekly data for {stock}...")
        logger.info("Updating weekly stock: %s", stock)

        new_stock_data = get_latest_stock_data(stock, market_code, timespan="week")
        if new_stock_data.empty:
            log_to_discord(f"❌ No new weekly data for {stock}.")
            logger.warning("No new weekly data returned for stock: %s", stock)
            continue

        update_stock_database(stock, new_stock_data, timeframe="weekly")
        check_alerts(stock, alert_data, "weekly")

    log_to_discord(f"✅ Completed weekly check for {market_code}.")
    flush_logs_to_discord()


# Global variable to keep track of markets that have already been scheduled.
scheduled_markets = set()
scheduled_weekly_markets = set()

logger.debug("code_to_country mapping: %s", code_to_country)


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

# Schedule weekly jobs for each market that has weekly alerts
weekly_alerts = [alert for alert in alert_data if alert.get("timeframe") == "1wk"]
logger.info("Found %d weekly alerts.", len(weekly_alerts))
weekly_markets = {alert.get("exchange") for alert in weekly_alerts}
for market_code in weekly_markets:
    country_name = code_to_country.get(market_code, market_code)

    try:
        closing_time_str = exchange_info.loc[exchange_info["Country"] == country_name, "Closing Time (EST)"].iloc[0]
        logger.debug("For weekly market '%s' (Country: %s), closing time string is: %s", market_code, country_name, closing_time_str)
    except Exception as e:
        logger.error("Unable to retrieve closing time for weekly market '%s' (Country: %s): %s", market_code, country_name, e)
        continue

    try:
        closing_dt = datetime.datetime.strptime(closing_time_str.replace(" EST", ""), "%I:%M %p")
        logger.debug("Parsed closing_dt for weekly market '%s': %s", market_code, closing_dt)
    except Exception as e:
        logger.error("Could not parse closing time for weekly market '%s': %s", market_code, e)
        continue

    close_hour, close_min = closing_dt.hour, closing_dt.minute
    offset = 15 if market_code == "US" else 20
    run_hour = close_hour + ((close_min + offset) // 60)
    run_minute = (close_min + offset) % 60

    logger.info("Scheduling weekly job for market '%s' at %d:%02d", market_code, run_hour, run_minute)
    scheduler.add_job(run_weekly_stock_check_for_market, 'cron', args=[market_code],
                      day_of_week='fri', hour=run_hour, minute=run_minute)
    scheduled_weekly_markets.add(market_code)


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
            logger.info("✔️ Daily job for %s scheduled at %02d:%02d", market, run_hour, run_minute)
            scheduler.add_job(run_daily_stock_check_for_market, 'cron', args=[market],
                              day_of_week='mon-fri', hour=run_hour, minute=run_minute)
            scheduled_markets.add(market)

    new_markets_weekly = {alert.get("exchange") for alert in alert_data if alert.get("timeframe") == "1wk"}
    for market in new_markets_weekly:
        if market not in scheduled_weekly_markets:
            logger.info("Dynamic scheduling: Adding weekly job for new market: %s", market)
            country_name = code_to_country.get(market, market)
            try:
                closing_time_str = exchange_info.loc[exchange_info["Country"] == country_name, "Closing Time (EST)"].iloc[0]
                logger.debug("For dynamic weekly market '%s' (Country: %s), closing time string is: %s", market, country_name, closing_time_str)
            except Exception as e:
                logger.error("Unable to retrieve closing time for dynamic weekly market '%s' (Country: %s): %s", market, country_name, e)
                continue

            try:
                closing_dt = datetime.datetime.strptime(closing_time_str.replace(" EST", ""), "%I:%M %p")
                logger.debug("Parsed closing_dt for dynamic weekly market '%s': %s", market, closing_dt)
            except Exception as e:
                logger.error("Could not parse closing time for dynamic weekly market '%s': %s", market, e)
                continue

            close_hour, close_min = closing_dt.hour, closing_dt.minute
            offset = 15 if market == "US" else 20
            run_hour = close_hour + ((close_min + offset) // 60)
            run_minute = (close_min + offset) % 60

            logger.info("Dynamically scheduling weekly job for market '%s' at %d:%02d", market, run_hour, run_minute)
            scheduler.add_job(run_weekly_stock_check_for_market, 'cron', args=[market],
                              day_of_week='fri', hour=run_hour, minute=run_minute)
            scheduled_weekly_markets.add(market)


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
