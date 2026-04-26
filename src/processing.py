import polars as pl
import numpy as np
from scipy.signal import savgol_filter
from typing import Dict, Any, List, Optional
import datetime

def calculate_snr(series: np.ndarray, window_length: int = 31, polyorder: int = 3) -> float:
    """
    Extracts the underlying 'Signal' using a Savitzky-Golay low-pass filter,
    calculates the 'Noise' (Original Price - Signal), and returns the Signal-to-Noise Ratio (SNR).
    """
    if len(series) < window_length:
        return np.nan
    
    # 1. Extract Signal
    signal = savgol_filter(series, window_length=window_length, polyorder=polyorder)
    
    # 2. Calculate Noise
    noise = series - signal
    
    # 3. Calculate Standard Deviations
    std_signal = np.std(signal)
    std_noise = np.std(noise)
    
    # 4. Return SNR Ratio
    if std_noise == 0:
        return np.inf
    return float(std_signal / std_noise)

def process_market_indicators(df: pl.DataFrame, window_len: int = 31) -> pl.DataFrame:
    """
    Calculates returns, volatility, anomalies and denoised trend using Polars.
    """
    # Calculate returns and rolling volatility
    df = df.with_columns([
        (pl.col("Close") / pl.col("Close").shift(1) - 1).alias("Return")
    ]).with_columns([
        pl.col("Return").rolling_std(window_size=14).alias("Rolling_Std")
    ])

    # Detect Anomalies (2.5 std devs)
    df = df.with_columns(
        (pl.col("Return").abs() > (2.5 * pl.col("Rolling_Std"))).alias("Is_Anomaly")
    )

    # Savitzky-Golay Denoising
    if len(df) > window_len:
        # We still need numpy for scipy, but we keep it encapsulated
        prices = df["Close"].to_numpy()
        smoothed = savgol_filter(prices, window_length=window_len, polyorder=3)
        df = df.with_columns(pl.Series("Smoothed_Trend", smoothed))
    else:
        df = df.with_columns(pl.col("Close").alias("Smoothed_Trend"))

    return df

def match_historical_events(df: pl.DataFrame, event_catalog: List[Dict[str, str]], tolerance_days: int = 4) -> pl.DataFrame:
    """
    Matches market dates with historical events using Polars optimized join_asof.
    This replaces the nested loop O(N*M) with a high-performance temporal join.
    """
    # Convert catalog to DataFrame and ensure Date type
    event_df = pl.DataFrame(event_catalog).with_columns(
        pl.col("date").str.to_date("%Y-%m-%d").alias("Date")
    ).sort("Date")

    # Ensure market df has Date type (cast from datetime if necessary)
    df = df.with_columns(pl.col("Date").cast(pl.Date)).sort("Date")
    
    # join_asof requires a shared key
    matched = df.join_asof(
        event_df.select(["Date", "title", "category"]),
        on="Date",
        strategy="nearest",
        tolerance=f"{tolerance_days}d"
    ).rename({
        "title": "Headline",
        "category": "Category"
    })

    # Fill nulls for days with no matching event
    return matched.with_columns([
        pl.col("Headline").fill_null("Unknown Anomaly Event"),
        pl.col("Category").fill_null("Unknown")
    ])

def calculate_ccl_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates the implicit Contado con Liquidación (CCL) rate and the gap (Brecha).
    """
    # Filter required tickers
    df_ggalba = df.filter(pl.col("Ticker") == "GGAL.BA").select(["Date", "Close"]).rename({"Close": "GGAL_BA_Close"})
    df_ggal = df.filter(pl.col("Ticker") == "GGAL").select(["Date", "Close"]).rename({"Close": "GGAL_Close"})
    df_arsx = df.filter(pl.col("Ticker") == "ARS=X").select(["Date", "Close"]).rename({"Close": "ARS_X_Close"})

    # Join and calculate
    df_ccl = df_ggalba.join(df_ggal, on="Date", how="inner").join(df_arsx, on="Date", how="inner")
    
    return df_ccl.with_columns([
        ((pl.col("GGAL_BA_Close") * 10) / pl.col("GGAL_Close")).alias("CCL_Price")
    ]).with_columns([
        (((pl.col("CCL_Price") / pl.col("ARS_X_Close")) - 1) * 100).alias("Brecha_Pct")
    ])
