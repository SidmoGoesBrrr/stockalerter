import talib
import numpy as np

def SMA(df, timeperiod):
    sma = talib.SMA(df['Close'], timeperiod = timeperiod)
    df['sma'] = sma
    return df

def EMA(df, timeperiod):
    ema = talib.EMA(df['Close'], timeperiod = timeperiod)
    df['ema'] = ema
    return df

def HMA(df, timeperiod):

    prices = df['Close']
    
    half_period = timeperiod // 2
    sqrt_period = int(np.sqrt(timeperiod))
    
    wma_half_period = talib.WMA(prices, timeperiod=half_period)
    wma_full_period = talib.WMA(prices, timeperiod=timeperiod)
    
    wma_delta = 2 * wma_half_period - wma_full_period
    hma_values = talib.WMA(wma_delta, timeperiod=sqrt_period)

    df['hma'] = hma_values
    
    return df

def SLOPE_SMA(df, timeperiod):
    prices = df['Close']
    df['slope_sma'] = np.gradient(talib.SMA(prices,timeperiod=timeperiod))
    return df

def SLOPE_EMA(df, timeperiod):
    prices = df['Close']
    df['slope_sma'] = np.gradient(talib.EMA(prices,timeperiod=timeperiod))
    return df

def SLOPE_HMA(df, timeperiod):
    prices = df['Close']
    df['slope_sma'] = np.gradient(HMA(prices,timeperiod=timeperiod))
    return df