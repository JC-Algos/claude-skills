#!/bin/bash
# =============================================================================
# Forex Sentiment API - VPS Deployment Script
# =============================================================================
# This script automates the deployment of the Flask API on your VPS
# =============================================================================

set -e  # Exit on error

echo "================================================================"
echo "  🚀 Forex Sentiment API - VPS Deployment"
echo "================================================================"
echo ""

# Configuration
INSTALL_DIR="/root/forex-sentiment"
DATA_DIR="$INSTALL_DIR/data"
SERVICE_NAME="forex-api"
PYTHON_FILE="forex_sentiment_api.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Step 1: Check if running as root
# =============================================================================
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo bash deploy-forex-api.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running as root${NC}"

# =============================================================================
# Step 2: Create directories
# =============================================================================
echo ""
echo "📁 Creating directories..."

mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"

echo -e "${GREEN}✓ Directories created${NC}"
echo "   - Install dir: $INSTALL_DIR"
echo "   - Data dir: $DATA_DIR"

# =============================================================================
# Step 3: Check if Python file exists
# =============================================================================
echo ""
echo "🔍 Checking for Python file..."

if [ ! -f "$INSTALL_DIR/$PYTHON_FILE" ]; then
    echo -e "${YELLOW}⚠️  Python file not found at: $INSTALL_DIR/$PYTHON_FILE${NC}"
    echo ""
    echo "Please copy forex_sentiment_api.py to $INSTALL_DIR first:"
    echo ""
    echo "  From local machine:"
    echo "  scp forex_sentiment_api.py root@YOUR_VPS_IP:$INSTALL_DIR/"
    echo ""
    echo "  Or manually upload the file"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Python file found${NC}"

# =============================================================================
# Step 4: Update file paths in Python file
# =============================================================================
echo ""
echo "📝 Updating file paths in Python script..."

# Backup original
cp "$INSTALL_DIR/$PYTHON_FILE" "$INSTALL_DIR/${PYTHON_FILE}.backup"

# Replace Windows path with Linux path
sed -i 's|DATA_FILE = r"C:\\\\B_Drive\\\\Market Sentiment Analysis\\\\forex_sentiment_detailed.json"|DATA_FILE = "/root/forex-sentiment/data/forex_sentiment_detailed.json"|g' "$INSTALL_DIR/$PYTHON_FILE"

echo -e "${GREEN}✓ File paths updated${NC}"
echo "   - Backup saved: ${PYTHON_FILE}.backup"

# =============================================================================
# Step 5: Install system dependencies
# =============================================================================
echo ""
echo "📦 Installing system dependencies..."

apt-get update -qq
apt-get install -y -qq python3 python3-pip curl wget chromium-browser chromium-chromedriver > /dev/null 2>&1

echo -e "${GREEN}✓ System dependencies installed${NC}"

# =============================================================================
# Step 6: Install Python packages
# =============================================================================
echo ""
echo "🐍 Installing Python packages (this may take a few minutes)..."

pip3 install --quiet flask pandas requests feedparser beautifulsoup4 selenium webdriver-manager undetected-chromedriver torch transformers numpy

echo -e "${GREEN}✓ Python packages installed${NC}"

# =============================================================================
# Step 7: Create systemd service
# =============================================================================
echo ""
echo "⚙️  Creating systemd service..."

cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Forex Sentiment Analysis API (Flask)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 $INSTALL_DIR/$PYTHON_FILE
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd service created${NC}"

# =============================================================================
# Step 8: Enable and start service
# =============================================================================
echo ""
echo "🚀 Starting service..."

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl start ${SERVICE_NAME}.service

# Wait a bit for service to start
sleep 3

# Check if service is running
if systemctl is-active --quiet ${SERVICE_NAME}.service; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo ""
    echo "Check logs with: sudo journalctl -u ${SERVICE_NAME}.service -n 50"
    exit 1
fi

# =============================================================================
# Step 9: Test API
# =============================================================================
echo ""
echo "🧪 Testing API..."

sleep 5  # Wait for FinBERT model to load

TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/forex-analysis-realtime?pair=EURUSD 2>/dev/null || echo "000")

if [ "$TEST_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API is responding (HTTP 200)${NC}"
else
    echo -e "${YELLOW}⚠️  API returned HTTP $TEST_RESPONSE${NC}"
    echo "   This might be normal if FinBERT model is still loading"
    echo "   Check logs: sudo journalctl -u ${SERVICE_NAME}.service -f"
fi

# =============================================================================
# Done!
# =============================================================================
echo ""
echo "================================================================"
echo -e "  ${GREEN}🎉 Deployment Complete!${NC}"
echo "================================================================"
echo ""
echo "Service Status:"
systemctl status ${SERVICE_NAME}.service --no-pager | head -n 10
echo ""
echo "📊 Useful Commands:"
echo "   Check status:  sudo systemctl status ${SERVICE_NAME}.service"
echo "   View logs:     sudo journalctl -u ${SERVICE_NAME}.service -f"
echo "   Restart:       sudo systemctl restart ${SERVICE_NAME}.service"
echo "   Stop:          sudo systemctl stop ${SERVICE_NAME}.service"
echo ""
echo "🧪 Test API:"
echo "   curl 'http://localhost:5002/forex-analysis-realtime?pair=EURUSD'"
echo ""
echo "📝 Next Steps:"
echo "   1. Update your n8n workflow to use Schedule Trigger"
echo "   2. Hardcode currency pair in workflow"
echo "   3. Update HTTP Request URLs to http://localhost:5002"
echo "   4. Test the workflow manually in n8n"
echo ""
echo "📖 Full guide: VPS-DEPLOYMENT-GUIDE.md"
echo ""
