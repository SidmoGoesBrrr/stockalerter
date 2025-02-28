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

def display_alert(alert):
    with st.expander(f"{alert['stock_name']} ({alert['ticker']}) - Alert ID: {alert['alert_id']}"):
        st.write("### Stock Alert")
        st.write(f"**Stock Name:** {alert['stock_name']} ({alert['ticker']})")
        st.write(f"**Alert ID:** {alert['alert_id']}")
        
        st.write("### Conditions:")
        for condition in alert["conditions"]:
            st.write(f"**Condition {condition['index']}**:")
            condition_text = " ".join(condition['conditions'])
            st.code(condition_text, language="python")
        
        st.write("### Combination Logic:")
        st.write(alert['combination_logic'])
        
        st.write("### Last Triggered:")
        last_triggered = alert["last_triggered"] if alert["last_triggered"] else "Not Triggered Yet"
        st.write(last_triggered)
        


st.header("Active Stock Alerts")
st.write("Here are the active stock alerts that you have set up:")

# Load existing alerts if the JSON file exists
try:
    with open("metadata.json", "r") as file:
        alerts = json.load(file)

except (FileNotFoundError, json.JSONDecodeError):
    alerts = []

search_query = st.text_input("Search alerts by stock name, ticker, condition, or exchange:").strip().lower()

def search_alerts(alert, query):
    return (
        query in alert['stock_name'].lower() or 
        query in alert['ticker'].lower() or 
        query in alert['exchange'].lower() or 
        any(query in " ".join(condition['conditions']).lower() for condition in alert['conditions'])
    )

filtered_alerts = sorted(
    [alert for alert in alerts if search_alerts(alert, search_query)],
    key=lambda x: x['last_triggered'] if x['last_triggered'] else "", 
    reverse=True
)

if not filtered_alerts:
    st.write("No active alerts matching your search.")
else:
    for alert in filtered_alerts:
        with st.expander(f"{alert['stock_name']} ({alert['ticker']}) - {alert['exchange']} - Alert ID: {alert['alert_id']}"):
            st.write("### Stock Alert")
            st.write(f"**Stock Name:** {alert['stock_name']} ({alert['ticker']})")
            st.write(f"**Exchange:** {alert['exchange']}")
            st.write(f"**Alert ID:** {alert['alert_id']}")
            
            st.write("### Conditions:")
            st.write(format_conditions(alert['conditions']))
            
            st.write("### Combination Logic:")
            st.write(alert['combination_logic'])
            
            st.write("### Last Triggered:")
            last_triggered = alert["last_triggered"] if alert["last_triggered"] else "Not Triggered Yet"
            st.write(last_triggered)
