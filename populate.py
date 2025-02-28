from indicators import extract_indicators
from preprocess import parse_condition
from indicators_lib import *
import pandas as pd

def apply_indicators(df: pd.DataFrame, condition_string: str) -> pd.DataFrame:
    """
    Parses the user expression with parse_condition,
    extracts the indicators with extract_indicators,
    then calls the relevant indicator functions from indicators_lib.
    """
    print(f"Applying indicators for condition: {condition_string}")
    parse_tree, error = parse_condition(condition_string)
    print("DEBUG parse_tree:", parse_tree)
    if error:
        print(f"Parse error: {error}")
        return df  # or df.copy()

    inds_found = extract_indicators(parse_tree)

    # Map names to actual functions
    supported_indicators = {
        "sma": SMA,
        "ema": EMA,
        "hma": HMA,
        "slope_sma": SLOPE_SMA,
        "slope_ema": SLOPE_EMA,
        "slope_hma": SLOPE_HMA,
        "rsi": RSI,
        "atr": ATR,
        "cci": CCI,
        "bb": BBANDS,
        "roc": ROC,
        "williamsr": WILLR,
        "macd": MACD,
        "psar": SAR
    }

    df = df.copy()
    print(f"Indicators found: {inds_found}")
    for ind_tuple in inds_found:
        # e.g. ("rsi", "period=14")
        indicator_name = ind_tuple[0]
        print(f"indicators_name: {indicator_name}")

        timeperiod = None
        fast_period = None
        slow_period = None
        signal_period = None
        std_dev_val = None
        line_type = None  # e.g. "upper","lower","middle" for BBANDS
        acceleration = None
        max_acceleration = None
        type = None  # e.g. "signal","line" for MACD


        if indicator_name not in supported_indicators:
            print(f"Unsupported indicator: {indicator_name}")

        for param in ind_tuple[1:]:
            if "period=" in param:
                val_str = param.split("=")[1]
                print(f"val_str: {val_str}")
                timeperiod = int(val_str)

            elif "fast_period=" in param:
                val_str = param.split("=")[1]
                fast_period = int(val_str)

            elif "slow_period=" in param:
                val_str = param.split("=")[1]
                slow_period = int(val_str)

            elif "signal_period=" in param:
                val_str = param.split("=")[1]
                signal_period = int(val_str)

            elif "std_dev=" in param:
                val_str = param.split("=")[1]
                std_dev_val = float(val_str)

            elif "type=" in param:
                # For BBANDS (upper, middle, lower) or MACD (line, signal), etc.
                val_str = param.split("=")[1]
                type = val_str  

            elif "acceleration=" in param:
                val_str = param.split("=")[1]
                acceleration = float(val_str)

            elif "max_acceleration=" in param:
                val_str = param.split("=")[1]
                max_acceleration = float(val_str)

        if indicator_name == "sma":
            arr = SMA(df, timeperiod)
            col_name = f"SMA_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "ema":
            arr = EMA(df, timeperiod)
            col_name = f"EMA_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "rsi":
            arr = RSI(df, timeperiod)
            col_name = f"RSI_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "atr":
            arr = ATR(df, timeperiod)
            col_name = f"ATR_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "cci":
            arr = CCI(df, timeperiod)
            col_name = f"CCI_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "hma":
            arr = HMA(df, timeperiod)
            col_name = f"HMA_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "slope_sma":
            arr = SLOPE_SMA(df, timeperiod)
            col_name = f"SLOPE_SMA_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "slope_ema":
            arr = SLOPE_EMA(df, timeperiod)
            col_name = f"SLOPE_EMA_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "slope_hma":
            arr = SLOPE_HMA(df, timeperiod)
            col_name = f"SLOPE_HMA_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "bb":
            # e.g. "bb(period=20,std_dev=2,type=upper)"
            arr = BBANDS(df, timeperiod, std_dev_val, line_type)
            col_name = f"BB_{line_type}_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "roc":
            arr = ROC(df, timeperiod)
            col_name = f"ROC_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "williamsr":
            arr = WILLR(df, timeperiod)
            col_name = f"WILLR_{timeperiod}"
            df[col_name] = arr

        elif indicator_name == "macd":
            arr = MACD(df, fast_period, slow_period, signal_period, line_type)
            col_name = f"MACD_{line_type}_{fast_period}_{slow_period}_{signal_period}"
            df[col_name] = arr

        elif indicator_name == "psar":
            arr = SAR(df, acceleration, max_acceleration)
            col_name = f"PSAR_{acceleration}_{max_acceleration}"
            df[col_name] = arr

        else:
            print(f"Indicator '{indicator_name}' not recognized—skipping.")
            continue



        # result_array = supported_indicators[indicator_name](df, timeperiod)

        # col_name = f"{indicator_name.upper()}_{timeperiod}"
        # df[col_name] = result_array
        # cols_created.append(col_name)

    return df