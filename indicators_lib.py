import talib
import numpy as np


def SMA(df, timeperiod):
    sma = talib.SMA(df['Close'], timeperiod = timeperiod)
    return sma

def EMA(df, timeperiod):
    ema = talib.EMA(df['Close'], timeperiod = timeperiod)
    return ema

def RSI(df, timeperiod):
    rsi = talib.RSI(df['Close'], timeperiod = timeperiod)
    return rsi

def ATR(df, timeperiod):
    close = df['Close']
    high = df['High']
    low = df['Low']

    return talib.ATR(high, low, close, timeperiod = timeperiod)

def CCI(df, timeperiod):
    close = df['Close']
    high = df['High']
    low = df['Low']

    return talib.ATR(high, low, close, timeperiod = timeperiod)

def HMA(df, timeperiod):

    prices = df['Close']
    
    half_period = timeperiod // 2
    sqrt_period = int(np.sqrt(timeperiod))
    
    wma_half_period = talib.WMA(prices, timeperiod=half_period)
    wma_full_period = talib.WMA(prices, timeperiod=timeperiod)
    
    wma_delta = 2 * wma_half_period - wma_full_period
    hma_values = talib.WMA(wma_delta, timeperiod=sqrt_period)

    return hma_values

def SLOPE_SMA(df, timeperiod):
    sma = SMA(df, timeperiod)
    return np.gradient(sma)

def SLOPE_EMA(df, timeperiod):
    sma = EMA(df, timeperiod)
    return np.gradient(sma)

def SLOPE_HMA(df, timeperiod):
    hma = HMA(df, timeperiod)
    return np.gradient(hma)

def RSI(df, timeperiod):
    return talib.RSI(df['Close'], timeperiod=timeperiod)

def BBANDS(df, timeperiod, std_dev, type)
    upper, middle, lower = talib.BBANDS(df['Close'], timeperiod = timeperiod, nbdevdn= std_dev, nbdevup= std_dev, matype=0)
    if type == "upper":
        return upper
    elif type == "middle":
        return middle
    elif type == "lower":
        return lower
    
def CCI(df, timeperiod):
    return talib.CCI(df['High'], df['Low'], df['Close'], timeperiod=timeperiod)

def ROC(df, timeperiod):
    return talib.ROC(df['Close'], timeperiod=timeperiod)

def WILLR(df, timeperiod):
    return talib.WILLR(df["High"], df['Low'], df['Close'], timeperiod=timeperiod)

def MACD(df, fast_period, slow_period, signal_period, type):
    macd, macdsignal, macdhist = talib.MACD(df['Close'], fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    if type == "line":
        return macd
    elif type == "signal":
        return macdsignal

def SAR(df, acceleration, max_acceleration):
    return talib.SAR(df['High'], df['Low'], acceleration= acceleration, maximum=max_acceleration)