import talib
import numpy as np
import pandas as pd
import re
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

def apply_indicators(
    df: pd.DataFrame,
    indicators_list: list,      # e.g. ["sma(period=14)", "rsi(period=14) > 50"]
    entry_conditions: list,     # e.g. [{"index": 1, "conditions": [...]}, ...]
    combination_logic: str      # e.g. "1 and (2 or 3)"
) -> pd.DataFrame:
    """
    Example function to parse user indicator strings and add columns to the DataFrame.
    
    Args:
        df (pd.DataFrame): Price data (must have columns like 'Open', 'High', 'Low', 'Close').
        indicators_list (list of str): Raw strings like ["sma(period=14)", "rsi(period=14) > 50"].
        entry_conditions (list): Condition structures from your Streamlit app. (Not fully used here, but shown for reference.)
        combination_logic (str): User-defined text specifying how to combine conditions (e.g. "1 and (2 or 3)").
    
    Returns:
        pd.DataFrame: A copy of the input df with new columns for each indicator.
    """
    # Define a dictionary of supported indicators and their corresponding TA-Lib functions.
    # If you want to add more, just put them here with the appropriate function calls.
    supported_indicators = {
        "sma": lambda close_prices, period: talib.SMA(close_prices, timeperiod=period),
        "ema": lambda close_prices, period: talib.EMA(close_prices, timeperiod=period),
        "rsi": lambda close_prices, period: talib.RSI(close_prices, timeperiod=period),
        "hma": None,   # Not natively in TA-Lib; you’d implement your own or remove for now
        "macd": None, # Not natively in TA-Lib; you’d implement your own or remove for now
    }
    
    # Basic parsing helper to extract the indicator name and period from a string
    def parse_indicator_expr(expr: str):
        """
        Returns:
            (indicator_name, kwargs_dict, condition_part)
            e.g. "sma(period=14) > 50" -> ("sma", {"period":14}, "> 50")
            e.g. "rsi(period=14)" -> ("rsi", {"period":14}, "")
        """
        # Separate any trailing condition, e.g. "> 50" or "<= 45"
        match_paren = re.search(r"\)", expr)
        if not match_paren:
            # If there's no closing paren at all, we can't parse reliably
            return None, {}, ""

        # The position of the first closing parenthesis
        split_index = match_paren.end()
        indicator_part = expr[:split_index]   # e.g. "sma(period=14)"
        condition_part = expr[split_index:].strip()  # e.g. "> 50" (if present)

        # 2. Extract the name of the indicator before '('
        match_name = re.match(r"([a-zA-Z_]+)\(", indicator_part)
        if not match_name:
            return None, {}, condition_part
        
        indicator_name = match_name.group(1).lower()  # e.g. "sma"

        # Extract the inside of parentheses "period=14, arg2=val2..."
        inside_paren = re.search(r"\(([^)]*)\)", indicator_part)
        if inside_paren:
            params_str = inside_paren.group(1).strip()
        else:
            params_str = ""
        
        # Parse params_str into a dict. We expect something like "period=14" or "period = 14"
        kwargs = {}
        if params_str:
            # Split by commas -> ["period=14", "something=val"]
            param_pairs = [x.strip() for x in params_str.split(",") if x.strip()]
            for pair in param_pairs:
                if "=" in pair:
                    k, v = pair.split("=")
                    k = k.strip()
                    v = v.strip()
                    # Attempt to parse numeric
                    # If it fails, keep as string
                    try:
                        v = float(v)
                        # If it’s an integer (like 14.0), convert to int
                        if v.is_integer():
                            v = int(v)
                    except:
                        pass
                    kwargs[k] = v

        return indicator_name, kwargs, condition_part

    # iterate over each indicator in the list
    for expr in indicators_list:
        # e.g. expr could be: "sma(period=14)", "rsi(period=14) > 50", etc.
        indicator_name, kwargs_dict, trailing_condition = parse_indicator_expr(expr)
        if not indicator_name:
            # If we can’t parse the name, skip
            print(f"Could not parse indicator expression: {expr}")
            continue
        
        if indicator_name not in supported_indicators or supported_indicators[indicator_name] is None:
            print(f"Indicator '{indicator_name}' is not implemented or not supported.")
            continue
        
        # The user might have typed "sma(period=14)", so we see if 'period' is in kwargs_dict
        period = kwargs_dict.get("period", 14)  # fallback to 14 as default, if needed
        
        # Actually compute the indicator using the TA-Lib function
        close_prices = df["Close"].values 
        func = supported_indicators[indicator_name]
        
        try:
            result = func(close_prices, period)
            # Construct a column name for the new indicator
            col_name = f"{indicator_name.upper()}_{period}"
            df[col_name] = result
        except Exception as e:
            print(f"Error computing {indicator_name} with expression '{expr}': {e}")
            continue
        
        # If there's some trailing condition, e.g. "> 50", you could store it or evaluate it
        if trailing_condition:
            # e.g. trailing_condition might be "> 50" or ">= 80"
            condition_col = f"{col_name}_cond"
            # Evaluate the condition if possible:
            match_cond = re.match(r"([><=!]+)\s*(\d+\.?\d*)", trailing_condition)
            if match_cond:
                operator_ = match_cond.group(1)
                threshold_ = float(match_cond.group(2))
                # Evaluate
                if operator_ == ">":
                    df[condition_col] = df[col_name] > threshold_
                elif operator_ == "<":
                    df[condition_col] = df[col_name] < threshold_
                elif operator_ == ">=":
                    df[condition_col] = df[col_name] >= threshold_
                elif operator_ == "<=":
                    df[condition_col] = df[col_name] <= threshold_
                elif operator_ == "==":
                    df[condition_col] = df[col_name] == threshold_
                else:
                    # Unsupported operator
                    df[condition_col] = False
            else:
                # If the format is something else, we skip
                df[condition_col] = False

    # evaluate or combine the entry_conditions with combination_logic
    print(f"Received {len(entry_conditions)} entry conditions.")
    print(f"User combination logic: {combination_logic}")
    # return dataframe 
    return df