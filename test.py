from utils import grab_new_data_yfinance

df = grab_new_data_yfinance("AAPL")
print(df)