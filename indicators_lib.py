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


def HARSI_Flip(df, timeperiod, smoothing):
    def calculate_harsi_base(df, timeperiod, smoothing):
        # zero‑centered RSI
        c = pd.Series(RSI(df, timeperiod, "Close"), index=df.index) - 50
        h = pd.Series(RSI(df, timeperiod, "High"),   index=df.index) - 50
        l = pd.Series(RSI(df, timeperiod, "Low"),    index=df.index) - 50

        # previous bar’s zero‑centered close for HA open
        o = c.shift(1)

        # high/low of RSI for the bar
        H = np.maximum(h, l)
        L = np.minimum(h, l)

        # Heikin‑Ashi RSI close
        close_ha = (o + H + L + c) / 4

        # init HA open series
        open_ha = pd.Series(index=df.index, dtype=float)

        # find first bar with a valid HA close
        first = close_ha.first_valid_index()
        if first is None:
            return open_ha, pd.Series(np.nan, df.index), pd.Series(np.nan, df.index), close_ha

        # set HA open at first valid bar = midpoint of prior RSI-close and RSI-close
        open_ha.loc[first] = (o.loc[first] + c.loc[first]) / 2

        # fill subsequent opens recursively
        idxs = list(df.index)
        start = idxs.index(first)
        for i in range(start + 1, len(idxs)):
            prev = idxs[i - 1]
            cur  = idxs[i]
            open_ha.loc[cur] = (open_ha.loc[prev] * smoothing + close_ha.loc[prev]) / (smoothing + 1)

        # HA high/low
        high_ha = pd.Series(np.maximum.reduce([H, open_ha, close_ha]), index=df.index)
        low_ha  = pd.Series(np.minimum.reduce([L, open_ha, close_ha]), index=df.index)

        return open_ha, high_ha, low_ha, close_ha

    def har_si_colors(df, timeperiod, smoothing):
        o, h, l, c = calculate_harsi_base(df, timeperiod, smoothing)
        return pd.Series(np.where(c > o, "green", "red"), index=df.index)

    def color_transitions(colors):
        prev = colors.shift(1)
        result = pd.Series(0, index=colors.index)
        result[(prev == "green") & (colors == "red")] = 1
        result[(prev == "red") & (colors == "green")] = 2
        return result
    
    return color_transitions(har_si_colors(df,timeperiod,smoothing))

def SROCST(df, ma_type='EMA', lsma_off=0, smooth_len=12, kal_src='Close', sharp=25.0, k_period=1.0, roc_len=9, stoch_len=14, stoch_k_smooth=1, stoch_d_smooth=3):
    def f_ma(ma_type, df, period, src, lsma_off=0):
        ma_type = ma_type.lower()
        if ma_type=='sma': return SMA(df, period, src)
        if ma_type=='ema': return EMA(df, period, src)
        if ma_type=='hma': return HMA(df, period, src)
        raise ValueError(type)

    def calc_srocst_line(df, ma_type='EMA', lsma_off=0, smooth_len=12, kal_src='Close', sharp=25.0, k_period=1.0, roc_len=9, stoch_len=14, stoch_k_smooth=1, stoch_d_smooth=3):
        kf=pd.Series(index=df.index,dtype=float)
        vel=pd.Series(0.0,index=df.index)
        for i in range(len(df)):
            if i==0:
                kf.iat[0]=df[kal_src].iat[0]
            else:
                d=df[kal_src].iat[i]-kf.iat[i-1]
                e=kf.iat[i-1]+d*np.sqrt(sharp*k_period/100)
                vel.iat[i]=vel.iat[i-1]+d*(k_period/100)
                kf.iat[i]=e+vel.iat[i]
        roc=100*(kf-kf.shift(roc_len))/kf.shift(roc_len)
        low=df['Low'].rolling(stoch_len).min()
        high=df['High'].rolling(stoch_len).max()
        k_raw=(df['Close']-low)/(high-low)*100
        k_sma=k_raw.rolling(stoch_k_smooth).mean()
        d_sma=k_sma.rolling(stoch_d_smooth).mean()
        blend=f_ma(ma_type,df,smooth_len,(roc+d_sma)/2,lsma_off)
        return blend

    def calc_srocst_colors(blend):
        return pd.Series(np.where(blend>blend.shift(1),'white','blue'),index=blend.index)

    def color_transition_codes(colors: pd.Series) -> pd.Series:
        """
        Given a Series of 'white'/'blue' values, returns:
        0 = no change
        1 = white -> blue
        2 = blue -> white
        """
        prev = colors.shift(1)
        codes = pd.Series(0, index=colors.index)
        codes[(prev == 'white') & (colors == 'blue')] = 1
        codes[(prev == 'blue') & (colors == 'white')] = 2
        return codes
    
    return color_transition_codes(calc_srocst_colors(calc_srocst_line(df, ma_type, lsma_off, smooth_len, kal_src, sharp, k_period, roc_len, stoch_len, stoch_k_smooth, stoch_d_smooth)))

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
    macd, macdsignal, macdhistory  = talib.MACD(df['Close'], fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    if type == "line":
        return macd
    elif type == "signal":
        return macdsignal

