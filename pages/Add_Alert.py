import time

import streamlit as st

st.set_page_config(
    page_title="Add Alert",
    page_icon="+",
    layout="wide",
)

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uuid

import pandas as pd
from streamlit_tags import st_tags

# Local imports
from utils import bl_sp, grab_new_data_polygon, grab_new_data_yfinance, load_market_data, predefined_suggestions, save_alert

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
st.write(f"{bl_sp(1)}Select a stock exchange and one or more stocks to set up alerts.")

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
    "Denmark": "DK", "Finland": "FI", "Swesden": "SE",
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
selected_stocks = st.multiselect("Select Stock(s):", filtered_stocks)

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
        if st.button("╳", key=f'button_{i}'):
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


st.subheader("Apply Indicators")

if st.button("Add Alert"):
    if not selected_stocks:
        st.error("⚠️ Please select at least one stock.")
    else:
        successes = []
        failures = []
        total = len(selected_stocks)
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, stock_name in enumerate(selected_stocks):
            # 2. Update status text and progress
            status_text.text(f"Processing {stock_name} ({idx+1}/{total})")
            progress_bar.progress((idx + 1) / total)

            try:
                # map to ticker
                ticker = market_data.loc[market_data["Name"] == stock_name, "Symbol"].iat[0]

                # fetch data with rate-limit handling
                try:
                    if country_code.upper() == "US":
                        timespan = "week" if timeframe == "1wk" else "day"
                        df_stock = grab_new_data_polygon(ticker, timespan=timespan, multiplier=1)
                    else:
                        df_stock = grab_new_data_yfinance(ticker, timespan=timeframe)
                except Exception as e:
                    msg = str(e)
                    if "Rate limited" in msg or "Too Many Requests" in msg:
                        failures.append(f"{stock_name}: YFinance rate-limited, skipping")
                        continue
                    else:
                        failures.append(f"{stock_name}: {e}")
                        continue

                # flatten MultiIndex columns if present
                if hasattr(df_stock.columns, "nlevels") and df_stock.columns.nlevels > 1:
                    df_stock.columns = [
                        "_".join([str(x) for x in col if x]).strip()
                        for col in df_stock.columns.values
                    ]

                # prepare and save CSV (overwrite with fresh data)
                if "Date" not in df_stock.columns:
                    df_stock.reset_index(inplace=True)
                df_stock.insert(0, "index", range(1, len(df_stock) + 1))
                df_final = df_stock.copy()

                safe_ticker = ticker.replace(" ", "_")
                tf_name = timeframe.replace("1", "").replace("d", "daily").replace("wk", "weekly")
                file_path = os.path.join("data", f"{safe_ticker}_{tf_name}.csv")
                df_final.to_csv(file_path, index=False, date_format="%Y-%m-%d")

                # build conditions payload
                entry_conditions_list = [
                    {"index": idx, "conditions": " ".join(conds)}
                    for idx, conds in enumerate(st.session_state.entry_conditions.values(), start=1)
                ]

                # save the alert
                save_alert(
                    alert_name or f"{stock_name} Alert",
                    entry_conditions_list,
                    st.session_state.entry_combination,
                    ticker,
                    stock_name,
                    country_code,
                    timeframe,
                    None,
                    action
                )
                successes.append(stock_name)

            except Exception as e:
                failures.append(f"{stock_name}: {e}")

        time.sleep(2)
        # final report
        if successes:
            st.success(f"✅ Alerts saved for: {', '.join(successes)}")
        if failures:
            for err in failures:
                st.error(f"❌ Failed for {err}")
