#!/bin/bash
# Quick flash script for M5Stack Atom Echo
# Usage: ./flash.sh [device_name]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}WiFi Walkie-Talkie Flash Tool${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Optional: Set device name from command line argument
if [ ! -z "$1" ]; then
    echo -e "${YELLOW}Setting device name to: $1${NC}"
    # Update .env file with new device name
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^DEVICE_NAME=.*/DEVICE_NAME=$1/" .env
    else
        # Linux
        sed -i "s/^DEVICE_NAME=.*/DEVICE_NAME=$1/" .env
    fi
fi

# Step 1: Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file with your WiFi credentials${NC}"
    echo ""
    echo "Example:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Edit WiFi password"
    exit 1
fi

# Step 2: Check WiFi password is set
if grep -q "PUT_YOUR_PASSWORD_HERE" .env; then
    echo -e "${RED}Error: WiFi password not set!${NC}"
    echo -e "${YELLOW}Please edit .env file and set WIFI_PASSWORD_1${NC}"
    echo ""
    echo "  nano .env"
    exit 1
fi

# Step 3: Generate configuration
echo -e "${BLUE}Generating configuration...${NC}"
python3 configure.py || exit 1
echo ""

# Step 4: Build firmware
echo -e "${BLUE}Building firmware...${NC}"
pio run || exit 1
echo ""

# Step 5: Upload to device
echo -e "${BLUE}Uploading to M5Stack Atom Echo...${NC}"
echo -e "${YELLOW}Make sure device is connected via USB-C!${NC}"
sleep 2
pio run --target upload || exit 1
echo ""

# Success!
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ SUCCESS!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Device: ${BLUE}$(grep DEVICE_NAME .env | cut -d'=' -f2)${NC}"
echo -e "WiFi: ${BLUE}$(grep WIFI_SSID_1 .env | cut -d'=' -f2)${NC}"
echo ""
echo "To monitor the device:"
echo -e "  ${BLUE}pio device monitor${NC}"
echo ""
echo "To flash another device with different name:"
echo -e "  ${BLUE}./flash.sh Alice${NC}"
echo ""
