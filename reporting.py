# reporting.py

import base64
import io
from datetime import datetime

import jinja2
import plotly.graph_objects as go
import streamlit as st

# --- HTML Template for the report ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Analysis Report for {{ ticker }}</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        h1, h2 { color: #333; }
            p { margin-bottom: 1em;color: #333; }
        .summary, .prediction { border: 1px solid #eee; padding: 1em; margin-bottom: 1em; border-radius: 5px;background-color: #ffffff; }
        .chart { margin-top: 2em; }
        .disclaimer { font-size: 0.8em; color: #777; margin-top: 2em; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #ffffff; }
    </style>
</head>
<body>
    <h1>Stock Analysis Report: {{ ticker }}</h1>
    <p>Report generated on: {{ generation_date }}</p>

    <div class="summary">
        <h2>Market Snapshot</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Last Traded Price (LTP)</td><td>{{ market_status.LTP | round(2) }}</td></tr>
            <tr><td>Change</td><td>{{ market_status.Change | round(2) }}</td></tr>
            <tr><td>% Change</td><td>{{ '%.2f' % market_status['% Change'] }}%</td></tr>
            <tr><td>Volume</td><td>{{ '{:,}'.format(market_status.Volume) }}</td></tr>
        </table>
    </div>



    <div class="prediction">
        <h2>Model Prediction</h2>
        <p>Prediction for the next trading session:</p>
        <ul>
            <li><strong>Direction:</strong> {{ prediction.direction }}</li>
            <li><strong>Predicted Close:</strong> {{ prediction.price | round(2) }}</li>
            <li><strong>Confidence Score:</strong> {{ '%.2f' % (prediction.confidence * 100) }}%</li>
        </ul>
    </div>

    <div class="disclaimer">
        <p><strong>Disclaimer:</strong> This tool is for educational and informational purposes only and does not constitute financial advice. The predictions are based on a model and are not guaranteed.</p>
    </div>
</body>
</html>
"""


def generate_html_report(ticker, market_status, prediction, df_hist):
    """Renders the HTML report from the template."""
    template = jinja2.Template(HTML_TEMPLATE)

    report_data = {
        "ticker": ticker,
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_status": market_status,
        "prediction": prediction,
    }

    html_content = template.render(report_data)
    return html_content


def get_report_download_link(ticker, market_status, prediction, df_hist):
    """Generates a download link for the HTML report."""
    html_report = generate_html_report(ticker, market_status, prediction, df_hist)

    b64 = base64.b64encode(html_report.encode()).decode()
    filename = (
        f"{ticker.replace('.NS', '')}_report_{datetime.now().strftime('%Y%m%d')}.html"
    )

    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">Download HTML Report</a>'
    return href
