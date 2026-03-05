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

# Add Google Chrome's official PPA and install Chrome Stable
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
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
# We configure our scrapers to check this var to know where the native Chrome binary lives on Linux
ENV CHROME_BIN_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99

EXPOSE 8000

# Use xvfb-run to provide a virtual display for headed Chrome execution
CMD ["xvfb-run", "--server-args=-screen 0 1024x768x24", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
