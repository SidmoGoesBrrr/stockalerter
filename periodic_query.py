from utils import update_market_data
import time

while True:
    update_market_data()
    time.sleep(86400)  # Sleep for 1 day
