import yfinance as yf
import polars as pl
import pandas as pd
import duckdb

def fetch_and_store_data():
    tickers = ['^MERV', 'YPF', 'GGAL', 'GGAL.BA', 'ARS=X']
    all_data = []
    
    for ticker in tickers:
        print(f"Downloading data for {ticker}...")
        tkr = yf.Ticker(ticker)
        # Download last 3 years of daily data
        df = tkr.history(period="3y")
        df.reset_index(inplace=True)
        
        # Remove timezone to avoid issues with Polars/DuckDB conversion
        if 'Date' in df.columns and isinstance(df['Date'].dtype, pd.DatetimeTZDtype):
            df['Date'] = df['Date'].dt.tz_localize(None)
        elif 'Datetime' in df.columns and isinstance(df['Datetime'].dtype, pd.DatetimeTZDtype):
            df['Datetime'] = df['Datetime'].dt.tz_localize(None)
            
        pldf = pl.from_pandas(df)
        pldf = pldf.with_columns(pl.lit(ticker).alias("Ticker"))
        all_data.append(pldf)

    print("Combining data...")
    final_df = pl.concat(all_data, how="vertical_relaxed")
    
    print("Cleaning data...")
    # Sort by Ticker and Date
    date_col = "Date" if "Date" in final_df.columns else "Datetime"
    final_df = final_df.sort(["Ticker", date_col])
    
    # Forward fill missing values within each ticker
    cols_to_fill = ["Open", "High", "Low", "Close", "Volume"]
    actual_cols_to_fill = [c for c in cols_to_fill if c in final_df.columns]
    
    final_df = final_df.with_columns([
        pl.col(c).fill_null(strategy="forward").over("Ticker") for c in actual_cols_to_fill
    ])
    # Drop any remaining rows where prices are still null (e.g., at the very start)
    final_df = final_df.drop_nulls(subset=actual_cols_to_fill)
    
    db_path = "merval_data.db"
    print(f"Saving data to {db_path}...")
    
    # Store in DuckDB
    con = duckdb.connect(db_path)
    con.register('final_df_view', final_df)
    con.execute("CREATE OR REPLACE TABLE merval_prices AS SELECT * FROM final_df_view")
    
    print("\nFirst 5 rows of the saved database:")
    res = con.execute("SELECT * FROM merval_prices LIMIT 5").df()
    print(res.to_string())
    
    con.close()
    print("\nSuccess!")

if __name__ == "__main__":
    fetch_and_store_data()
