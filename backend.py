from stockalerter.utils import ops, supported_indicators, inverse_map, period_and_input, period_only, log_to_discord, send_alert
from stockalerter.indicators_lib import *
import re
import datetime
import pandas as pd

def extract_params(s):
    """
    extract_params("period=40,input=Close") turns into
    {'period': '40', 'input': 'Close'}
    """
    depth = 0
    parts = []
    start = 0
    for i,char in enumerate(s):
        if char == '(':
            depth+=1
        elif char == ')':
            depth-=1
        elif char == ',' and depth == 0:
            parts.append(s[start:i])
            start = i + 1
            
    parts.append(s[start:])

    return {k:v for k,v in [x.split("=",1) for x in parts]}


def is_number(s):
    """
    isnumeric() does not work for decimal or negative values, hence this is used
    """
    try:
        float(s)
        return True
    except ValueError:
        return False
    
# HELPER FUNCS TO WORK WITH BOOLS
def is_bool(s):
    temp = s.lower()
    if temp =="false" or temp=="true":
        return True
    return False

def str_to_bool(s):
    s = s.strip().lower()
    if s == "true":
        return True
    if s == "false":
        return False
    raise ValueError(f"Cannot convert {s!r} to bool")


# This function creates a saveable dict of indicators (nested)
# Contains all information to get one number out of it
# Debug mode turns on print statements

def ind_to_dict(ind, debug_mode = False):
    
    ind = ind.replace(" ","")

    # CHECKS FOR STANDALONE NUMBERS
    if is_number(ind):
        ind_dict = {"isNum" : True,
                    "number": int(ind),
                    "operable" : True,
                    "specifier" : -1}
        return ind_dict
    
    # CHECKS FOR BOOLS
    if is_bool(ind):
        ind_dict = {"isBool" : True,
                    "boolean" : str_to_bool(ind),
                    "operable" : True,
                    "specifier" : -1}
        
        return ind_dict
    
    # CHECKS FOR OHLC
    if len(ind.split("(")) == 1:
        func = ind.split("[")[0]
        specifier = ind.split("[")[1].split("]")[0]
        return {'ind':func,
                'specifier':specifier,
                "operable":True}

    
    func = ind.split("(")[0]

    if debug_mode:
        print(f"Working on {func}")
    
    params = ind[(ind.find("(") + 1) : ind.rfind(")")]
    ind_dict =  extract_params(params)
    if "input" not in ind_dict:
        ind_dict["input"] = "Close"

    ind_dict['ind'] = func
    ind_dict['operable'] = True

    if len(ind.split("[")) > 1:
        ind_dict['specifier'] = ind.split("[")[1].split("]")[0]
    if ind_dict['input'].lower() not in ['open', 'high', 'low', 'close']:
        ind_dict['operable'] = False
        ind_dict['input'] = ind_to_dict(ind_dict['input'])

    return ind_dict

# MAKE SPLITTING ON OPERATORS WORK

def simplify_conditions(cond, breakout_flag = False):
    """
    Trivial Case:
    convert rsi(period=14, input=Close)[-1]>sma(period=50, input=Close)[-1] to {cond1, cond2, comparison, breakoutflag=False}

    Breakout() Case:
    breakout(rsi(period=80, input=Close)[-1]<rsi(period=50, input=Close)[-1]) to {cond1, cond2, comparison, breakoutflag=True}
    """
    cond = cond.replace(" ", "")  # Remove spaces
    operators = sorted(list(inverse_map.keys()), key=len, reverse=True)  # Sort by length (longest first)

    # If the condition starts with "breakout"
    if cond[0:8] == "breakout":
        return simplify_conditions(cond[9:-1], True)

    # For multi-character and single-character operators
    for operator in operators:
        if operator in cond:
            # Split the condition by the operator
            ind1, ind2 = cond.split(operator, 1)  # Split only once
            return {
                'ind1': ind_to_dict(ind1),
                'ind2': ind_to_dict(ind2),
                'comparison': operator,
                'breakout_flag': breakout_flag
            }
    
def apply_function(df, ind, vals= None, debug_mode = False):
    # If it is a flat number, simply return it
    if 'isNum' in ind and ind['isNum']:
        return ind['number']
    
    if 'isBool' in ind and ind['isBool']:
        return ind['boolean']

    func = ind['ind']

    if debug_mode:
        print(f'At position 1, and func is {func}')

    if func in ["Close", "Open", "High", "Low"]:
        calculated = df[func]
    
    # INPUT FRIENDLY
    elif func in period_and_input:
        if vals is None:
            calculated = supported_indicators[func](df, int(ind['period']), ind['input'])
        else:
            calculated = supported_indicators[func](df, int(ind['period']), vals)

    # CHECK TO SEE IF INPUT UNFRIENDLY RECIEVED INPUT
    elif ind['input'] not in ['Close', 'Open', 'High', 'Low']:
        raise ValueError("You entered input with a forbidden value")
    
    # INPUT UNFRIENDLY
    elif func in ['atr', 'cci', 'williamsr']:
        calculated = supported_indicators[func](df, int(ind['period']))    

    elif func == "sar":
        calculated = SAR(df, float(ind['acceleration']), float(ind['max_acceleration']))

    elif func == "bbands":
        calculated = BBANDS(df,int(ind['period']),float(ind['std_dev']),ind['type'])
        
    elif func == "macd":
        calculated = MACD(df,int(ind['fast_period']),int(ind['slow_period']),int(ind['signal_period']), ind['type'])

    elif func == "HARSI_Flip":
        calculated = HARSI_Flip(df, timeperiod=int(ind['period']), smoothing=float(ind['smoothing']))

    elif func == "SROCST":
        calculated = SROCST(df, ind['ma_type'], int(ind['lsma_offset']), int(ind['smoothing_length']), ind['kalman_src'], float(ind['sharpness']), float(ind['filter_period']), int(ind['roc_length']), int(ind['k_length']), int(ind['k_smoothing']), int(ind['d_smoothing']))


    if 'specifier' in ind:
        return calculated.iloc[int(ind['specifier'])]
    
        # DEPRECATED VERSION BUT WORKS
        #return calculated[int(ind['specifier'])]

    return calculated

def indicator_calculation(df, ind_dict, values = None, debug_mode = False):
    if debug_mode:
        print(f"at {ind_dict['ind']} and values are {values}, and it is {ind_dict['operable']}")

    if not ind_dict['operable'] and values is None: #Skips to deepest layer
        if debug_mode:
            print(f"Going from {ind_dict['ind']} to {ind_dict['input']}")
        values = indicator_calculation(df, ind_dict['input'], None, debug_mode)

    if ind_dict['operable']: #Only triggers at deepest layer
        if debug_mode:
            print(f"\nreached {ind_dict['input']}")
            print(ind_dict)
        values = (apply_function(df, ind_dict))
        return values
    
    if debug_mode:
        print(f"At {ind_dict['ind']} and values are {len(values)}")
    
    if values is not None: 
        if debug_mode:
            print(f"At {ind_dict['ind']}")
        values = (apply_function(df, ind_dict, values))
        return values
    
def evaluate_expression(df, exp, debug_mode=False):
    exp = simplify_conditions(exp)
    lhs = indicator_calculation(df, exp['ind1'])
    rhs = indicator_calculation(df, exp['ind2'])

    if debug_mode and not exp['breakout_flag']:
        print(f"LHS is {lhs} \nRHS is {rhs}")

    op = exp['comparison']
    if not exp['breakout_flag']:
        return bool(ops[op](lhs,rhs))
    
    # if breakout is there, we need to calculate yesterdays lhs and rhs too
    exp['ind1']['specifier'] = str(int(exp['ind1']['specifier'])-1)
    exp['ind2']['specifier'] = str(int(exp['ind2']['specifier'])-1)

    lhs_yest = indicator_calculation(df, exp['ind1'])
    rhs_yest = indicator_calculation(df, exp['ind2'])

    if debug_mode:
        print(f"LHS is {lhs} \nRHS is {rhs} \nLHS_yest is {lhs_yest} \nRHS_yest is {rhs_yest}\nExpression: {lhs}{op}{rhs}")

    return bool(ops[op](lhs,rhs) and ops[inverse_map(op)](lhs_yest,rhs_yest))

def validate_referenced_indices(expr, bools):
    import re
    referenced = set(int(num) for num in re.findall(r'\b\d+\b', expr))
    for idx in referenced:
        if not 1 <= idx <= len(bools):
            raise ValueError(f"Invalid reference: {idx} is out of range (1 to {len(bools)})")
    return referenced

def evaluate_boolean_expression(expr, bools):
    # Find all standalone numbers in the expression
    referenced = set(int(num) for num in re.findall(r'\b\d+\b', expr))

    # Replace each number with a variable like var_1, var_2, etc.
    for i in sorted(referenced, reverse=True):  # biggest to smallest to avoid partials
        expr = re.sub(rf'\b{i}\b', f'var_{i}', expr)

    context = {f'var_{i+1}': val for i, val in enumerate(bools)}
    
    return eval(expr, {}, context)


def evaluate_expression_list(df, exps, combination = '1'):
    """
    Wrapper on whole backend
    \nAccepts a list of expressions and combination logic, outputs a boolean value
    """
    bools = []
    for exp in exps:
        bools.append(evaluate_expression(df, exp))

    return evaluate_boolean_expression(combination,bools)



def check_alerts(stock, alert_data,timeframe):
    """
    """
    
    file_path = f"data/{stock}_{timeframe}.csv"
    df = pd.read_csv(file_path)
    
    if df.empty:
        print(f"[Alert Check] No data for {stock}, skipping alert check.")
        return

    # Filter alerts for this stock (case-insensitive ticker match)
    alert_timeframe = "1d" if timeframe == "daily" else "1wk"
    alerts = [alert for alert in alert_data if alert['ticker'].upper() == stock.upper() and alert['timeframe'] == alert_timeframe]
    
    for alert in alerts:
            
            log_to_discord(f"[Alert Check] Checking alert '{alert['name']}' for {stock}...")
            print(f"[Alert Check] Alert conditions: {alert['conditions']}")
            
            print(alert)
            print("Conditions:")
            condition = [item['conditions'] for item in alert['conditions']]
            print(condition)
            comb_logic = alert['combination_logic']
            result = evaluate_expression_list(df = df, exps = condition, combination='1' if len(comb_logic)==0 else comb_logic)
            
            print(f"Result: {result}")
            log_to_discord(f"Evaluating alert '{alert['name']}' for {stock}: condition '{condition}' evaluated to {result} at {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}.")

            if result:
                # Send alert via Discord
                send_alert(stock, alert, condition[0], df)
                log_to_discord(f"[Alert Check] Alert '{alert['name']}' triggered for {stock} with condition '{condition[0]}'.")
                # Update last triggered time
                alert["last_triggered"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                log_to_discord(f"[Alert Check] Alert '{alert['name']}' not triggered for {stock}.")
