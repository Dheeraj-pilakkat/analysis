# features.py

import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna


def add_technical_indicators(df):
    """
    Adds a comprehensive set of technical indicators to the dataframe.
    """
    # Add all ta features
    df = add_all_ta_features(
        df,
        open="Open",
        high="High",
        low="Low",
        close="Close",
        volume="Volume",
        fillna=True,
    )
    return df


def add_returns_and_volatility(df):
    """
    Adds daily returns and rolling volatility to the dataframe.
    """
    df["daily_return"] = df["Close"].pct_change()
    df["rolling_volatility_30d"] = df["daily_return"].rolling(window=30).std() * (
        252**0.5
    )  # Annualized
    return df


def generate_features(df):
    """
    Main function to generate all features for the model.
    """
    MIN_DATAFRAME_LENGTH = 90
    if len(df) < MIN_DATAFRAME_LENGTH:
        return pd.DataFrame()

    df = add_technical_indicators(df)
    df = add_returns_and_volatility(df)

    # Drop columns with too many NaNs that might have been created
    df.dropna(axis=1, how="all", inplace=True)
    df.dropna(axis=0, inplace=True)

    return df
