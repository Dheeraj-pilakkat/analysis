# data_loader.py

# from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

# NIFTY 50 tickers for autocomplete
NIFTY_50_TICKERS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "SBIN.NS",
    "KOTAKBANK.NS",
    "BHARTIARTL.NS",
    "ITC.NS",
    "HDFC.NS",
    "ASIANPAINT.NS",
    "WIPRO.NS",
    "AXISBANK.NS",
    "LT.NS",
    "MARUTI.NS",
    "BAJFINANCE.NS",
    "ULTRACEMCO.NS",
    "HCLTECH.NS",
    "SUNPHARMA.NS",
    "ADANIENT.NS",
    "TITAN.NS",
    "TATASTEEL.NS",
    "ONGC.NS",
    "TATAMOTORS.NS",
    "POWERGRID.NS",
    "NTPC.NS",
    "COALINDIA.NS",
    "INDUSINDBK.NS",
    "HINDALCO.NS",
    "JSWSTEEL.NS",
    "DRREDDY.NS",
    "M&M.NS",
    "GRASIM.NS",
    "CIPLA.NS",
    "ADANIPORTS.NS",
    "SBILIFE.NS",
    "BAJAJFINSV.NS",
    "EICHERMOT.NS",
    "DIVISLAB.NS",
    "HEROMOTOCO.NS",
    "BRITANNIA.NS",
    "APOLLOHOSP.NS",
    "UPL.NS",
    "NESTLEIND.NS",
    "TECHM.NS",
    "BPCL.NS",
    "TATACONSUM.NS",
    "WIPRO.NS",
]

# Major indices
INDICES = {"NIFTY 50": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}


@st.cache_data(ttl=60 * 5)  # Cache for 5 minutes
def get_live_price(ticker):
    """Fetches live price data for a given ticker."""
    try:
        stock = yf.Ticker(ticker)

        data = stock.history(period="1d", interval="1m")
        if data.empty:
            # Fallback to previous day's close if no intraday data
            data = stock.history(period="2d")
            if not data.empty:
                latest = data.iloc[-1]
                prev_close = data.iloc[-2]["Close"]
                change = latest["Close"] - prev_close
                percent_change = (change / prev_close) * 100
                return {
                    "LTP": latest["Close"],
                    "Change": change,
                    "% Change": percent_change,
                    "Volume": latest["Volume"],
                    "Day High": latest["High"],
                    "Day Low": latest["Low"],
                }
        else:
            latest = data.iloc[-1]
            prev_close = stock.history(period="2d").iloc[-2]["Close"]
            change = latest["Close"] - prev_close
            percent_change = (change / prev_close) * 100
            return {
                "LTP": latest["Close"],
                "Change": change,
                "% Change": percent_change,
                "Volume": data["Volume"].sum(),
                "Day High": data["High"].max(),
                "Day Low": data["Low"].min(),
            }
    except Exception as e:
        st.error(f"Error fetching live price for {ticker}: {e}")
        return None
    return None


@st.cache_data(ttl=60 * 60)  # Cache for 1 hour
def get_historical_data(ticker, start_date, end_date):
    """Fetches historical OHLCV data for a given ticker and date range."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        return data
    except Exception as e:
        st.error(f"Error fetching historical data for {ticker}: {e}")
        return pd.DataFrame()


def get_nse_holidays():
    """Returns a list of NSE holidays. Placeholder function."""
    # In a real scenario, this would be fetched from a reliable source.
    # For now, we'll list a few common ones.
    return [
        "2025-01-26",
        "2025-03-25",
        "2025-04-14",
        "2025-05-01",
        "2025-08-15",
        "2025-10-02",
        "2025-10-31",
        "2025-12-25",
    ]


def adjust_for_holidays(df):
    """Adjusts data for market holidays by forward-filling missing dates."""
    holidays = get_nse_holidays()
    df = df.asfreq("B")  # B for business day
    df.index = pd.to_datetime(df.index)
    # This is a simplification. A more robust solution would handle holidays better.
    df = df.drop(holidays, errors="ignore")
    df.ffill(inplace=True)
    return df
