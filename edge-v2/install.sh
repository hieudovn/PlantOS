#!/usr/bin/env bash
#
# PlantOS Edge Lite v2 — One-command installer
# Supports systemd-based Linux distributions (Ubuntu 22.04+, Debian 12+)
#
# Usage:
#   curl -fsSL https://install.plantos.io/edge-v2 | sudo bash
#   # or locally:
#   sudo ./install.sh
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---- Configuration ---------------------------------------------------------
INSTALL_DIR="/opt/plantos-edge-v2"
CONFIG_DIR="/etc/plantos-edge-v2"
DATA_DIR="${INSTALL_DIR}/data"
SERVICE_NAME="plantos-edge-v2"
REQUIRED_PYTHON="3.11"

# ---- Prerequisites ----------------------------------------------------------
log_info "Checking prerequisites..."

# Must be root
if [[ $EUID -ne 0 ]]; then
    log_error "This installer must be run as root (sudo)"
    exit 1
fi

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON=$(command -v python3)
elif command -v python &>/dev/null; then
    PYTHON=$(command -v python)
else
    log_error "Python 3.11+ is required. Install it with: apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $(echo "$PYTHON_VERSION < $REQUIRED_PYTHON" | bc -l) -eq 1 ]]; then
    log_error "Python $REQUIRED_PYTHON+ required, found $PYTHON_VERSION"
    exit 1
fi
log_info "Python $PYTHON_VERSION found at $PYTHON"

# Check git or source directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$SCRIPT_DIR/agent/main.py" ]]; then
    log_warn "Source files not found at $SCRIPT_DIR"
    log_info "Cloning repository..."
    apt-get install -y git
    TMP_DIR=$(mktemp -d)
    git clone --depth 1 --branch feature/edge-v2 https://github.com/PlantOS/plantos.git "$TMP_DIR"
    SCRIPT_DIR="$TMP_DIR/edge-v2"
fi

# ---- Create user -----------------------------------------------------------
if ! id -u plantos &>/dev/null; then
    log_info "Creating plantos user..."
    useradd --system --no-create-home --shell /usr/sbin/nologin plantos
fi

# ---- Create directories ----------------------------------------------------
log_info "Creating directories..."
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR"

# ---- Copy files ------------------------------------------------------------
log_info "Copying files..."
cp -r "$SCRIPT_DIR/agent" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/console" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/plantos-edge-v2.service" "/etc/systemd/system/"

# ---- Create config if not exists -------------------------------------------
if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
    log_info "Creating default config..."
    cat > "$CONFIG_DIR/config.yaml" << 'EOF'
# PlantOS Edge v2 — Configuration
# Edit this file to match your environment.
# Run `systemctl restart plantos-edge-v2` after changes.

edge_node_id: EDGEV2-PC-01
plant_id: EDGEV2-DEMO
center_url: http://localhost:8000
api_key: plantos-edge-key-2026
session_secret: CHANGE_ME_TO_A_RANDOM_SECRET

auth:
  # Set admin password via web UI after first start:
  # http://localhost:8011/login

buffer:
  path: /opt/plantos-edge-v2/data/edge_data.duckdb
  retention_days: 7

mqtt:
  host: localhost
  port: 1883
  topic_prefix: avenue/edgev2-demo

http:
  ingest_url: http://localhost:8000/api/v1/measurements/ingest

heartbeat:
  url: http://localhost:8000/api/v1/edge-nodes/heartbeat
  interval_seconds: 10

publish:
  interval_seconds: 10
  batch_size: 10

web:
  port: 8011
EOF
    log_warn "Edit $CONFIG_DIR/config.yaml with your settings"
    log_warn "  - Set session_secret to a random value"
    log_warn "  - Set center_url to your Center API URL"
fi

# ---- Create Python venv ----------------------------------------------------
log_info "Creating Python virtual environment..."
$PYTHON -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install --no-cache-dir -r "$INSTALL_DIR/requirements.txt" 2>&1 | tail -1
deactivate

# ---- Set permissions -------------------------------------------------------
log_info "Setting permissions..."
chown -R plantos:plantos "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR"
chmod 750 "$INSTALL_DIR" "$CONFIG_DIR"
chmod 640 "$CONFIG_DIR/config.yaml"
chmod 755 "$INSTALL_DIR/venv/bin/python"

# ---- Install & enable systemd service --------------------------------------
log_info "Installing systemd service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# ---- Verify ----------------------------------------------------------------
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log_info "✅ PlantOS Edge Lite v2 is running!"
    log_info "   Service: systemctl status $SERVICE_NAME"
    log_info "   Logs:    journalctl -u $SERVICE_NAME -f"
    log_info "   Console: http://$(hostname -I | awk '{print $1}'):8011"
    log_info ""
    log_info "Next steps:"
    log_info "   1. Open the Console URL in a browser"
    log_info "   2. Set admin password on first login"
    log_info "   3. Configure connectors via the web UI"
    log_info "   4. Verify heartbeat reaches Center"
else
    log_error "Service failed to start. Check: journalctl -u $SERVICE_NAME -n 50 --no-pager"
    exit 1
fi
