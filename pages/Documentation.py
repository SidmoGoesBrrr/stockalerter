
import streamlit as st

st.set_page_config(page_title="How to Pass Alerts", layout="wide")

st.title("📘 User Manual: How to Pass Alerts")
st.markdown("This guide explains how to define and submit alerts using text boxes and blocks for your conditions.")

# SECTION 1: INDICATORS
st.header("📊 Indicators Available for Use")

st.markdown(
    "Here’s the list of indicators you can use in your conditions:\n"
    "- SMA (Simple Moving Average): sma(period=)[-1]\n"
    "- EMA (Exponential Moving Average): ema(period=)[-1]\n"
    "- RSI (Relative Strength Index): rsi(period=)[-1]\n"
    "- BB (Bollinger Bands): bb(period=, std_dev=, type=)[-1]\n"
    "- ATR (Average True Range): atr(period=)[-1]\n"
    "- CCI (Commodity Channel Index): cci(period=)[-1]\n"
    "- ROC (Rate of Change): roc(period=)[-1]\n"
    "- Williams %R: williamsr(period=)[-1]\n"
    "- PSAR (Parabolic SAR): psar(acceleration=, max_acceleration=)[-1]\n"
    "- Breakout: breakout\n"
    "- OHLC Values: Close[-1], Open[-1], High[-1], Low[-1]"
)

# SECTION 2: SETTING UP INDICATORS
st.header("⚙️ Setting Up Indicators")

st.markdown(
    "1. SMA, RSI, EMA, ATR, CCI, Williams %R:\n"
    "   Simply specify an integer period.\n"
    "   Example: sma(period=50)[-1]\n\n"
    "2. MACD:\n"
    "   Use type as either signal or line.\n"
    "   Example: macd(fast_period=12, slow_period=26, signal_period=9, type=line)[-1]\n\n"
    "3. Bollinger Bands (BB):\n"
    "   type can be upper, middle, or lower\n"
    "   std_dev accepts float values.\n"
    "   Example: bb(period=20, std_dev=2.5, type=upper)[-1]\n\n"
    "4. PSAR:\n"
    "   acceleration and max_acceleration must be floats.\n"
    "   Example: psar(acceleration=0.02, max_acceleration=0.2)[-1]\n\n"
    "5. Input Flexibility:\n"
    "   You can use another indicator as input.\n"
    "   Example: sma(period=30, input=rsi(period=30, input=ema(period=55)))"
)

# SECTION 3: WRITING CONDITIONS
st.header("🧠 Writing Conditions")

st.markdown(
    "To define an alert, write each block of your condition separately.\n"
    "A block can be:\n"
    "- An indicator like rsi(period=14)[-1]\n"
    "- A number or symbol like > or <\n"
    "- An OHLC value like Close[-1]\n\n"
    "After each block, press Enter to confirm.\n\n"
    "Example:\n"
    "sma(period=15)[-1]\n"
    ">\n"
    "sma(period=30)[-1]\n\n"
    "To combine conditions, use the Combine Entry Conditions box:\n"
    "Example: 1 and 2"
)

# SECTION 4: BREAKOUT EXPLANATION
st.header("📈 Understanding Breakout")

st.markdown(
    "Breakout checks for the exact crossover moment.\n\n"
    "Example:\n"
    "breakout, sma(period=30)[-1], >, sma(period=60)[-1]\n\n"
    "This checks only for the crossover candle.\n"
    "Compare with:\n"
    "sma(period=30)[-1] > sma(period=60)[-1]\n"
    "Which checks ongoing relationship, not the crossover event."
)

# SECTION 5: INDEXING
st.header("🔢 Understanding Indexing")

st.markdown(
    "- [-1] is the most recent candle\n"
    "- [-2] is the one before it\n"
    "- [-3] is two before it\n"
    "- 0 refers to the first candle (rarely used)\n\n"
    "Example:\n"
    "Close[-1] > Close[-2]\n"
    "Close[-2] > Close[-3]\n\n"
    "Combine with: 1 and 2"
)
