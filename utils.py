from polygon import RESTClient
client = RESTClient(api_key="I0D0ldkssJgACZm3fcs9DlZAX5osmgZp")
from typing import cast
from urllib3 import HTTPResponse
import json
import pandas as pd
import datetime

def grab_new_data_polygon(ticker, timespan = "day", multiplier = 1):

    today = datetime.datetime.today().strftime('%Y-%m-%d')
    last_year = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')

    aggs = cast(
        HTTPResponse,
        client.get_aggs(ticker=ticker, multiplier=1, timespan=timespan, from_=last_year, to=today, raw=True),
    )

    data_str = aggs.data.decode("utf-8")
    data = json.loads(data_str)
    df = pd.DataFrame(data["results"])

    df.sort_values(by="t", ascending=True, inplace=True)
    df["Date"] = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert("America/New_York")
    df["Date"] = df["Date"].dt.strftime("%d-%m-%Y %H:%M:%S %Z")

    df.rename(columns={
        "o": "Open",
        "c": "Close",
        "h": "High",
        "l": "Low",
        "v": "Volume",
        "vw": "VWAP",
        "n": "Trades"
    }, inplace=True)

    # Drop original timestamp column
    df.drop(columns=["t"], inplace=True)
    df.set_index("Date", inplace=True)

    return df
