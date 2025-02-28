import streamlit as st
import streamlit_tags as st_tags
import uuid
from utils import bl_sp

st.header("WE test components here")

suggests = predefined_suggestions = [
    "sma(period = )[-1]", "hma(period = )[-1]", "rsi(period = )[-1]",
    "ema(period = )[-1]", "slope_sma(period = )[-1]", "slope_ema(period = )[-1]",
    "slope_hma(period = )[-1]", "bb(period = , std_dev = , type = )[-1]",
    "macd(fast_period = , slow_period = , signal_period = , type = )[-1]", "Breakout",
    "atr(period = )[-1]", "cci(period = )[-1]", "roc(period = )[-1]", "WilliamSR(period = )[-1]",
    "psar(acceleration = , max_acceleration = )[-1]", "Close[-1]", "Open[-1]",
    "Low[-1]", "High[-1]"
]


if "entry_conditions" not in st.session_state:
    st.session_state.entry_conditions = {}

# Add new entry condition
if st.button("Add New Condition"):
    new_uuid = str(uuid.uuid4())
    st.session_state.entry_conditions[new_uuid] = []
    st.rerun()

if len(st.session_state.entry_conditions) > 1:
    st.divider()
    st.subheader("Combine Entry Conditions")
    st.write(f"{bl_sp(1)}Use numbers to reference conditions (e.g., '1 and (2 or 3)')")
    
    new_value = st_tags(
        label = f'',
        text="Press tab to autocomplete and enter to save",
        suggestions=suggests,
        value=st.session_state.entry_conditions[i],
        key=f"entry_condition_{i}"
    )
    

