import requests
from datetime import datetime, timezone

#Send the stock alert to the Discord webhook URL.
#The alert_name is the name of the alert, ticker is the stock ticker, triggered_condition is the condition that was triggered, 
# triggered_value is the value that triggered the alert, and current_price is the current price of the stock.
def send_stock_alert(webhook_url, alert_name, ticker, triggered_condition, triggered_value, current_price):
    embed = {
        "title": f"📈 Alert Triggered: {alert_name} ({ticker})",
        "description": f"The condition **{triggered_condition}** was triggered with a value of **{triggered_value}**.",
        "fields": [
            {
                "name": "Current Price",
                "value": f"${current_price:.2f}",
                "inline": True
            }
        ],
        "color": 3066993,  # Default green color.
        "timestamp": datetime.now(timezone.utc).isoformat()
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