#!/bin/bash
# ============================================================
# deploy.sh — Spokane Auction Tracker → Hostinger VPS
# Usage: ./deploy/deploy.sh
# Run from the project root: spokane-auction-properties/
# ============================================================
set -e

# Load env vars
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

VPS_HOST="${VPS_HOST:-your-vps-ip}"
VPS_USER="${VPS_USER:-root}"
VPS_DEPLOY_PATH="${VPS_DEPLOY_PATH:-/var/www/spokane-auction}"
DOMAIN="${DOMAIN:-}"

echo "==> 🏗  Building frontend..."
cd frontend
npm install --silent
npm run build
cd ..

echo "==> 📦  Syncing files to VPS ${VPS_USER}@${VPS_HOST}:${VPS_DEPLOY_PATH}..."

# Create directory on VPS
ssh ${VPS_USER}@${VPS_HOST} "mkdir -p ${VPS_DEPLOY_PATH}/backend ${VPS_DEPLOY_PATH}/frontend"

# Sync backend
rsync -az --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' --exclude='*.db' \
  backend/ ${VPS_USER}@${VPS_HOST}:${VPS_DEPLOY_PATH}/backend/

# Sync built frontend
rsync -az frontend/dist/ ${VPS_USER}@${VPS_HOST}:${VPS_DEPLOY_PATH}/frontend/

# Sync deploy config files
rsync -az deploy/ ${VPS_USER}@${VPS_HOST}:${VPS_DEPLOY_PATH}/deploy/

# Sync .env (if it exists — don't commit this!)
if [ -f .env ]; then
  scp .env ${VPS_USER}@${VPS_HOST}:${VPS_DEPLOY_PATH}/backend/.env
fi

echo "==> 🐍  Installing Python dependencies on VPS..."
ssh ${VPS_USER}@${VPS_HOST} "
  cd ${VPS_DEPLOY_PATH}/backend
  python3 -m venv venv 2>/dev/null || true
  source venv/bin/activate
  pip install -q -r requirements.txt
  playwright install chromium --with-deps
  deactivate
"

echo "==> ⚙️   Configuring systemd service..."
ssh ${VPS_USER}@${VPS_HOST} "
  # Replace placeholder paths in service files
  sed -i 's|DEPLOY_PATH|${VPS_DEPLOY_PATH}|g' ${VPS_DEPLOY_PATH}/deploy/spokane-auction-api.service
  sed -i 's|DEPLOY_PATH|${VPS_DEPLOY_PATH}|g' ${VPS_DEPLOY_PATH}/deploy/spokane-auction-scheduler.service

  cp ${VPS_DEPLOY_PATH}/deploy/spokane-auction-api.service /etc/systemd/system/
  cp ${VPS_DEPLOY_PATH}/deploy/spokane-auction-scheduler.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable spokane-auction-api spokane-auction-scheduler
  systemctl restart spokane-auction-api spokane-auction-scheduler
"

echo "==> 🌐  Configuring Nginx..."
ssh ${VPS_USER}@${VPS_HOST} "
  # Update nginx config with correct paths and domain
  sed -i 's|DEPLOY_PATH|${VPS_DEPLOY_PATH}|g' ${VPS_DEPLOY_PATH}/deploy/nginx.conf
  if [ -n '${DOMAIN}' ]; then
    sed -i 's|server_name _;|server_name ${DOMAIN} www.${DOMAIN};|g' ${VPS_DEPLOY_PATH}/deploy/nginx.conf
  fi
  cp ${VPS_DEPLOY_PATH}/deploy/nginx.conf /etc/nginx/sites-available/spokane-auction
  ln -sf /etc/nginx/sites-available/spokane-auction /etc/nginx/sites-enabled/spokane-auction
  nginx -t && systemctl reload nginx
"

echo ""
echo "✅ Deployment complete!"
echo ""
if [ -n "$DOMAIN" ]; then
  echo "   🌍 App: http://${DOMAIN}"
  echo "   💡 For HTTPS: ssh ${VPS_USER}@${VPS_HOST} 'certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}'"
else
  echo "   🌍 App: http://${VPS_HOST}"
fi
echo "   📋 View logs: ssh ${VPS_USER}@${VPS_HOST} 'journalctl -u spokane-auction-api -f'"
echo ""
