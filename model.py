# model.py

import os

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential, load_model

# --- Model Configuration ---
MODEL_DIR = "models"
MODEL_FILENAME_TPL = os.path.join(MODEL_DIR, "{}_lstm_model.keras")
LOOKBACK_WINDOW = 60
PREDICTION_HORIZON = 1
TARGET_VARIABLE = "Close"

# Ensure model directory exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


def preprocess_data(df, lookback_window=LOOKBACK_WINDOW):
    """
    Prepares the data for the LSTM model.
    - Scales the data.
    - Creates sequences of data.
    """
    if df.empty or len(df) <= lookback_window:
        return None, None, None, None

    # Use a subset of features for simplicity, or all numeric.
    features = df.select_dtypes(include=np.number).columns.tolist()
    if TARGET_VARIABLE not in features:
        raise ValueError(
            f"Target variable '{TARGET_VARIABLE}' not in dataframe columns."
        )

    data = df[features].values

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    for i in range(lookback_window, len(scaled_data) - PREDICTION_HORIZON + 1):
        X.append(scaled_data[i - lookback_window : i, :])
        y.append(
            scaled_data[i + PREDICTION_HORIZON - 1, features.index(TARGET_VARIABLE)]
        )

    if not X:
        return None, None, None, None

    return np.array(X), np.array(y), scaler, features


def build_lstm_model(input_shape):
    """
    Builds the LSTM model architecture.
    """
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=25))
    model.add(Dense(units=1))

    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


@st.cache_resource
def train_model(ticker, df_features, force_retrain=False):
    """
    Trains the LSTM model for a given ticker or loads a pre-trained one.
    """
    model_path = MODEL_FILENAME_TPL.format(ticker.replace(".NS", ""))

    if os.path.exists(model_path) and not force_retrain:
        st.write("Loading pre-trained model...")
        return load_model(model_path), None, None

    st.write(f"Training new model for {ticker}...")

    X, y, scaler, features = preprocess_data(df_features)

    if X is None or y is None:
        st.error("Not enough data to train the model after preprocessing.")
        return None, None, None

    # Time-based split
    split_index = int(len(X) * 0.8)
    X_train, X_val = X[:split_index], X[split_index:]
    y_train, y_val = y[:split_index], y[split_index:]

    if len(X_train) == 0 or len(X_val) == 0:
        st.error("Train or validation set is empty. Cannot train model.")
        return None, None, None

    model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))

    early_stopping = EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True
    )

    history = model.fit(
        X_train,
        y_train,
        epochs=100,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[early_stopping],
        verbose=1,
    )

    model.save(model_path)
    st.success(f"Model for {ticker} trained and saved successfully.")

    return model, scaler, features


def predict_next_move(
    model, df_features, scaler, features, lookback_window=LOOKBACK_WINDOW
):
    """
    Predicts the next day's closing price.
    """
    if (
        model is None
        or scaler is None
        or df_features is None
        or len(df_features) < lookback_window
    ):
        return None, None

    last_sequence = df_features[features].values[-lookback_window:]
    scaled_sequence = scaler.transform(last_sequence)

    X_pred = np.array([scaled_sequence])

    predicted_price_scaled = model.predict(X_pred)

    # We need to inverse transform the prediction.
    # To do this, we create a dummy array with all features, put our prediction
    # in the 'Close' column, and then inverse transform.
    num_features = len(features)
    dummy_array = np.zeros((1, num_features))

    close_idx = features.index(TARGET_VARIABLE)
    dummy_array[0, close_idx] = predicted_price_scaled[0, 0]

    predicted_price = scaler.inverse_transform(dummy_array)[0, close_idx]

    last_close = df_features[TARGET_VARIABLE].iloc[-1]

    direction = "Up" if predicted_price > last_close else "Down"
    confidence = (
        np.abs(predicted_price - last_close) / last_close
    )  # Simplistic confidence

    return direction, predicted_price, confidence
