# Deploying Tenet Auction Tracker via Docker (VPS)

This project has been fully port-configured for Docker-based deployment on any Linux Virtual Private Server (VPS).

## Prerequisites

1.  A Linux VPS (Ubuntu/Debian recommended) with **Docker Engine** and **Docker Compose** installed.
2.  (Optional) A domain name mapped to the VPS IP for standard HTTP access.

## Quick Start on VPS

1. Clone or clone-upload the repository directory to your VPS logic path.
2. Execute Docker Compose to orchestrate both the Python API and the Nginx React Frontend:
    ```bash
    docker compose up -d --build
    ```
3. The scraper application will now be live on Port 80. Connect via `http://YOUR_VPS_IP/`.

## Architecture

*   **`auction_backend`**: A headless FastAPI instance running on Python 3.11. It installs `Xvfb` and `google-chrome-stable` structurally inside to enable `playwright` to successfully scrape rigorous Cloudflare/Okta bot-firewalls under headless Linux emulation natively.
*   **`auction_frontend`**: Bakes the latest `Vite` React production bundle into an optimized `Nginx` alpine container. Crucially, the nginx server reverses proxy mapping for all `/api/` traffic internally into the `backend`, securing CORS out-of-the-box.

### Maintaining Persistent Data
Volume mappings are automatically tracked inside `docker-compose.yml`:
*   The master SQLite database instance lives at `./backend/auction_data.db`. It maps 1:1 onto the host so a container reset does not nuke standard tracking lists.
*   The manual payload dropzone at `./backend/data` is also mapped safely to allow direct CLI uploads.
