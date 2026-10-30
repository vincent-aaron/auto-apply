#!/usr/bin/env bash
# =============================================================================
# deploy-oci.sh — One-command deploy of the Job Application Automation
# Assistant to an Oracle Cloud Always-Free VM (AMD/ARM).
#
# Run this ON the VM (after SSH-ing in as `opc`):
#   curl -fsSL https://raw.githubusercontent.com/<YOUR_GH_USER>/<REPO>/main/deploy-oci.sh | bash
# or copy it locally and run:  bash deploy-oci.sh
#
# Free-tier prerequisites on the VM:
#   - 2× vCPU, 1 GB RAM (AMD) or 4× vCPU, 24 GB RAM (ARM) — both are Always Free
#   - Docker is installed and started by this script if missing
#   - A security-list rule allowing TCP 8080 inbound (script prints a reminder)
# =============================================================================
set -euo pipefail

APP_NAME="autoapply-assistant"
APP_PORT=8080
IMAGE="ghcr.io/${GITHUB_REPO:-autoapply-assistant/local}:${TAG:-latest}"

echo "==> Deploying $APP_NAME on $(hostname)"

# --- 1. Install Docker if not present (Oracle Linux / Ubuntu / Debian) --------
if ! command -v docker &>/dev/null; then
    echo "==> Docker not found — installing..."
    if command -v dnf &>/dev/null; then
        sudo dnf -y update && sudo dnf -y install docker
    elif command -v apt-get &>/dev/null; then
        sudo apt-get update && sudo apt-get -y install docker.io
    elif command -v yum &>/dev/null; then
        sudo yum -y update && sudo yum -y install docker
    else
        echo "ERROR: Unsupported OS. Install Docker manually, then re-run."
        exit 1
    fi
    sudo usermod -aG docker "$USER" 2>/dev/null || true
    sudo systemctl enable --now docker
    echo "    Docker installed. (If you get a permission error below, re-SSH — the
    usermod -aG docker change takes effect on next login.)"
fi

echo "==> Docker version: $(docker --version)"

# --- 2. Create a persistent data volume for the SQLite database ---------------
VOLUME_NAME="${APP_NAME}-data"
echo "==> Creating / reusing Docker volume: $VOLUME_NAME"
docker volume create "$VOLUME_NAME"

# --- 3. Pull the latest image (built by GitHub Actions → GHCR) ----------------
echo "==> Pulling image: $IMAGE"
# If using a public repo image, GHCR works without login for public packages.
# If your repo is private, run:  echo \$GHCR_TOKEN | docker login ghcr.io -u \$USER --password-stdin
docker pull "$IMAGE" || {
    echo "ERROR: Could not pull $IMAGE."
    echo "       Is GitHub Actions workflow (oci-deploy.yml) configured yet?"
    echo "       Alternatively, build locally:  docker build -t $IMAGE ."
    exit 1
}

# --- 4. Stop + remove any previous container ----------------------------------
echo "==> Stopping / removing previous container (if any)..."
docker rm -f "$APP_NAME" 2>/dev/null || true

# --- 5. Run the container with persistent storage + .env passthrough ----------
# The container's /app/data directory persists the SQLite DB.
# Environment variables are read from the host .env via --env-file.
echo "==> Starting container on host port $APP_PORT..."
docker run -d \
    --name "$APP_NAME" \
    --restart unless-stopped \
    -p "$APP_PORT:$APP_PORT" \
    -v "$VOLUME_NAME:/app/data" \
    --env-file "${ENV_FILE:-/app/.env}" \
    "$IMAGE"

# --- 6. Print access instructions ---------------------------------------------
echo ""
echo "==> ✅ $APP_NAME is live at:  http://$(hostname -I | awk '{print $1}'):${APP_PORT}"
echo "    Health check:  curl http://localhost:${APP_PORT}/health"
echo "    Tail logs:     docker logs -f $APP_NAME"
echo ""
echo "*** ORACLE CLOUD SECURITY-LIST REMINDER ***"
echo "If you cannot reach the app from outside, add an Ingress Rule in the OCI"
echo "Console → Networking → Virtual Cloud Network → Security Lists →"
echo "<your VCN's Security List> → Add Ingress Rule:"
echo "    Source: 0.0.0.0/0  |  Protocol: TCP  |  Port: ${APP_PORT}"
echo "============================================="
