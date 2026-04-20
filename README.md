# Argentine Fintech Screener 🇦🇷

Hi! Thanks for stopping by my portfolio. I'm currently a student learning data engineering, and I built this project to practice processing real financial data and building interactive apps from scratch.

### Why the Argentine Market?
When learning Time Series analysis and Anomaly Detection, you need data that actually moves. I chose the Argentine market (the MERVAL index, local ADRs, and the FX rate) because its extreme volatility, high inflation, and sudden political shocks make it a great place to learn. Instead of looking at a flat chart, tracking the Argentine market during the 2023 elections shows you exactly what a massive economic swing looks like in the data.

I also implemented Digital Signal Processing (a Savitzky-Golay low-pass filter) to calculate a Signal-to-Noise Ratio (SNR). This allows the tool to mathematically distinguish whether an asset is moving due to underlying Market Trends (the core signal) or purely due to short-term Political Noise and panic.

### Intentionally Upskilling
While I already have a strong mastery of traditional data engineering tools like Pandas, Jupyter, and SQLite, I deliberately chose the 2026 Modern Data Stack (Polars, DuckDB, Marimo) for this project to push my boundaries and learn the latest industry standards.

Specifically, I used:
- **Polars**: for super fast data pipelines and cleaning up the missing days that naturally happen in emerging market feeds.
- **DuckDB**: for querying the data locally without setting up a heavy database server.
- **Marimo**: to build an interactive UI that updates instantly based on inputs (it writes like a notebook but behaves like a web app!).

### Getting Started

Because the database files are skipped in version control, you'll just need to pull the data yourself. Here is how:

**1. Create the environment:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. Fetch 3 years of market data:**
```bash
python fetch_data.py
```

**3. Boot the dashboard!**
Run the Marimo server to explore the charts and the historical events I mapped out.
```bash
python -m marimo edit dashboard.py
```
