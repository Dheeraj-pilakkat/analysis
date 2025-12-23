# ui_components.py

from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from data_loader import INDICES, NIFTY_50_TICKERS, get_live_price


def render_sidebar():
    """Renders the sidebar controls and returns user selections."""
    st.sidebar.header("Settings")

    # Exchange selection (currently just a placeholder)
    st.sidebar.selectbox(
        "Exchange",
        ["NSE", "BSE"],
        index=0,
        disabled=False,
        help="Currently only NSE tickers are supported.",
    )

    # Ticker selection
    ticker = st.sidebar.selectbox(
        "Select Ticker",
        options=NIFTY_50_TICKERS,
        index=0,  # Default to Reliance
        help="Select a stock from the NIFTY 50 list.",
    )

    # Date range selection
    end_date = datetime.now()
    start_date = st.sidebar.date_input(
        "Start Date", end_date - timedelta(days=365 * 5)
    )  # 5 years of data
    end_date = st.sidebar.date_input("End Date", end_date)

    # Model options
    st.sidebar.subheader("Model Settings")
    lookback_window = st.sidebar.slider(
        "Lookback Window", 30, 90, 60, help="Number of past days to use for prediction."
    )
    force_retrain = st.sidebar.checkbox("Force Model Retraining", value=False)

    return ticker, start_date, end_date, lookback_window, force_retrain


def render_stock_snapshot(ticker):
    """Displays a snapshot of the selected stock's live data."""
    st.subheader(f"Live Snapshot: {ticker}")
    live_data = get_live_price(ticker)

    if live_data:
        delta = f"{live_data['Change']:.2f} ({live_data['% Change']:.2f}%)"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("LTP", f"₹{live_data['LTP']:.2f}", delta=delta)
        col2.metric("Volume", f"{live_data['Volume']:,}")
        col3.metric("Day High", f"₹{live_data['Day High']:.2f}")
        col4.metric("Day Low", f"₹{live_data['Day Low']:.2f}")
    else:
        st.warning("Could not fetch live data for the selected ticker.")


def render_index_snapshots():
    """Displays snapshots of major market indices."""
    st.subheader("Major Indices")
    cols = st.columns(len(INDICES))

    for i, (name, ticker) in enumerate(INDICES.items()):
        with cols[i]:
            live_data = get_live_price(ticker)
            if live_data:
                delta = f"{live_data['Change']:.2f} ({live_data['% Change']:.2f}%)"
                st.metric(name, f"{live_data['LTP']:.2f}", delta=delta)


def render_charts(df_hist, df_features):
    """Displays interactive charts for price and technical indicators."""
    st.subheader("Charts & Technicals")

    # Candlestick chart with Moving Averages
    fig_price = go.Figure()
    fig_price.add_trace(
        go.Candlestick(
            x=df_hist.index,
            open=df_hist["Open"],
            high=df_hist["High"],
            low=df_hist["Low"],
            close=df_hist["Close"],
            name="Price",
        )
    )

    if "momentum_sma" in df_features.columns:  # Using a column from the ta library
        fig_price.add_trace(
            go.Scatter(
                x=df_features.index,
                y=df_features["trend_sma_fast"],
                mode="lines",
                name="20-Day SMA",
            )
        )
        fig_price.add_trace(
            go.Scatter(
                x=df_features.index,
                y=df_features["trend_sma_slow"],
                mode="lines",
                name="50-Day SMA",
            )
        )

    fig_price.update_layout(
        title="Price Candlestick Chart", xaxis_title="Date", yaxis_title="Price"
    )
    st.plotly_chart(fig_price, width="stretch")

    # RSI Chart
    if "momentum_rsi" in df_features.columns:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(
            go.Scatter(
                x=df_features.index,
                y=df_features["momentum_rsi"],
                mode="lines",
                name="RSI",
            )
        )
        fig_rsi.add_hline(
            y=70,
            line_dash="dash",
            line_color="red",
            annotation_text="Overbought",
            annotation_position="bottom right",
        )
        fig_rsi.add_hline(
            y=30,
            line_dash="dash",
            line_color="green",
            annotation_text="Oversold",
            annotation_position="top right",
        )
        fig_rsi.update_layout(title="Relative Strength Index (RSI)", yaxis_title="RSI")
        st.plotly_chart(fig_rsi, width="stretch")

    # MACD Chart
    if "trend_macd" in df_features.columns:
        fig_macd = go.Figure()
        fig_macd.add_trace(
            go.Scatter(
                x=df_features.index,
                y=df_features["trend_macd"],
                name="MACD",
                line_color="#1f77b4",
            )
        )
        fig_macd.add_trace(
            go.Scatter(
                x=df_features.index,
                y=df_features["trend_macd_signal"],
                name="Signal Line",
                line_color="#ff7f0e",
            )
        )
        fig_macd.add_bar(
            x=df_features.index,
            y=df_features["trend_macd_diff"],
            name="Histogram",
            marker_color="#2ca02c",
        )
        fig_macd.update_layout(title="MACD", yaxis_title="Value")
        st.plotly_chart(fig_macd, width="stretch")


def render_prediction_tab(prediction_data):
    """Displays the model's prediction."""
    st.subheader("Prediction")
    if prediction_data:
        direction, price, confidence = prediction_data
        st.write("Model's prediction for the next trading day:")

        color = "green" if direction == "Up" else "red"
        st.markdown(
            f"## Direction: <span style='color:{color};'>{direction}</span>",
            unsafe_allow_html=True,
        )
        st.metric("Predicted Close Price", f"₹{price:.2f}")
        st.metric("Confidence", f"{confidence * 100:.2f}%")

    else:
        st.info("Prediction is not available. This may be due to insufficient data.")


def render_report_tab(ticker, market_status, prediction, df_hist):
    """Renders the report preview and download button."""
    from reporting import generate_html_report, get_report_download_link

    st.subheader("Analysis Report")

    if market_status and prediction and not df_hist.empty:
        # Generate HTML report for preview
        html_report = generate_html_report(ticker, market_status, prediction, df_hist)
        st.components.v1.html(html_report, height=400, scrolling=True)

        # Generate download link
        download_link = get_report_download_link(
            ticker, market_status, prediction, df_hist
        )
        st.markdown(download_link, unsafe_allow_html=True)
    else:
        st.warning(
            "Cannot generate report. Ensure all data is loaded and model has run."
        )
