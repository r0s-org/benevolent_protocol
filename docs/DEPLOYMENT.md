# Deployment Guide - THE BENEVOLENT PROTOCOL

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running](#running)
5. [Systemd Service](#systemd-service)
6. [Docker Deployment](#docker-deployment)
7. [Security Considerations](#security-considerations)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10+ | 3.11+ |
| RAM | 512MB | 1GB |
| Disk | 100MB | 500MB |
| CPU | 1 core | 2+ cores |

### Supported Platforms

- **Linux** (carrier mode) - Ubuntu 20.04+, Debian 11+, Arch, Fedora
- **Windows** (active mode) - Windows 10/11
- **Android** (via ADB) - Android 8.0+

### Dependencies

```bash
# Python packages
pip install -r requirements.txt

# System packages (Linux)
sudo apt install python3-pip python3-venv
```

---

## Installation

### Option 1: From Source

```bash
# Clone repository
git clone https://github.com/r0s-org/benevolent_protocol.git
cd benevolent_protocol

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 2: From PyPI (Future)

```bash
pip install benevolent-protocol
```

### Option 3: Windows (PowerShell)

Run as Administrator in PowerShell:

```powershell
# Download and run installer
Invoke-WebRequest -Uri "https://r0s.org/benevolent-protocol-install.ps1" -OutFile "install.ps1"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

Or one-liner:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; Invoke-WebRequest -Uri "https://r0s.org/benevolent-protocol-install.ps1" -OutFile "install.ps1"; .\install.ps1
```

### Option 4: Docker

```bash
docker pull r0sorg/benevolent-protocol:latest
```

---

## Configuration

### Configuration File Location

The protocol looks for configuration in this order:

1. `--config /path/to/config.json` (command line)
2. `BENEVOLENT_PROTOCOL_CONFIG` environment variable
3. `/etc/benevolent_protocol/config.json`
4. `./config/config.json` (relative to working directory)

### Creating Configuration

```bash
# Copy example config
mkdir -p /etc/benevolent_protocol
cp config/config.json /etc/benevolent_protocol/

# Edit configuration
nano /etc/benevolent_protocol/config.json
```

### Key Configuration Options

#### Required Settings

```json
{
    "control_secret": "YOUR_SECURE_SECRET_HERE"
}
```

⚠️ **IMPORTANT**: Change `control_secret` to a secure random string!

```bash
# Generate a secure secret
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### Telemetry Settings

```json
{
    "telemetry_enabled": true,
    "telemetry_level": "standard",
    "telemetry_endpoint": "https://your-server.com/api/telemetry"
}
```

Telemetry levels:
- `minimal` - Only health status
- `standard` - Health + basic stats (default)
- `detailed` - Full diagnostic info

#### Resource Limits

```json
{
    "max_cpu_percent": 30,
    "max_memory_mb": 500,
    "gaming_mode_auto_detect": true
}
```

#### Propagation Settings

```json
{
    "propagation_enabled": false,
    "allowed_networks": ["192.168.0.0/16", "10.0.0.0/8"],
    "excluded_hosts": ["192.168.1.1", "192.168.1.100"]
}
```

⚠️ **WARNING**: Enable propagation only in controlled environments!

---

## Running

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run with default config
python -m src.core

# Run with specific config
python -m src.core --config /path/to/config.json

# Run with debug logging
LOG_LEVEL=DEBUG python -m src.core
```

### Production Mode

```bash
# Direct execution
benevolent-protocol --config /etc/benevolent_protocol/config.json

# Or via Python
python3 -m src.core.orchestrator --config /etc/benevolent_protocol/config.json
```

### Command Line Options

```
Usage: benevolent-protocol [OPTIONS]

Options:
  --config PATH         Path to configuration file
  --version            Show version and exit
  --help               Show this message and exit
```

---

## Systemd Service

### Create Service File

```bash
sudo nano /etc/systemd/system/benevolent-protocol.service
```

```ini
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
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

# Security
NoNewPrivileges=true
PrivateTmp=true

# Resource limits
LimitNOFILE=65536
CPUQuota=30%
MemoryMax=500M

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable at boot
sudo systemctl enable benevolent-protocol

# Start service
sudo systemctl start benevolent-protocol

# Check status
sudo systemctl status benevolent-protocol

# View logs
sudo journalctl -u benevolent-protocol -f
```

### Service Management

```bash
# Stop
sudo systemctl stop benevolent-protocol

# Restart
sudo systemctl restart benevolent-protocol

# Disable at boot
sudo systemctl disable benevolent-protocol
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 protocol
USER protocol

# Default configuration
ENV BENEVOLENT_PROTOCOL_CONFIG=/app/config/config.json

CMD ["python", "-m", "src.core.orchestrator"]
```

### Build and Run

```bash
# Build image
docker build -t benevolent-protocol .

# Run container
docker run -d \
    --name benevolent-protocol \
    --restart unless-stopped \
    -v /etc/benevolent_protocol:/app/config:ro \
    -v /var/log/benevolent_protocol:/var/log/benevolent_protocol \
    --cpus="0.5" \
    --memory="512m" \
    benevolent-protocol
```

### Docker Compose

```yaml
version: '3.8'

services:
  benevolent-protocol:
    build: .
    container_name: benevolent-protocol
    restart: unless-stopped
    volumes:
      - ./config:/app/config:ro
      - ./logs:/var/log/benevolent_protocol
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    environment:
      - LOG_LEVEL=INFO
```

```bash
docker-compose up -d
```

---

## Security Considerations

### 1. Change Default Secret

```bash
# NEVER use the default secret!
# Generate a new one:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. File Permissions

```bash
# Config file should be readable only by protocol user
sudo chmod 600 /etc/benevolent_protocol/config.json
sudo chown root:root /etc/benevolent_protocol/config.json
```

### 3. Network Security

- Command receiver binds to localhost by default
- Use firewall rules to restrict access
- Enable TLS for remote telemetry endpoints

### 4. Propagation Caution

⚠️ **WARNING**: Only enable propagation in controlled test environments!

```json
{
    "propagation_enabled": false  // Keep disabled in production!
}
```

### 5. Kill Switch Access

Ensure you have access to trigger kill switch:

```bash
# Soft stop (finish current operations)
sudo kill -SIGUSR1 $(pidof benevolent-protocol)

# Hard stop (immediate)
sudo systemctl stop benevolent-protocol
```

---

## Monitoring

### Health Check Endpoint

```bash
# Check protocol status
curl http://localhost:9527/status
```

### Log Monitoring

```bash
# Follow logs
tail -f /var/log/benevolent_protocol.log

# With journalctl
sudo journalctl -u benevolent-protocol -f
```

### Metrics

The protocol exposes metrics via telemetry:

```python
# Get current stats
{
    "version": "0.3.0-alpha",
    "uptime_seconds": 3600,
    "devices_encountered": 5,
    "optimizations_applied": 12,
    "threats_removed": 2,
    "errors_count": 0
}
```

### Prometheus Integration (Optional)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'benevolent-protocol'
    static_configs:
      - targets: ['localhost:9527']
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied

```bash
# Check file permissions
ls -la /etc/benevolent_protocol/config.json

# Fix permissions
sudo chmod 600 /etc/benevolent_protocol/config.json
```

#### 2. Module Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. High CPU Usage

Check if gaming mode is detecting correctly:

```bash
# View current mode in logs
grep "mode" /var/log/benevolent_protocol.log
```

#### 4. Kill Switch Triggered

```bash
# Check if kill switch was activated
ls -la /opt/benevolent_protocol/.stop
ls -la /opt/benevolent_protocol/.hard_stop

# Reset (if not nuclear)
rm /opt/benevolent_protocol/.stop
systemctl restart benevolent-protocol
```

### Debug Mode

```bash
# Run with maximum logging
LOG_LEVEL=DEBUG python -m src.core.orchestrator
```

### Getting Help

1. Check logs: `/var/log/benevolent_protocol.log`
2. Review configuration: `/etc/benevolent_protocol/config.json`
3. GitHub Issues: https://github.com/r0s-org/benevolent_protocol/issues
4. Discord: https://discord.com/invite/clawd

---

## Updates

### Manual Update

```bash
# Stop service
sudo systemctl stop benevolent-protocol

# Pull latest code
cd /opt/benevolent_protocol
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start service
sudo systemctl start benevolent-protocol
```

### Automatic Updates

The protocol includes an update receiver module that can apply updates automatically (when configured).

---

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop benevolent-protocol
sudo systemctl disable benevolent-protocol

# Remove service file
sudo rm /etc/systemd/system/benevolent-protocol.service
sudo systemctl daemon-reload

# Remove files
sudo rm -rf /opt/benevolent_protocol
sudo rm -rf /etc/benevolent_protocol

# Remove logs (optional)
sudo rm -rf /var/log/benevolent_protocol
```

---

## Next Steps

After deployment:

1. ✅ Verify protocol is running: `systemctl status benevolent-protocol`
2. ✅ Check logs for errors: `journalctl -u benevolent-protocol`
3. ✅ Test commands: `curl localhost:9527/status`
4. ✅ Configure telemetry endpoint (if using)
5. ✅ Set up monitoring and alerts

---

*Last Updated: 2026-02-28*
*Version: 0.3.0-alpha*
