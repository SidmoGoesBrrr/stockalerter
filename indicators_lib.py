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

import re
import numpy as np
import pandas as pd

def apply_indicators(
    df: pd.DataFrame,
    indicators_list: list,      # e.g. ["sma(period=14)", "slope_ema(period=20) > 0"]
    entry_conditions: list,     # e.g. [{"index": 1, "conditions": [...]}, ...]
    combination_logic: str      # e.g. "1 and (2 or 3)"
) -> pd.DataFrame:
    """
    Parses user indicator strings (e.g. "sma(period=14)") and applies your
    custom indicator functions (SMA, EMA, HMA, SLOPE_SMA, etc.) to the DataFrame.
    If a trailing condition is included (e.g. "> 50"), a separate boolean column
    is added that checks whether the indicator meets that threshold.
    """

    # 1) Create a dictionary referencing your existing functions
    supported_indicators = {
        "sma": SMA,
        "ema": EMA,
        "hma": HMA,
        "slope_sma": SLOPE_SMA,
        "slope_ema": SLOPE_EMA,
        "slope_hma": SLOPE_HMA
    }

    # 2) Helper function to parse an expression like "sma(period=14) > 50"
    def parse_indicator_expr(expr: str):
        """
        Returns (indicator_name, kwargs_dict, condition_part):
          e.g. "sma(period=14) > 50" -> ("sma", {"period": 14}, "> 50")
        """
        match_paren = re.search(r"\)", expr)
        if not match_paren:
            # No closing parenthesis => can't parse
            return None, {}, ""

        # Split at the first closing parenthesis
        split_index = match_paren.end()
        indicator_part = expr[:split_index].strip()  # e.g. "sma(period=14)"
        condition_part = expr[split_index:].strip()  # e.g. "> 50"

        # Extract the name of the indicator before "("
        match_name = re.match(r"([a-zA-Z_]+)\(", indicator_part)
        if not match_name:
            return None, {}, condition_part

        indicator_name = match_name.group(1).lower()

        # Extract the inside of parentheses "period=14, arg2=val2..."
        inside_paren = re.search(r"\(([^)]*)\)", indicator_part)
        params_str = inside_paren.group(1).strip() if inside_paren else ""

        # Convert those parameters into a dictionary, e.g. {"period": 14}
        kwargs = {}
        if params_str:
            param_pairs = [x.strip() for x in params_str.split(",") if x.strip()]
            for pair in param_pairs:
                if "=" in pair:
                    k, v = pair.split("=")
                    k = k.strip()
                    v = v.strip()
                    # Attempt to parse numeric
                    try:
                        val = float(v)
                        if val.is_integer():
                            val = int(val)
                        kwargs[k] = val
                    except ValueError:
                        # If it fails, store as a string
                        kwargs[k] = v

        return indicator_name, kwargs, condition_part

    # Work on a copy so we don’t alter the original DataFrame in place
    df = df.copy()

    # 3) Parse each user expression and apply the corresponding function
    for expr in indicators_list:
        indicator_name, kwargs_dict, trailing_condition = parse_indicator_expr(expr)
        if not indicator_name:
            print(f"Could not parse expression: '{expr}'")
            continue

        if indicator_name not in supported_indicators:
            print(f"Indicator '{indicator_name}' is not supported.")
            continue

        # Get the period from the user-supplied arguments, or default to 14
        timeperiod = kwargs_dict.get("period", 14)

        # Call your custom function with (df, timeperiod)
        # Example: df = SMA(df, 14)
        try:
            df = supported_indicators[indicator_name](df, timeperiod)
        except Exception as e:
            print(f"Error computing {indicator_name}({timeperiod}) for '{expr}': {e}")
            continue

        # Now, by default, your function might have created df['sma'] or df['ema'] etc.
        # If you want a unique column name, rename it here:
        # e.g. "sma" -> "SMA_14", "ema" -> "EMA_14", etc.
        col_created = indicator_name  # e.g. "sma", "ema", "slope_sma", etc.
        rename_to = f"{indicator_name.upper()}_{timeperiod}"
        if col_created in df.columns:
            df.rename(columns={col_created: rename_to}, inplace=True)
        else:
            # If your function named the column differently, adjust as needed
            pass

        # 4) If there's a trailing condition (e.g. "> 50"), create a boolean column
        if trailing_condition:
            condition_col = f"{rename_to}_cond"
            match_cond = re.match(r"([><=!]+)\s*(\d+\.?\d*)", trailing_condition)
            if match_cond and rename_to in df.columns:
                operator_ = match_cond.group(1)
                threshold_ = float(match_cond.group(2))
                if operator_ == ">":
                    df[condition_col] = df[rename_to] > threshold_
                elif operator_ == "<":
                    df[condition_col] = df[rename_to] < threshold_
                elif operator_ == ">=":
                    df[condition_col] = df[rename_to] >= threshold_
                elif operator_ == "<=":
                    df[condition_col] = df[rename_to] <= threshold_
                elif operator_ == "==":
                    df[condition_col] = df[rename_to] == threshold_
                else:
                    df[condition_col] = False
            else:
                # If the condition format is something else, or column not found
                df[condition_col] = False

    # 5) Optionally handle entry_conditions / combination_logic
    print(f"Received {len(entry_conditions)} entry conditions.")
    print(f"User combination logic: {combination_logic}")

    return df