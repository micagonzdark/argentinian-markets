# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Polars/DuckDB/Scipy if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the data directory (if we wanted to mount it, but here we just ensure it exists)
# Run the data fetcher during build to have initial data (optional, or run on startup)
# RUN python fetch_data.py

# Expose the port Marimo will run on
EXPOSE 8080

# Run marimo dashboard in 'run' mode (read-only app)
CMD ["marimo", "run", "dashboard.py", "--host", "0.0.0.0", "--port", "8080"]
