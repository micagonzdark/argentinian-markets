import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import polars as pl
    import duckdb
    import plotly.graph_objects as go
    return duckdb, go, mo, pl


@app.cell
def __(duckdb, pl):
    # Data Connection
    con = duckdb.connect("merval_data.db", read_only=True)
    # Load into a polars DataFrame
    df = con.execute("SELECT * FROM merval_prices").pl()
    tickers = df["Ticker"].unique().to_list()
    return con, df, tickers


@app.cell
def __(mo, tickers):
    # Interactivity
    ticker_dropdown = mo.ui.dropdown(
        options=tickers,
        value="^MERV" if "^MERV" in tickers else tickers[0],
        label="Select Ticker: "
    )
    theme_switch = mo.ui.switch(label="Dark Mode", value=False)
    return theme_switch, ticker_dropdown


@app.cell
def __(df, pl, ticker_dropdown):
    selected_ticker = ticker_dropdown.value
    
    # Filter by ticker
    df_filtered = df.filter(pl.col("Ticker") == selected_ticker)
    
    # Calculate daily percentage change (returns)
    df_calc = df_filtered.with_columns(
        (pl.col("Close") / pl.col("Close").shift(1) - 1).alias("Return")
    )
    
    # Calculate 14-day rolling standard deviation (volatility)
    df_calc = df_calc.with_columns(
        pl.col("Return").rolling_std(window_size=14).alias("Rolling_Std")
    )
    
    # Flag 'Anomalies'
    df_calc = df_calc.with_columns(
        (pl.col("Return").abs() > (2.5 * pl.col("Rolling_Std"))).alias("Is_Anomaly")
    )
    
    # Map Headlines for Contextual Intelligence
    HEADLINES = {
        "2023-08-14": "PASO Elections Shock",
        "2023-11-21": "Milei Wins Run-off Reaction",
        "2023-12-13": "Caputo Announces Devaluation",
        "2023-12-14": "Caputo Devaluation Market Adjustment",
        "2024-01-24": "General Strike",
        "2024-06-10": "Ley Bases Senate Debate Starts",
        "2024-06-13": "Ley Bases Approved in Senate",
        "2024-08-05": "Global Market Sell-off (Black Monday)"
    }
    
    # Convert dates to string (YYYY-MM-DD) for lookup and map headlines
    df_calc = df_calc.with_columns(
        pl.col("Date").cast(pl.Utf8).str.slice(0, 10).replace(HEADLINES, default="Unknown Volatility Event").alias("Headline")
    )
    return HEADLINES, df_calc, selected_ticker


@app.cell
def __(df_calc, go, pl, selected_ticker, theme_switch):
    fig = go.Figure()
    
    # Base line chart
    fig.add_trace(go.Scatter(
        x=df_calc["Date"], 
        y=df_calc["Close"],
        mode='lines',
        name='Close Price',
        line=dict(color='#1f77b4')
    ))
    
    # Anomalies
    anomalies = df_calc.filter(pl.col("Is_Anomaly") == True)
    
    # Separate positives and negatives for coloring
    anomalies_pos = anomalies.filter(pl.col("Return") > 0)
    anomalies_neg = anomalies.filter(pl.col("Return") < 0)
    
    # Positive Anomalies
    if len(anomalies_pos) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies_pos["Date"], 
            y=anomalies_pos["Close"],
            mode='markers',
            name='Positive Anomaly',
            marker=dict(color='green', size=12, symbol='triangle-up', line=dict(width=1, color='darkgreen')),
            customdata=anomalies_pos["Headline"],
            hovertemplate="<b>Date:</b> %{x}<br><b>Price:</b> $%{y:.2f}<br><b>Event:</b> %{customdata}<extra></extra>"
        ))
    
    # Negative Anomalies
    if len(anomalies_neg) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies_neg["Date"], 
            y=anomalies_neg["Close"],
            mode='markers',
            name='Negative Anomaly',
            marker=dict(color='red', size=12, symbol='triangle-down', line=dict(width=1, color='darkred')),
            customdata=anomalies_neg["Headline"],
            hovertemplate="<b>Date:</b> %{x}<br><b>Price:</b> $%{y:.2f}<br><b>Event:</b> %{customdata}<extra></extra>"
        ))
    
    fig.update_layout(
        title=f"Price and Volatility for {selected_ticker}",
        xaxis_title="Date",
        yaxis_title="Close Price",
        template="plotly_dark" if theme_switch.value else "plotly_white",
        hovermode="x unified"
    )
    return anomalies, anomalies_neg, anomalies_pos, fig


@app.cell
def __(anomalies, fig, mo, theme_switch, ticker_dropdown):
    # UI Layout
    mo.vstack([
        mo.md("# Market Volatility Dashboard"),
        mo.hstack([ticker_dropdown, theme_switch], align="center", gap=2),
        mo.ui.plotly(fig),
        mo.md("### Anomaly Events Overview"),
        mo.ui.table(
            anomalies.select(["Date", "Close", "Return", "Headline"]),
            selection=None
        )
    ])
    return


if __name__ == "__main__":
    app.run()
