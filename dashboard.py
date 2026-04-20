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
    import datetime

    return datetime, duckdb, go, make_subplots, mo, pl

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
    
    event_multiselect = mo.ui.multiselect(
        options={ev["title"]: ev for ev in EVENT_CATALOG},
        value=[ev["title"] for ev in EVENT_CATALOG],
        label="Overlay Events Filter:"
    )
    
    return EVENT_CATALOG, event_multiselect, theme_switch, ticker_dropdown

@app.cell
def _(EVENT_CATALOG, datetime, df, event_multiselect, pl, ticker_dropdown):
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

    # Fuzzy Matching (+/- 4 days)
    titles = []
    cats = []
    
    # Convert dates to raw date objects for easy subtraction
    dates_list = df_calc["Date"].to_list()
    active_events = event_multiselect.value # list of event dicts
    
    for d in dates_list:
        title, cat = "Unknown Anomaly Event", "Unknown"
        # Extract date natively
        if hasattr(d, 'date'): d = d.date()
        elif isinstance(d, datetime.datetime): d = d.date()
        
        for ev in active_events:
            ev_date = datetime.datetime.strptime(ev["date"], "%Y-%m-%d").date()
            if abs((d - ev_date).days) <= 4:
                title = ev["title"]
                cat = ev["category"]
                break
        
        titles.append(title)
        cats.append(cat)

    df_calc = df_calc.with_columns([
        pl.Series("Headline", titles),
        pl.Series("Category", cats)
    ])

    return df_calc, selected_ticker

@app.cell
def _(df_calc, df_ccl, go, make_subplots, pl, selected_ticker, theme_switch):
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
        x=df_calc["Date"], y=df_calc["Close"], mode='lines', name='Close Price', line=dict(color='#1f77b4')
    ), row=1, col=1)

    # Sub-filter Anomalies
    anomalies = df_calc.filter(pl.col("Is_Anomaly") == True)
    
    category_colors = {
        "Official Measure": "purple",
        "Political/Rumor": "orange",
        "Market/External": "blue",
        "Protest/Strike": "brown",
        "Unknown": "gray"
    }
    
    # Plot positive anomalies
    anomalies_pos = anomalies.filter(pl.col("Return") > 0)
    for cat in anomalies_pos["Category"].unique():
        cat_df = anomalies_pos.filter(pl.col("Category") == cat)
        color = category_colors.get(cat, "gray")
        fig.add_trace(go.Scatter(
            x=cat_df["Date"], y=cat_df["Close"], mode='markers', name=f'Positive Anomaly ({cat})',
            marker=dict(color=color, size=14, symbol='triangle-up', line=dict(width=2, color='green')),
            customdata=cat_df["Headline"], hovertemplate="Date: %{x}<br>Price: %{y:.2f}<br>Event: %{customdata}<extra></extra>"
        ), row=1, col=1)
        
    # Plot negative anomalies
    anomalies_neg = anomalies.filter(pl.col("Return") < 0)
    for cat in anomalies_neg["Category"].unique():
        cat_df = anomalies_neg.filter(pl.col("Category") == cat)
        color = category_colors.get(cat, "gray")
        fig.add_trace(go.Scatter(
            x=cat_df["Date"], y=cat_df["Close"], mode='markers', name=f'Negative Anomaly ({cat})',
            marker=dict(color=color, size=14, symbol='triangle-down', line=dict(width=2, color='red')),
            customdata=cat_df["Headline"], hovertemplate="Date: %{x}<br>Price: %{y:.2f}<br>Event: %{customdata}<extra></extra>"
        ), row=1, col=1)

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
    
    return anomalies, fig

@app.cell
def _(anomalies, event_multiselect, fig, mo, theme_switch, ticker_dropdown):
    # UI Layout
    mo.vstack([
        mo.md("# Argentine Macro & Volatility Dashboard 🇦🇷"),
        mo.md("Analyze structural market shifts, implicit FX rates (CCL), and historical anomalies."),
        mo.hstack([ticker_dropdown, theme_switch], align="center", gap=2),
        mo.md("#### Contextual Event Filters"),
        event_multiselect,
        mo.ui.plotly(fig),
        mo.md("### Flagged Anomaly Events Log"),
        mo.ui.table(
            anomalies.select(["Date", "Close", "Return", "Headline", "Category"]),
            selection=None
        )
    ])
    return

if __name__ == "__main__":
    app.run()
