FROM python:3.11-slim

# Install system dependencies needed for Playwright, Chrome, and Xvfb
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    xauth \
    libnss3 \
    libxss1 \
    libasound2 \
    libgbm-dev \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Download and install Google Chrome Stable via official .deb package (bypasses deprecated apt-key)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements into the container
COPY requirements.txt .

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dependencies (just in case they aren't covered by the chrome install)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy Python source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99

EXPOSE 8000

# Start Xvfb in the background explicitly, bypassing the broken xvfb-run wrapper, then start Uvicorn
CMD Xvfb :99 -screen 0 1024x768x24 & python migrate_db.py && uvicorn main:app --host 0.0.0.0 --port 8000
