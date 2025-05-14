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
alert_ids = {
    alert['alert_id']: f"{alert['stock_name']} ({alert['ticker']}) - {alert['alert_id']}"
    for alert in alert_data
}

if not alert_ids:
    st.write("No active alerts to delete.")
else:
    selected_alert_ids = st.multiselect(
        "Select alerts to delete:",
        list(alert_ids.keys()),
        format_func=lambda x: alert_ids[x]
    )

    # Display selected alert details in a compact table
    if selected_alert_ids:
        st.markdown("### 🧾 Selected Alert(s)")
        for alert_selected in selected_alert_ids:
            alert = next((a for a in alert_data if a['alert_id'] == alert_selected), None)
            if alert:
                st.markdown(f"""
                <div style="border:1px solid #444;padding:15px;border-radius:10px;margin-bottom:15px;background-color:#111;">
                    <b>{alert['name']}</b> <br>
                    <small><b>Stock:</b> {alert['stock_name']} | <b>Ticker:</b> {alert['ticker']} | <b>Exchange:</b> {alert['exchange']} | <b>Timeframe:</b> {alert['timeframe']}</small><br><br>
                    <b>Conditions:</b><br>
                    <code>{'<br>'.join(c['conditions'] for c in alert['conditions'])}</code>
                </div>
                """, unsafe_allow_html=True)

        

    # Delete all selected alerts
    if st.button("Delete Alert(s)"):
        alert_data = [alert for alert in alert_data if alert['alert_id'] not in selected_alert_ids]
        save_alert_data(alert_data)
        st.success("Selected alert(s) deleted successfully!")
        st.rerun()
