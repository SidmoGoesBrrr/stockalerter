import streamlit as st
import json
import pandas as pd

st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
)

# Function to format conditions
def format_conditions(conditions):
    return " AND ".join([" ".join(condition["conditions"]) for condition in conditions])

def add_stock_alert():
    st.title("Add a New Stock Alert")

# Load alert data from JSON file
def load_alert_data():
    with open("alerts.json", "r") as file:
        return json.load(file)

# Save updated alert data to JSON file
def save_alert_data(alert_data):
    with open("alerts.json", "w") as file:
        json.dump(alert_data, file, indent=4)

alert_data = load_alert_data()



st.header("Active Stock Alerts")
st.write("Here are the active stock alerts that you have set up:")



search_query = st.text_input("Search alerts by alert name, stock name, ticker, condition, action, or exchange:").strip().lower()

def search_alerts(alert, query):
    return (
        query in alert['stock_name'].lower() or 
        query in alert['ticker'].lower() or 
        query in alert['name'].lower() or
        query in alert['exchange'].lower() or 
        query in alert.get('action', '').lower() or
        query in alert.get('timeframe', '').lower() or
        any(query in " ".join(condition['conditions']).lower() for condition in alert['conditions'])
    )

filtered_alerts = sorted(
    [alert for alert in alert_data if search_alerts(alert, search_query)],
    key=lambda x: x['last_triggered'] if x['last_triggered'] else "", 
    reverse=True
)

def delete_alert(alert_id):
    global alert_data
    alert_data = [alert for alert in alert_data if alert['alert_id'] != alert_id]
    save_alert_data(alert_data)
    st.rerun()

if not filtered_alerts:
    st.write("No active alerts matching your search.")
else:
    for alert in filtered_alerts:
        with st.expander(f"{alert['name']} ({alert['ticker']}) - {alert['exchange']}"):
            
            st.write(f"### Alert Name: {alert['name']}")
            st.write(f"**Stock Name:** {alert['stock_name']} ({alert['ticker']})")
            st.write(f"**Exchange:** {alert['exchange']}")
            
            st.write("### Last Triggered:")
            last_triggered = alert["last_triggered"] if alert["last_triggered"] else "Not Triggered Yet"
            st.write(last_triggered)
            
            st.write("### Conditions:")
            st.write(format_conditions(alert['conditions']))
            
            st.write("### Combination Logic:")
            st.write(alert['combination_logic'])
            
            st.write("### Action:")
            st.write(alert['action'])

            st.write("### Timeframe:")
            st.write(alert['timeframe'])

            if st.button(f"Delete Alert", key=alert['alert_id']):
                delete_alert(alert['alert_id'])

            st.write(f"**Alert ID:** {alert['alert_id']}")
