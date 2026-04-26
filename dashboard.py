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
    
    # Import modular logic
    from src.config import EVENT_CATALOG, DSP_WINDOW_LENGTH
    from src.processing import (
        calculate_snr, 
        process_market_indicators, 
        match_historical_events, 
        calculate_ccl_indicators
    )

    return (
        EVENT_CATALOG,
        DSP_WINDOW_LENGTH,
        calculate_ccl_indicators,
        calculate_snr,
        duckdb,
        go,
        make_subplots,
        match_historical_events,
        mo,
        pl,
        process_market_indicators,
    )


@app.cell
def _(calculate_ccl_indicators, calculate_snr, duckdb, pl):
    # Data Connection
    con = duckdb.connect("merval_data.db", read_only=True)
    df = con.execute("SELECT * FROM merval_prices").pl()

    # Available tickers (excluding helper tickers for CCL)
    tickers = [t for t in df["Ticker"].unique().to_list() if t != "GGAL.BA" and t != "ARS=X"]

    # --- CCL & Brecha ---
    df_ccl = calculate_ccl_indicators(df)

    # --- Market SNR Analysis ---
    snrs = {}
    for t_name in ["^MERV", "YPF", "GGAL"]:
        s_price = df.filter(pl.col("Ticker") == t_name)["Close"].to_numpy()
        snrs[t_name] = calculate_snr(s_price)
    snrs["CCL"] = calculate_snr(df_ccl["CCL_Price"].to_numpy())
    
    snr_table = pl.DataFrame({
        "Asset": list(snrs.keys()),
        "SNR Ratio": [round(v, 2) for v in snrs.values()]
    }).sort("SNR Ratio")

    return df, df_ccl, snr_table, tickers


@app.cell
def _(EVENT_CATALOG, mo, tickers):
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

    return event_multiselect, theme_switch, ticker_dropdown, trend_switch


@app.cell
def _(
    DSP_WINDOW_LENGTH,
    df,
    event_multiselect,
    match_historical_events,
    pl,
    process_market_indicators,
    ticker_dropdown,
):
    selected_ticker = ticker_dropdown.value

    # 1. Filter and process basic indicators (Returns, Vol, DSP)
    df_filtered = df.filter(pl.col("Ticker") == selected_ticker)
    df_calc = process_market_indicators(df_filtered, window_len=DSP_WINDOW_LENGTH)

    # 2. Optimized Event Matching (Join_asof)
    active_events = event_multiselect.value  # list of event dicts
    df_calc = match_historical_events(df_calc, active_events)

    return df_calc, selected_ticker


@app.cell
def _(
    df_calc,
    df_ccl,
    go,
    make_subplots,
    pl,
    selected_ticker,
    theme_switch,
    trend_switch,
):
    # Two Subplots: 1 for Ticker/Anomalies, 1 for Dólar CCL & Brecha
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
        x=df_calc["Date"], y=df_calc["Close"], mode='lines', name='Raw Close Price', 
        line=dict(color='rgba(31, 119, 180, 0.5)', width=1)
    ), row=1, col=1)

    if trend_switch.value and "Smoothed_Trend" in df_calc.columns:
        fig.add_trace(go.Scatter(
            x=df_calc["Date"], y=df_calc["Smoothed_Trend"], mode='lines', name='Denoised Trend (DSP)',
            line=dict(color='magenta', width=3)
        ), row=1, col=1)

    # Anomalies
    anomalies = df_calc.filter(pl.col("Is_Anomaly") == True)
    
    for color, symbol, name, direction in [('green', 'triangle-up', 'Positive Anomaly', 1), 
                                          ('red', 'triangle-down', 'Negative Anomaly', -1)]:
        subset = anomalies.filter((pl.col("Return") * direction) > 0)
        if len(subset) > 0:
            fig.add_trace(go.Scatter(
                x=subset["Date"], y=subset["Close"], mode='markers', name=name,
                marker=dict(color=color, size=12, symbol=symbol, line=dict(width=1, color='black')),
                hovertemplate="Date: %{x}<br>Price: %{y:.2f}<extra></extra>"
            ), row=1, col=1)

    # --- HISTORICAL EVENTS ---
    matched_events = df_calc.filter(pl.col("Headline") != "Unknown Anomaly Event")
    if len(matched_events) > 0:
        fig.add_trace(go.Scatter(
            x=matched_events["Date"], y=matched_events["Close"], mode='markers', name='Event Map',
            marker=dict(color='gray', size=6, symbol='circle-open'),
            customdata=matched_events["Headline"], 
            hovertemplate="Date: %{x}<br>Event: %{customdata}<extra></extra>"
        ), row=1, col=1)

    # --- BOTTOM CHART: FX & BRECHA ---
    fig.add_trace(go.Scatter(
        x=df_ccl["Date"], y=df_ccl["CCL_Price"], mode='lines', name='Dólar CCL', line=dict(color='orange')
    ), row=2, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df_ccl["Date"], y=df_ccl["ARS_X_Close"], mode='lines', name='Official USD', line=dict(color='green')
    ), row=2, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df_ccl["Date"], y=df_ccl["Brecha_Pct"], mode='lines', 
        name='Brecha (%)', fill='tozeroy', line=dict(color='rgba(128, 128, 128, 0.3)')
    ), row=2, col=1, secondary_y=True)

    fig.update_layout(
        template="plotly_dark" if theme_switch.value else "plotly_white",
        hovermode="x unified",
        height=800,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig, matched_events


@app.cell
def _(
    event_multiselect,
    fig,
    matched_events,
    mo,
    snr_table,
    theme_switch,
    ticker_dropdown,
    trend_switch,
):
    mo.vstack([
        mo.md("# Argentine Macro & Volatility Dashboard 🇦🇷"),
        mo.md("Analyze structural market shifts and political noise using Modern Data Stack (Polars, DuckDB)."),
        mo.hstack([ticker_dropdown, theme_switch, trend_switch], align="center", gap=2),
        mo.md("#### Contextual Event Filters"),
        event_multiselect,
        mo.ui.plotly(fig),
        mo.md("### Argentina Noise Factor (Signal-to-Noise Ratio)"),
        mo.ui.table(snr_table, selection=None),
        mo.md("### Flagged Anomaly Events Log"),
        mo.ui.table(
            matched_events.select(["Date", "Close", "Return", "Headline", "Category"]),
            selection=None
        )
    ])
    return


if __name__ == "__main__":
    app.run()
