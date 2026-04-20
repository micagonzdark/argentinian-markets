import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")

@app.cell
def _():
    import marimo as mo
    import polars as pl
    import duckdb
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from scipy.signal import savgol_filter
    import datetime

    return datetime, duckdb, go, make_subplots, mo, pl, savgol_filter

@app.cell
def _(duckdb, pl):
    # Data Connection
    con = duckdb.connect("merval_data.db", read_only=True)
    # Load into a polars DataFrame
    df = con.execute("SELECT * FROM merval_prices").pl()
    
    # Exclude GGAL.BA from the primary ticker dropdown so it's not analyzed as a main asset directly, it's used for CCL
    tickers = [t for t in df["Ticker"].unique().to_list() if t != "GGAL.BA"]
    
    # --- Calculate CCL and Brecha ---
    df_ggalba = df.filter(pl.col("Ticker") == "GGAL.BA").select(["Date", "Close"]).rename({"Close": "GGAL_BA_Close"})
    df_ggal = df.filter(pl.col("Ticker") == "GGAL").select(["Date", "Close"]).rename({"Close": "GGAL_Close"})
    df_arsx = df.filter(pl.col("Ticker") == "ARS=X").select(["Date", "Close"]).rename({"Close": "ARS_X_Close"})
    
    df_ccl = df_ggalba.join(df_ggal, on="Date", how="inner").join(df_arsx, on="Date", how="inner")
    
    # Calculate implicit CCL: (GGAL.BA * 10) / GGAL
    df_ccl = df_ccl.with_columns(
        ((pl.col("GGAL_BA_Close") * 10) / pl.col("GGAL_Close")).alias("CCL_Price")
    )
    
    # Calculate Brecha (% gap between CCL and Official ARS=X)
    df_ccl = df_ccl.with_columns(
        (((pl.col("CCL_Price") / pl.col("ARS_X_Close")) - 1) * 100).alias("Brecha_Pct")
    )
    
    return con, df, df_ccl, tickers

@app.cell
def _(mo, tickers):
    EVENT_CATALOG = [
        {"date": "2023-04-25", "title": "Blue Dollar historic surge past 400 ARS", "category": "Market/External"},
        {"date": "2023-06-24", "title": "Sergio Massa announced as UP candidate", "category": "Political/Rumor"},
        {"date": "2023-08-14", "title": "PASO Elections Shock: Milei wins, 22% Devaluation", "category": "Official Measure"},
        {"date": "2023-10-23", "title": "General Elections: Massa vs Milei run-off", "category": "Political/Rumor"},
        {"date": "2023-11-20", "title": "Javier Milei wins Presidential Run-off", "category": "Political/Rumor"},
        {"date": "2023-12-10", "title": "Presidential Inauguration of Javier Milei", "category": "Official Measure"},
        {"date": "2023-12-13", "title": "Caputo Announces 54% Devaluation", "category": "Official Measure"},
        {"date": "2023-12-20", "title": "Mega DNU 70/2023 Deregulation Announced", "category": "Official Measure"},
        {"date": "2024-01-24", "title": "First General Strike (CGT)", "category": "Protest/Strike"},
        {"date": "2024-02-06", "title": "First Ley Ómnibus debate collapses", "category": "Political/Rumor"},
        {"date": "2024-04-23", "title": "Massive Public University March", "category": "Protest/Strike"},
        {"date": "2024-05-14", "title": "Inflation officially drops to single digits", "category": "Official Measure"},
        {"date": "2024-06-13", "title": "Ley Bases approved in Senate amid protests", "category": "Official Measure"},
        {"date": "2024-06-28", "title": "Ley Bases definitively approved in Deputies", "category": "Official Measure"},
        {"date": "2024-07-13", "title": "Phase 2 of Economic Plan announced", "category": "Official Measure"},
        {"date": "2024-08-05", "title": "Global Market Sell-off (Black Monday)", "category": "Market/External"},
        {"date": "2024-10-02", "title": "Second Massive University March", "category": "Protest/Strike"},
        {"date": "2024-11-13", "title": "Argentine Country Risk drops below 800 pts", "category": "Market/External"},
        {"date": "2025-01-20", "title": "Inauguration of US President Trump", "category": "Market/External"},
        {"date": "2025-03-01", "title": "Opening of Regular Congressional Sessions", "category": "Official Measure"}
    ]
    
    # Interactivity
    ticker_dropdown = mo.ui.dropdown(
        options=tickers,
        value="^MERV" if "^MERV" in tickers else tickers[0],
        label="Select Asset Strategy: "
    )
    theme_switch = mo.ui.switch(label="Dark Mode", value=False)
    trend_switch = mo.ui.switch(label="Show Denoised Trend (Savitzky-Golay DSP)", value=True)
    
    event_multiselect = mo.ui.multiselect(
        options={ev["title"]: ev for ev in EVENT_CATALOG},
        value=[ev["title"] for ev in EVENT_CATALOG],
        label="Overlay Events Filter:"
    )
    
    return EVENT_CATALOG, event_multiselect, theme_switch, ticker_dropdown, trend_switch

@app.cell
def _(EVENT_CATALOG, datetime, df, event_multiselect, pl, savgol_filter, ticker_dropdown):
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

    # Digital Signal Processing: Savitzky-Golay Filter for low-pass denoising
    # Only calculate if the dataset is large enough for the window
    window_len = 31
    if len(df_calc) > window_len:
        arr = df_calc["Close"].to_numpy()
        smoothed = savgol_filter(arr, window_length=window_len, polyorder=3)
        df_calc = df_calc.with_columns(pl.Series("Smoothed_Trend", smoothed))
    else:
        df_calc = df_calc.with_columns(pl.col("Close").alias("Smoothed_Trend"))

    # Fuzzy Matching (+/- 4 days)
    titles = []
    cats = []
    
    # Convert dates to raw date objects for easy subtraction
    dates_list = df_calc["Date"].to_list()
    active_events = event_multiselect.value # list of event dicts
    
    for _d in dates_list:
        _title, _cat = "Unknown Anomaly Event", "Unknown"
        # Extract date natively
        if hasattr(_d, 'date'): _d = _d.date()
        elif isinstance(_d, datetime.datetime): _d = _d.date()
        
        for _ev in active_events:
            _ev_date = datetime.datetime.strptime(_ev["date"], "%Y-%m-%d").date()
            if abs((_d - _ev_date).days) <= 4:
                _title = _ev["title"]
                _cat = _ev["category"]
                break
        
        titles.append(_title)
        cats.append(_cat)

    df_calc = df_calc.with_columns([
        pl.Series("Headline", titles),
        pl.Series("Category", cats)
    ])

    return df_calc, selected_ticker

@app.cell
def _(df_calc, df_ccl, go, make_subplots, pl, selected_ticker, theme_switch, trend_switch):
    # Two Subplots: 1 for Ticker/Anomalies, 1 for Dólar CCL & Brecha with secondary Y axis
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
        subplot_titles=(f"Price and Volatility Anomalies: {selected_ticker}", "Dólar CCL vs Official & Brecha (%)"),
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
    )

    # --- TOP CHART: TICKER PRICE ---
    fig.add_trace(go.Scatter(
        x=df_calc["Date"], y=df_calc["Close"], mode='lines', name='Raw Close Price', line=dict(color='rgba(31, 119, 180, 0.5)', width=1)
    ), row=1, col=1)

    # Add Denoised Trend if active
    if trend_switch.value and "Smoothed_Trend" in df_calc.columns:
        fig.add_trace(go.Scatter(
            x=df_calc["Date"], y=df_calc["Smoothed_Trend"], mode='lines', name='Denoised Trend (Savitzky-Golay)',
            line=dict(color='magenta', width=3)
        ), row=1, col=1)

    # Anomalies
    anomalies = df_calc.filter(pl.col("Is_Anomaly") == True)
    
    # Plot positive anomalies strictly GREEN
    anomalies_pos = anomalies.filter(pl.col("Return") > 0)
    if len(anomalies_pos) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies_pos["Date"], y=anomalies_pos["Close"], mode='markers', name='Positive Price Anomaly',
            marker=dict(color='green', size=12, symbol='triangle-up', line=dict(width=1, color='darkgreen')),
            hovertemplate="Date: %{x}<br>Price: %{y:.2f}<extra></extra>"
        ), row=1, col=1)
        
    # Plot negative anomalies strictly RED
    anomalies_neg = anomalies.filter(pl.col("Return") < 0)
    if len(anomalies_neg) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies_neg["Date"], y=anomalies_neg["Close"], mode='markers', name='Negative Price Anomaly',
            marker=dict(color='red', size=12, symbol='triangle-down', line=dict(width=1, color='darkred')),
            hovertemplate="Date: %{x}<br>Price: %{y:.2f}<extra></extra>"
        ), row=1, col=1)

    # --- FUZZY MATCHED EVENTS ---
    # completely distinct marker and vertical dashed line
    matched_events = df_calc.filter(pl.col("Headline") != "Unknown Anomaly Event")
    if len(matched_events) > 0:
        fig.add_trace(go.Scatter(
            x=matched_events["Date"], y=matched_events["Close"], mode='markers', name='Historical Event Map',
            marker=dict(color='yellow', size=16, symbol='circle-open', line=dict(width=3, color='orange')),
            customdata=matched_events["Headline"], hovertemplate="Date: %{x}<br>Event Found: %{customdata}<extra></extra>"
        ), row=1, col=1)
        
        for _d in matched_events["Date"].to_list():
            fig.add_vline(x=_d, line_dash="dash", line_color="rgba(255, 255, 0, 0.4)", row=1, col=1)

    # --- BOTTOM CHART: DÓLAR CCL & BRECHA ---
    fig.add_trace(go.Scatter(
        x=df_ccl["Date"], y=df_ccl["CCL_Price"], mode='lines', name='Dólar CCL', line=dict(color='orange')
    ), row=2, col=1, secondary_y=False)
    
    fig.add_trace(go.Scatter(
        x=df_ccl["Date"], y=df_ccl["ARS_X_Close"], mode='lines', name='Official USD', line=dict(color='green')
    ), row=2, col=1, secondary_y=False)
    
    # Plot Brecha on Secondary Y as an area
    fig.add_trace(go.Scatter(
        x=df_ccl["Date"], y=df_ccl["Brecha_Pct"], mode='lines', 
        name='Brecha (%)', fill='tozeroy', line=dict(color='rgba(128, 128, 128, 0.3)'),
        marker=dict(opacity=0)
    ), row=2, col=1, secondary_y=True)

    fig.update_layout(
        template="plotly_dark" if theme_switch.value else "plotly_white",
        hovermode="x unified",
        height=800
    )
    
    return anomalies, fig, matched_events

@app.cell
def _(anomalies, event_multiselect, fig, matched_events, mo, theme_switch, ticker_dropdown, trend_switch):
    # UI Layout
    mo.vstack([
        mo.md("# Argentine Macro & Volatility Dashboard 🇦🇷"),
        mo.md("Analyze structural market shifts, implicit FX rates (CCL), and historical anomalies using robust DSP filtering."),
        mo.hstack([ticker_dropdown, theme_switch, trend_switch], align="center", gap=2),
        mo.md("#### Contextual Event Filters"),
        event_multiselect,
        mo.ui.plotly(fig),
        mo.md("### Flagged Anomaly Events Log"),
        mo.ui.table(
            matched_events.select(["Date", "Close", "Return", "Headline", "Category"]),
            selection=None
        )
    ])
    return

if __name__ == "__main__":
    app.run()
