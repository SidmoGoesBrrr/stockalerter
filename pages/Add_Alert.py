import streamlit as st

st.set_page_config(
    page_title="Add Alert",
    page_icon="+",
    layout="wide",
)

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import uuid
from streamlit_tags import st_tags

# Local imports
from utils import (
    load_market_data,
    bl_sp,
    predefined_suggestions,
    grab_new_data_polygon,
    grab_new_data_yfinance,
    save_alert
)

# Load market data
market_data = load_market_data()

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
st.header("Add a New Stock Alert")
st.write(f"{bl_sp(1)}Select a stock exchange and stock to set up an alert.")

#ask for the name of the alert
alert_name = st.text_input("Enter the name of the alert")

# Select market exchange
exchange_info = pd.read_csv("market_data.csv")

# Prepare mapping from exchange country name to country code used in cleaned_data
country_to_code = {
    "USA": "US", "Australia": "AUS", "Switzerland": "SW",
    "Italy": "MI", "United Kingdom": "UK", "UK": "UK",
    "Canada": "CA", "Japan": "JP", "Germany": "DE",
    "France": "FR", "Spain": "ES", "Netherlands": "NL",
    "Belgium": "BE", "Ireland": "IE", "Portugal": "PT",
    "Denmark": "DK", "Finland": "FI", "Sweden": "SE",
    "Norway": "NO", "Austria": "AT", "Poland": "PL",
    "Hungary": "HU", "Greece": "GR", "Turkey": "TR", 
    "Mexico": "MX", "Czech Republic": "CZ"
}

# Exchange selection by name
exchange_names = exchange_info["Exchange Name"].tolist()
selected_exchange_name = st.selectbox("Select Market Exchange:", exchange_names)

# Map the selected exchange's country to the proper code
country_name = exchange_info.loc[exchange_info["Exchange Name"] == selected_exchange_name, "Country"].iloc[0]
country_code = country_to_code.get(country_name, country_name)  # default to name if already a code

# Filter stocks from cleaned_data (market_data) by this country code
filtered_stocks = market_data[market_data["Country"] == country_code]["Name"].tolist()
selected_stock = st.selectbox("Select Stock:", filtered_stocks)

# Select whether to buy or sell
action = st.selectbox("Select Action:", ["Buy", "Sell"])

# Section: Define Entry Conditions
st.subheader("Entry Conditions")

timeframe = st.selectbox(
    f"{bl_sp(1)}Select the required Timeframe",
    ["1d", "1wk"],
    index=0
)

    

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

stock_ticker = market_data[market_data["Name"] == selected_stock]["Symbol"].values[0]

st.subheader(f"Apply Indicators on {stock_ticker}'s Price")

# This button will fetch Stock data from Polygon and apply your indicator logic
if st.button("Add Alert"):
    print("Parsed entry conditions"+str(st.session_state.entry_conditions))

    with st.spinner(f"Fetching {selected_stock} data from Polygon and computing indicators..."):
        if country_code.upper() == "US":
            # Use Polygon for US stocks
            if timeframe == "1wk":
                time_poly = "week"
            else:
                time_poly = "day"
            
            df_stock = grab_new_data_polygon(stock_ticker, timespan=time_poly, multiplier=1)
        else:
            # Use yfinance for non-US stocks
            
                
            df_stock = grab_new_data_yfinance(stock_ticker, timespan=timeframe)

        entry_conditions_list = []
        
        for idx, cond_list in enumerate(st.session_state.entry_conditions.values(), start=1):
            entry_conditions_list.append({
                "index": idx,
                "conditions": " ".join(cond_list)
            })
            line_expr = " ".join(cond_list)  # e.g. "sma(period=14)[-1] > sma(period=15)[-1]"
            print("DEBUGGING" + line_expr)
            print(f"Parsing condition {idx}: {line_expr}")
            

        #st.dataframe(df_stock.tail(20)) 
        print("Parsed entry conditions"+str(entry_conditions_list))

        
        try:
            if alert_name == "":
                alert_name = f"{selected_stock} Alert"

            safe_ticker_name = stock_ticker.replace(" ", "_")
            timeframe_name = timeframe.replace("1", "").replace("d", "daily").replace("wk", "weekly")

            file_name = f"{safe_ticker_name}_{timeframe_name}.csv"
            save_path = os.path.join("data", file_name)

            if os.path.exists(save_path):
                df_existing = pd.read_csv(save_path,index_col=0)
                len_existing = len(df_existing)
            
                df_new = df_stock

                
                if "Date" not in df_existing.columns:
                    df_stock.reset_index(inplace=True)
                    df_stock.insert(0, "index", range(1, len(df_stock) + 1))

                df_existing.reset_index(drop=True, inplace=True)
                df_new = df_stock.copy().reset_index(drop=True)
                new_cols = [c for c in df_new.columns if c not in df_existing.columns]
                df_final = pd.concat([df_existing, df_new[new_cols]], axis=1)


            else:
                print("No existing file, using df_stock")
                if "Date" not in df_stock.columns:
                                df_stock.reset_index(inplace=True)

                df_final = df_stock.copy()                

            
            df_final.insert(0, "index", range(1, len(df_final) + 1))

            df_final.to_csv(save_path, index=False, date_format="%Y-%m-%d")

            print(entry_conditions_list)
            
            save_alert(alert_name,entry_conditions_list, st.session_state.entry_combination, stock_ticker,selected_stock,country_code,timeframe,None,action)
            st.success(f"{alert_name} saved successfully!")

        except ValueError as e:
            st.error(f"Error: {e}")
