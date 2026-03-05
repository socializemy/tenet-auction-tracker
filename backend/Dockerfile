FROM python:3.11-slim

# Install system dependencies needed for Playwright, Chrome, and Xvfb
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
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
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

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
# We configure our scrapers to check this var to know where the native Chrome binary lives on Linux
ENV CHROME_BIN_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99

EXPOSE 8000

# Use xvfb-run to provide a virtual display for headed Chrome execution
CMD ["xvfb-run", "--server-args=-screen 0 1024x768x24", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
