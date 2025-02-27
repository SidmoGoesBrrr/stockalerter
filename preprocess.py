from pyparsing import (
    Or, CaselessLiteral, Word, alphas, alphanums, nums, Forward, Group, Optional, oneOf, Keyword, Suppress, Literal, ZeroOrMore, Combine
)

# Define basic components
band_input = Combine(Literal("upper") | Literal("middle") | Literal("lower"))
sig_input = Combine(Literal("signal") | Literal("line"))
identifier = Word(alphas, alphanums + "_")  # Convert to lowercase
tf = Combine("timeframe=" + Word(alphanums+'_'))
integer = Word(nums)  # Matches integers like "1", "2"
float_number = Combine(Word(nums) + "." + Word(nums) | Word(nums))
numeric_literal = Combine(Optional(Literal("-")) + (float_number | Word(nums)))
period_with_brackets = Suppress("(") + Combine("period=" + integer) + Optional(Suppress(",") + tf) + Suppress(")")

index = Combine(Combine(Literal("-") + integer) | integer)  # Matches both negative indices (e.g., "-1") and non-negative indices (e.g., "0", "1")

# Define index parsing
index_with_brackets = Combine(Literal("[") + index + Literal("]"))

# Define individual indicator patterns
sma = Group(Literal("sma") + period_with_brackets + index_with_brackets)

ema = Group(Literal("ema") + period_with_brackets + index_with_brackets)

hma = Group(Literal("hma") + period_with_brackets + index_with_brackets)

slope_sma = Group(Literal("slope_sma") + period_with_brackets + index_with_brackets)

slope_ema = Group(Literal("slope_ema") + period_with_brackets + index_with_brackets)

slope_hma = Group(Literal("slope_hma") + period_with_brackets + index_with_brackets)

rsi = Group(Literal("rsi") + period_with_brackets + index_with_brackets)

macd = Group(
    Literal("macd") + Suppress("(") +
    Combine("fast_period=" + integer) + Suppress(",") +
    Combine("slow_period=" + integer) + Suppress(",") +
    Combine("signal_period=" + integer) + Suppress(",") +
    Combine("type=" + sig_input) + Optional(Suppress(",") + 
    tf) + Suppress(")") + index_with_brackets
)

bb = Group(
    Literal("bb") + Suppress("(") +
    Combine("period=" + integer) + Suppress(",") +
    Combine("std_dev=" + float_number) + Suppress(",") +
    Combine("type=" + band_input) + Optional(Suppress(",") + 
    tf) + Suppress(")") + index_with_brackets
)

atr = Group(Literal("atr") + period_with_brackets + index_with_brackets)

psar = Group(
    Literal("psar") + Suppress("(") +
    Combine("acceleration=" + float_number) + Suppress(",") +
    Combine("max_acceleration=" + float_number) + Optional(Suppress(",") + 
    tf) + Suppress(")") + index_with_brackets
)

cci = Group(Literal("cci") + period_with_brackets + index_with_brackets)

williamsr = Group(Literal("williamsr") + period_with_brackets + index_with_brackets)

roc = Group(Literal("roc") + period_with_brackets + index_with_brackets)


price = Group(oneOf("close open high low") + Optional(Suppress('(') + tf + Suppress(')')) + index_with_brackets)

# Combine all valid operands
operand = sma | hma | ema | slope_sma | slope_ema | slope_hma | rsi | macd | bb | atr | psar | cci | williamsr | roc | price | numeric_literal

# Define comparison operators
comparison_operator = oneOf("> < >= <= == !=")

# Forward declaration for complex expressions
expression = Forward()

# Define the BREAKOUT keyword
breakout = Group(Keyword("breakout") + Suppress("(") + expression + Suppress(")"))


# Define a condition: lhs operator rhs
condition = Group(operand + comparison_operator + operand)

# Define logical operators (only OR now)
logical_operator = oneOf("or and")

parenthesized_expression = Group(Suppress("(") + expression + Suppress(")"))


# Define the full expression grammar
expression <<= (breakout | condition | parenthesized_expression) + ZeroOrMore(logical_operator + (breakout | condition | parenthesized_expression))



# Parse input and generate the parse tree
def parse_condition(condition):
    """
    Parses a condition string and generates a parse tree.

    Args:
        condition (str): The user-defined condition string.

    Returns:
        list: Parsed condition as a tree.
        str: Error message if parsing fails.
    """
    condition = condition.lower()
    condition = condition.replace(" ","").replace("or", " or ").replace("and"," and ")

    #print(condition)
    try:
        # Parse the input
        parsed = expression.parseString(condition, parseAll=True).asList()
        return parsed, None
    except Exception as e:
        return None, str(e)