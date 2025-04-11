import talib
import numpy as np
import pandas as pd

# CLASSIFICATION ON BASIS OF NUMBER OF INPUTS

# INPUT FRIENDLY
def SMA(df, timeperiod, input):
    if type(input) == str and input in ["Close", "Open", "High", "Low", "Volume"]:
        return talib.SMA(df[input], timeperiod = timeperiod)
    return talib.SMA(input, timeperiod = timeperiod)

def EMA(df, timeperiod, input):
    if type(input) == str and input in ["Close", "Open", "High", "Low", "Volume"]:
        return talib.EMA(df[input], timeperiod = timeperiod)
    return talib.EMA(input, timeperiod = timeperiod)

def HMA(df, timeperiod, input):
    if type(input) == str and input in ["Close", "Open", "High", "Low", "Volume"]:
        prices = df[input]
    else:
        prices = input

    half_period = timeperiod // 2
    sqrt_period = int(np.sqrt(timeperiod))
    
    wma_half_period = talib.WMA(prices, timeperiod=half_period)
    wma_full_period = talib.WMA(prices, timeperiod=timeperiod)
    
    wma_delta = 2 * wma_half_period - wma_full_period
    hma_values = talib.WMA(wma_delta, timeperiod=sqrt_period)

    return hma_values

def SLOPE_SMA(df, timeperiod, input):
    sma = SMA(df, timeperiod, input)
    return pd.Series(np.gradient(sma))

def SLOPE_EMA(df, timeperiod, input):
    ema = EMA(df, timeperiod,input)
    return pd.Series(np.gradient(ema,input))

def SLOPE_HMA(df, timeperiod, input):
    hma = HMA(df, timeperiod, input)
    return pd.Series(np.gradient(hma))

def RSI(df, timeperiod, input):
    if type(input) == str and input in ["Close", "Open", "High", "Low", "Volume"]:
        return talib.RSI(df[input], timeperiod=timeperiod)
    return talib.RSI(input, timeperiod=timeperiod)

def ROC(df, timeperiod, input):
    if type(input) == str and input in ["Close", "Open", "High", "Low", "Volume"]:
        return talib.ROC(df[input], timeperiod=timeperiod)
    return talib.ROC(input, timeperiod=timeperiod)

# INPUT UNFRIENDLY

def ATR(df, timeperiod):
    close = df['Close']
    high = df['High']
    low = df['Low']

    return talib.ATR(high, low, close, timeperiod = timeperiod)

def CCI(df, timeperiod):
    close = df['Close']
    high = df['High']
    low = df['Low']

    return talib.CCI(high, low, close, timeperiod = timeperiod)

def WILLR(df, timeperiod):
    return talib.WILLR(df["High"], df['Low'], df['Close'], timeperiod=timeperiod)

# MULTI INPUTTED SINGLE OUTPUT

def SAR(df, acceleration, max_acceleration):
    return talib.SAR(df['High'], df['Low'], acceleration= acceleration, maximum=max_acceleration)

# MULTI INPUT AND MULTI OUTPUT 

def BBANDS(df, timeperiod, std_dev, type):
    upper, middle, lower = talib.BBANDS(df['Close'], timeperiod = timeperiod, nbdevdn= std_dev, nbdevup= std_dev, matype=0)
    if type == "upper":
        return upper
    elif type == "middle":
        return middle
    elif type == "lower":
        return lower

def MACD(df, fast_period, slow_period, signal_period, type):
    macd, macdsignal = talib.MACD(df['Close'], fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    if type == "line":
        return macd
    elif type == "signal":
        return macdsignal