# app.py
# To run: streamlit run app.py
from datetime import datetime

import streamlit as st

# --- Import custom modules ---
from data_loader import adjust_for_holidays, get_historical_data, get_live_price
from features import generate_features
from model import predict_next_move, train_model
from ui_components import (
    render_charts,
    render_index_snapshots,
    render_prediction_tab,
    render_report_tab,
    render_sidebar,
    render_stock_snapshot,
)

# --- Page Configuration ---
st.set_page_config(
    page_title="Indian Stock Market Analysis & Prediction",
    page_icon="🇮🇳",
    layout="wide",
)


# --- Main Application ---
def main():
    """
    The main function that runs the Streamlit application.
    """
    st.title("📈 Indian Stock Market Analysis & Prediction")
    st.markdown(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --- Sidebar ---
    ticker, start_date, end_date, lookback_window, force_retrain = render_sidebar()

    if not ticker:
        st.warning("Please select a ticker from the sidebar.")
        return

    # --- Data Loading ---
    with st.spinner(f"Loading historical data for {ticker}..."):
        df_hist = get_historical_data(ticker, start_date, end_date)
        if df_hist.empty:
            st.error(
                "Could not fetch historical data. Please check the ticker or date range."
            )
            return
        df_hist = adjust_for_holidays(df_hist)

    # --- Feature Engineering ---
    with st.spinner("Generating technical features..."):
        df_features = generate_features(df_hist.copy())
        if df_features.empty:
            st.error("Failed to generate features. The dataframe might be too small.")
            return

    # --- Model Training & Prediction ---
    with st.spinner(f"Loading model and making prediction for {ticker}..."):
        model, scaler, feature_list = train_model(ticker, df_features, force_retrain)

        prediction_data = None
        if model and scaler and feature_list and not df_features.empty:
            direction, price, confidence = predict_next_move(
                model, df_features, scaler, feature_list, lookback_window
            )
            prediction_data = (direction, price, confidence)

    # --- UI Layout (Tabs) ---
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Overview", "📈 Charts & Technicals", "🤖 Predictions", "📋 Report"]
    )

    with tab1:
        # Live Market Snapshots
        render_stock_snapshot(ticker)
        st.divider()
        render_index_snapshots()

        st.subheader("Recent Data")
        st.dataframe(df_hist)

    with tab2:
        render_charts(df_hist, df_features)

    with tab3:
        render_prediction_tab(prediction_data)

        st.subheader("Feature Data Used for Model")
        st.dataframe(df_features.tail())

    with tab4:
        live_data_for_report = get_live_price(ticker)
        render_report_tab(
            ticker,
            live_data_for_report,
            {
                "direction": prediction_data[0],
                "price": prediction_data[1],
                "confidence": prediction_data[2],
            }
            if prediction_data
            else None,
            df_hist.tail(100),
        )  # Pass last 100 days for chart

    # --- Disclaimer ---
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Disclaimer:** This tool is for educational and informational purposes only "
        "and does not constitute financial advice. Predictions are not guaranteed."
    )


if __name__ == "__main__":
    main()
