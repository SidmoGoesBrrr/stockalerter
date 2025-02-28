import streamlit as st
import pandas as pd
import uuid
from streamlit_tags import st_tags

# Local imports
from utils import (
    load_market_data,
    bl_sp,
    predefined_suggestions,
    predefined_suggestions_alt,
    grab_new_data_polygon,
    save_alert
)
st.set_page_config(layout="wide")
# Hypothetical indicators module (adjust import, function name, etc.)
import indicators_lib as indicators

# Helper function: parse the user’s text input into a list or structured data
def parse_indicator_text(text: str):
    """
    Example parse function:
      - Splits on commas, strips whitespace.
      - You can expand this to handle more complex syntax if needed.
    """
    # e.g., "sma(14), rsi(14) > 50" => ["sma(14)", "rsi(14) > 50"]
    items = [x.strip() for x in text.split(",")]
    return [item for item in items if item]  # filter out empty

# Load market data
market_data = load_market_data()

st.header("Stock Alert System")
# Initialize session state
if "entry_conditions" not in st.session_state:
    st.session_state.entry_conditions = {}

if "entry_combination" not in st.session_state:
    st.session_state.entry_combination = ""

# We'll store any typed-in indicator text here
if "indicator_text" not in st.session_state:
    st.session_state.indicator_text = ""

# We’ll also keep a parsed representation of the user’s indicators
if "parsed_indicators" not in st.session_state:
    st.session_state.parsed_indicators = []

# Section: Add New Stock Alert
st.subheader("Add a New Stock Alert")

# Select market exchange
exchange_list = market_data["Country"].unique().tolist()
selected_exchange = st.selectbox("Select Market Exchange:", exchange_list)

# Select stock from the chosen exchange
filtered_stocks = market_data[market_data["Country"] == selected_exchange]["Name"].tolist()
selected_stock = st.selectbox("Select Stock:", filtered_stocks)

# # Button to add the selected stock alert
# if st.button("Add Stock Alert"):
#     alert_id = str(uuid.uuid4())
#     st.session_state.entry_conditions[alert_id] = [selected_exchange, selected_stock]
#     st.success(f"Added alert for {selected_stock} on {selected_exchange}")
#     st.rerun()


# Section: Define Entry Conditions
st.subheader("Entry Conditions")

timeframe = st.selectbox(
    f"{bl_sp(1)}Select lowest required Timeframe",
    ["1h", "4h", "1d", "1wk", "1mo"],
    index=2
)

# For demonstration, always use multiple-timeframe suggestions
suggests = predefined_suggestions
for n, (i, condition) in enumerate(st.session_state.entry_conditions.items()):
    left,middle,right = st.columns([0.8,30,6])
    with left:
        st.markdown(f'<div class="bottom-align2"><p>{n+1}.</p></div>', unsafe_allow_html=True)
    with middle:
        new_value = st_tags(
            label = '',
            text="Press tab to autocomplete and enter to save",
            suggestions=suggests,
            value=st.session_state.entry_conditions[i],
            key=f"entry_condition_{i}"
        )
        if new_value!=condition:
            st.session_state.entry_conditions[i] = new_value
            st.rerun()
    with right:
        st.markdown('<div class="bottom-align">', unsafe_allow_html=True)
        if st.button(f"╳", key=f'button_{i}'):
            del st.session_state.entry_conditions[i]
            st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

# Button to add a new condition row
if st.button("Add New Condition"):
    new_uuid = str(uuid.uuid4())
    st.session_state.entry_conditions[new_uuid] = []
    st.rerun()

# Combine Entry Conditions (if multiple exist)
if len(st.session_state.entry_conditions) > 1:
    st.divider()
    st.subheader("Combine Entry Conditions")
    st.write(f"{bl_sp(1)}Use numbers to reference conditions (e.g., '1 and (2 or 3)')")

    new_val = st.text_input(
        "Enter logic to combine conditions (optional)",
        value=st.session_state.entry_combination
    )
    if new_val != st.session_state.entry_combination:
        st.session_state.entry_combination = new_val

st.divider()

st.subheader("Apply Indicators on AAPL's Price")

# This button will fetch Apple data from Polygon and apply your indicator logic
if st.button("Compute Indicators on AAPL"):
    print("Parsed entry conditions"+str(st.session_state.entry_conditions))

    with st.spinner("Fetching Apple data from Polygon and computing indicators..."):
        # 1) Grab AAPL data
        df_aapl = grab_new_data_polygon("AAPL", timespan="day", multiplier=1)
        # 2) Convert session state conditions into a list/dict if needed
        entry_conditions_list = []
        for idx, cond_list in enumerate(st.session_state.entry_conditions.values(), start=1):
            entry_conditions_list.append({
                "index": idx,
                "conditions": cond_list
            })
        print("Parsed entry conditions"+str(entry_conditions_list))
        # Get the indicators in a format we can add in a dataframe
        
        save_alert(entry_conditions_list, st.session_state.entry_combination, "AAPL","Apple",None)
        try:
            df_result = indicators.apply_indicators(
                df_aapl,
                st.session_state.parsed_indicators,    
                entry_conditions_list,
                st.session_state.entry_combination
            )
            
            st.success("Indicators computed successfully!")
            st.dataframe(df_result.tail(20))  # Display last 20 rows
        except Exception as e:
            st.error(f"An error occurred while computing indicators: {e}")