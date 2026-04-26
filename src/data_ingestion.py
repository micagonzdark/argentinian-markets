import yfinance as yf
import polars as pl
import pandas as pd
import duckdb
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_market_data(tickers: List[str], period: str = "3y") -> pl.DataFrame:
    """
    Downloads historical data from Yahoo Finance and returns a combined Polars DataFrame.
    """
    all_data = []
    
    for ticker in tickers:
        logger.info(f"Downloading data for {ticker}...")
        try:
            tkr = yf.Ticker(ticker)
            df = tkr.history(period=period)
            
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                continue
                
            df.reset_index(inplace=True)
            
            # Remove timezone to ensure compatibility with DuckDB/Polars
            date_col = "Date" if "Date" in df.columns else "Datetime"
            if isinstance(df[date_col].dtype, pd.DatetimeTZDtype):
                df[date_col] = df[date_col].dt.tz_localize(None)
                
            pldf = pl.from_pandas(df)
            pldf = pldf.with_columns(pl.lit(ticker).alias("Ticker"))
            all_data.append(pldf)
        except Exception as e:
            logger.error(f"Error downloading {ticker}: {e}")

    if not all_data:
        raise ValueError("No data was downloaded for any ticker.")

    return pl.concat(all_data, how="vertical_relaxed")

def clean_market_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Sorts, fills missing values, and cleans the market data.
    """
    date_col = "Date" if "Date" in df.columns else "Datetime"
    
    # Standardize date column name to 'Date'
    if date_col == "Datetime":
        df = df.rename({"Datetime": "Date"})
        date_col = "Date"

    df = df.sort(["Ticker", date_col])
    
    # Forward fill missing values within each ticker group
    cols_to_fill = ["Open", "High", "Low", "Close", "Volume"]
    actual_cols_to_fill = [c for c in cols_to_fill if c in df.columns]
    
    df = df.with_columns([
        pl.col(c).fill_null(strategy="forward").over("Ticker") for c in actual_cols_to_fill
    ])
    
    # Drop rows where prices are still null (e.g., first rows of a ticker history)
    return df.drop_nulls(subset=actual_cols_to_fill)

def save_to_duckdb(df: pl.DataFrame, db_path: str, table_name: str = "merval_prices"):
    """
    Saves a Polars DataFrame to a DuckDB table.
    """
    logger.info(f"Saving data to {db_path} table {table_name}...")
    con = duckdb.connect(db_path)
    try:
        # Register the polars dataframe as a virtual view for DuckDB
        con.register('df_view', df)
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_view")
    finally:
        con.close()
    logger.info("Successfully saved to DuckDB.")
