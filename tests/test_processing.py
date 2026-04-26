import polars as pl
import numpy as np
import pytest
import datetime
from src.processing import calculate_snr, process_market_indicators, calculate_ccl_indicators

def test_calculate_snr_trend():
    # Linear trend with no noise should have high SNR
    series = np.linspace(10, 100, 100)
    snr = calculate_snr(series)
    # std(linear trend) is high, std(noise) should be near 0
    assert snr > 10

def test_calculate_snr_low_length():
    series = np.array([1, 2, 3])
    snr = calculate_snr(series, window_length=31)
    assert np.isnan(snr)

def test_process_market_indicators():
    # Use a fixed date range
    dates = [datetime.date(2023, 1, 1) + datetime.timedelta(days=i) for i in range(100)]
    df = pl.DataFrame({
        "Date": dates,
        "Close": np.linspace(100, 200, 100), # Deterministic trend
        "Ticker": ["TEST"] * 100
    })
    
    processed = process_market_indicators(df, window_len=31)
    
    assert "Return" in processed.columns
    assert "Rolling_Std" in processed.columns
    assert "Is_Anomaly" in processed.columns
    assert "Smoothed_Trend" in processed.columns
    assert len(processed) == 100

def test_calculate_ccl_indicators():
    # Fix the data construction for Polars
    dt = datetime.date(2023, 1, 1)
    df = pl.DataFrame({
        "Date": [dt, dt, dt],
        "Ticker": ["GGAL.BA", "GGAL", "ARS=X"],
        "Close": [1000.0, 100.0, 800.0]
    })
    
    ccl_df = calculate_ccl_indicators(df)
    
    assert len(ccl_df) == 1
    # GGAL.BA=1000, GGAL=100 -> CCL = 1000*10/100 = 100.0
    assert ccl_df["CCL_Price"][0] == 100.0
    # Brecha vs ARS=X (800): (100 / 800 - 1) * 100 = -87.5
    assert ccl_df["Brecha_Pct"][0] == -87.5
