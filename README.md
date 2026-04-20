# Argentine Fintech Screener 🇦🇷

Hey there! Thanks for checking out my project. I'm a junior developer trying to figure out how to process financial data and build interactive dashboards. 

### Why the Argentine Market?
When learning Time Series analysis and Anomaly Detection, you want data that actually moves. I chose the Argentine market (the MERVAL index, plus ADRs and FX rates) because its wild volatility, high inflation, and frequent political shocks make it the absolute best playground to learn from. Instead of looking at boring, steady assets, looking at the Argentine market during the 2023 elections shows exactly what a huge market shift looks like in real time. 

### The 2026 Tech Stack
I wanted to push myself to learn the "2026 Modern Data Stack." That meant dropping the usual Pandas and Jupyter notebooks setups. Instead, I built this using:
- **Polars**: for crazy fast data cleaning and handling the missing days that happen in emerging market data.
- **DuckDB**: storing the clean data locally without dealing with a massive SQL server setup.
- **Marimo**: to build an interactive UI that updates instantly when you change inputs (plus, it acts just like a notebook but feels like a real web app!).

### How to use this project

Since the database files aren't tracked in version control, you'll need to fetch the data yourself. It's super easy:

**1. Copy the code and set up the environment**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. Download the data**
This script pulls the last 3 years of daily prices and saves them to a local DuckDB file.
```bash
python fetch_data.py
```

**3. Open the dashboard**
Run the Marimo server to see the interactive charts and the anomalies we flagged!
```bash
python -m marimo edit dashboard.py
```
