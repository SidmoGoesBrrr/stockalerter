import streamlit as st
import pandas as pd
import uuid
from utils import update_market_data, load_market_data, bl_sp, predefined_suggestions, predefined_suggestions_alt

# Load market data
market_data = load_market_data()

st.header("Stock Alert System")

# Initialize session state
if "entry_conditions" not in st.session_state:
    st.session_state.entry_conditions = {}

if "entry_combination" not in st.session_state:
    st.session_state.entry_combination = ""

# Section: Add New Stock Alert
st.subheader("Add a New Stock Alert")

# Select market exchange
exchange_list = market_data["Exchange"].unique().tolist()
selected_exchange = st.selectbox("Select Market Exchange:", exchange_list)

# Select stock from the chosen exchange
filtered_stocks = market_data[market_data["Exchange"] == selected_exchange]["Stock"].tolist()
selected_stock = st.selectbox("Select Stock:", filtered_stocks)

# Button to add the selected stock alert
if st.button("Add Stock Alert"):
    alert_id = str(uuid.uuid4())
    st.session_state.entry_conditions[alert_id] = [selected_exchange, selected_stock]
    st.success(f"Added alert for {selected_stock} on {selected_exchange}")
    st.rerun()

st.divider()

# Section: Define Entry Conditions
st.subheader("Entry Conditions")

multiframe = st.selectbox(f"{bl_sp(1)}Need multiple timeframes for strategy?", ["True", "False"], index=1)
timeframe = st.selectbox(f"{bl_sp(1)}Select lowest required Timeframe", ["1h", "4h", "1d", "1wk", "1mo"], index=2)

# Get indicator suggestions
suggests = predefined_suggestions_alt if multiframe == "True" else predefined_suggestions

# Display existing conditions
for n, (i, condition) in enumerate(st.session_state.entry_conditions.items()):
    left, middle, right = st.columns([0.8, 30, 6])
    
    with left:
        st.markdown(f'<div class="bottom-align2"><p>{n+1}</p></div>', unsafe_allow_html=True)
    
    with middle:
        new_value = st.text_area(f"Condition {n+1}", value=", ".join(condition), key=f"entry_condition_{i}")
        if new_value.split(", ") != condition:
            st.session_state.entry_conditions[i] = new_value.split(", ")
            st.rerun()
    
    with right:
        if st.button(f"╳", key=f'button_{i}'):
            del st.session_state.entry_conditions[i]
            st.rerun()

# Add new entry condition
if st.button("Add New Condition"):
    new_uuid = str(uuid.uuid4())
    st.session_state.entry_conditions[new_uuid] = []
    st.rerun()

# Combine Entry Conditions (if multiple exist)
if len(st.session_state.entry_conditions) > 1:
    st.divider()
    st.subheader("Combine Entry Conditions")
    st.write(f"{bl_sp(1)}Use numbers to reference conditions (e.g., '1 and (2 or 3)')")
    
    combination_input = st.text_input(
        label="Logical Condition",
        value=st.session_state.entry_combination,
        key="entry_combination_input"
    )
    st.session_state.entry_combination = combination_input

st.divider()