import logging
from src.config import TICKERS
from src.data_ingestion import fetch_market_data, clean_market_data, save_to_duckdb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for data ingestion.
    """
    try:
        logger.info("Starting market data ingestion...")
        
        # 1. Fetch
        raw_df = fetch_market_data(TICKERS, period="3y")
        
        # 2. Clean
        clean_df = clean_market_data(raw_df)
        
        # 3. Save
        save_to_duckdb(clean_df, "merval_data.db")
        
        logger.info("Ingestion completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to ingest data: {e}")
        exit(1)

if __name__ == "__main__":
    main()
