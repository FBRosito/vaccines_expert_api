# ---- Base Image ----
# Official Python 3.9 slim image — compatible with the experta rule engine.
FROM python:3.9-slim

# ---- Metadata ----
LABEL maintainer="Anonymized for peer review"
LABEL description="Vaccination Expert System API — Flask + Experta."

# ---- Environment Variables ----
WORKDIR /app

# Prevents Python from writing .pyc files to disk.
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent directly to the terminal (useful for log streaming).
ENV PYTHONUNBUFFERED 1

# --- SYSTEM DEPENDENCIES ---
# Install netcat so the entrypoint script can probe the database port.
# Clean up apt cache to keep the image small.
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# ---- Install Dependencies ----
# Copy requirements first to leverage Docker layer caching.
# Dependencies are only reinstalled when this file changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Application Code ----
COPY . .

# Copy the entrypoint script into the container.
COPY entrypoint.sh .

# ---- Expose Port ----
EXPOSE 5000

# ---- Entrypoint ----
# The container always runs this script first.
ENTRYPOINT ["/app/entrypoint.sh"]

# ---- Run Command ----
# Passed as "$@" to entrypoint.sh after migrations complete.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
