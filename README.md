# Argentine Fintech Screener 🇦🇷

Hey there! Thanks for visiting my portfolio project. I'm a junior developer, and I built this to practice processing real-world financial data and building interactive data apps from scratch. 

### Why the Argentine Market?
When studying Time Series analysis and Anomaly Detection, you need data that actually moves. I chose the Argentine market (the MERVAL index, local ADRs, and the FX rate) because its extreme volatility, high inflation, and sudden political shocks make it the absolute best playground to learn on. Instead of looking at a flat chart, tracking the Argentine market during the 2023 elections shows you exactly what a massive economic swing looks like in the data.

### The 2026 Tech Stack
I wanted to push beyond the basics and learn the modern data tools that teams use *today*. I ditched the standard Pandas and Jupyter setup and built this dashboard using:
- **Polars**: for super fast data pipelines and cleaning up the missing days that naturally happen in emerging market feeds.
- **DuckDB**: for querying the data locally without managing a bulky SQL server.
- **Marimo**: to build an interactive, reactive UI that updates instantly (it writes like a notebook but feels like a real frontend!).

### Getting Started

Because the database files are skipped in version control, you'll just need to pull the data yourself. It's super easy:

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
Run the Marimo server to see the interactive charts and the anomalies I mapped out.
```bash
python -m marimo edit dashboard.py
```
