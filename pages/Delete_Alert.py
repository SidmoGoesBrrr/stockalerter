import streamlit as st
import json

# Load alert data from JSON file
def load_alert_data():
    with open("alerts.json", "r") as file:
        return json.load(file)

# Save updated alert data to JSON file
def save_alert_data(alert_data):
    with open("alerts.json", "w") as file:
        json.dump(alert_data, file, indent=4)

# Load alerts
alert_data = load_alert_data()

st.title("Delete Stock Alert")

# Extract alert IDs for selection
alert_ids = {alert['alert_id']: f"{alert['stock_name']} ({alert['ticker']}) - {alert['alert_id']}" for alert in alert_data}

if not alert_ids:
    st.write("No active alerts to delete.")
else:
    selected_alert_id = st.selectbox("Select an alert to delete:", list(alert_ids.keys()), format_func=lambda x: alert_ids[x])
    
    if st.button("Delete Alert"):
        alert_data = [alert for alert in alert_data if alert['alert_id'] != selected_alert_id]
        save_alert_data(alert_data)
        st.success("Alert deleted successfully!")
        st.rerun()
