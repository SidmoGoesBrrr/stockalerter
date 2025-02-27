import requests
from datetime import datetime
import time

def send_stock_alert(webhook_url, stock_name, current_price, alert_price, action):
    """
    Sends a stock alert embed to a Discord channel using a webhook.

    :param webhook_url: The Discord webhook URL
    :param stock_name: The name of the stock
    :param current_price: The current price of the stock
    :param alert_price: The price at which the alert was triggered
    :param action: Suggested action (e.g., "Buy", "Sell", "Hold")
    """

    embed = {
        "title": f"📈 Stock Alert: {stock_name}",
        "description": f"The stock **{stock_name}** has reached a significant price point.",
        "color": 15158332 if action.lower() == "sell" else 3066993,  # Red for Sell, Green for Buy/Hold
        "fields": [
            {"name": "📊 Current Price", "value": f"${current_price:.2f}", "inline": True},
            {"name": "🚨 Alert Price", "value": f"${alert_price:.2f}", "inline": True},
            {"name": "📋 Suggested Action", "value": f"**{action}**"},
        ],
        "footer": {
            "text": "Stay informed and make wise investment decisions!",
            "icon_url": "https://i.imgur.com/aXZrdaK.png"  # Example footer icon (change if needed)
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("Stock alert sent successfully!")
        else:
            print(f"Failed to send stock alert. HTTP Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Replace with your actual Discord webhook URL
webhook_url = "https://discord.com/api/webhooks/1333550802505175061/gaHiFHU2-nEiK4Niz5kyJY0YcDTCMXxpwsE5gbVeFdwJ8shW8yWMXxjpZtu8Hap0WefE"
# Example stock alert details
stock_name = "AAPL"
current_price = 175.50
alert_price = 180.00
action = "Buy"

while True:
    # Sleep for 24 hours (86400 seconds) after executing the task
    time.sleep(86400)
    send_stock_alert(webhook_url, stock_name, current_price, alert_price, action)  