#!/usr/bin/env bash
# Install and enable the Apex SAPIENT Middleware systemd service.
# Run as root: sudo bash install_service.sh [install-dir]
set -euo pipefail

INSTALL_DIR="${1:-/opt/apex}"
SERVICE_NAME="apex"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Create dedicated system user if it doesn't exist
if ! id "${SERVICE_NAME}" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "${SERVICE_NAME}"
    echo "Created system user: ${SERVICE_NAME}"
fi

# Create install directory and copy files
mkdir -p "${INSTALL_DIR}"
cp -r "${REPO_DIR}/sapient_apex_server" \
      "${REPO_DIR}/sapient_apex_api" \
      "${REPO_DIR}/sapient_msg" \
      "${INSTALL_DIR}/"
cp "${REPO_DIR}/deploy/apex_config.json" "${INSTALL_DIR}/"

# Create virtual environment with Python 3.10 and install dependencies
python3.10 -m venv "${INSTALL_DIR}/venv"
"${INSTALL_DIR}/venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/venv/bin/pip" install \
    protobuf \
    trio \
    ulid-py \
    fastapi \
    uvicorn \
    httpx \
    elasticsearch \
    sqlalchemy

# Create data directory
mkdir -p "${INSTALL_DIR}/data"

# Fix ownership
chown -R "${SERVICE_NAME}:${SERVICE_NAME}" "${INSTALL_DIR}"

# Install the systemd unit (update ExecStart path)
sed "s|/opt/apex|${INSTALL_DIR}|g" "${REPO_DIR}/deploy/apex.service" > "${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl start "${SERVICE_NAME}"

echo ""
echo "Service installed. Useful commands:"
echo "  systemctl status ${SERVICE_NAME}"
echo "  journalctl -u ${SERVICE_NAME} -f"
echo "  systemctl restart ${SERVICE_NAME}"
