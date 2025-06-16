#!/bin/bash
# Binance Price CLI Installer - Updated for Externally Managed Environments
# Usage: ./install.sh

# Configuration
SCRIPT_NAME="binance_price_cli.py"
VENV_DIR="/opt/binance_cli_venv"
INSTALL_DIR="/usr/local/bin"
BIN_NAMES=("binance" "bn")  # Supported command names

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run this script as root (sudo)."
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    echo "Install Python with: sudo apt install python3 python3-venv"
    exit 1
fi

# Create virtual environment
echo "Creating Python virtual environment in $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install Python dependencies
echo "Installing required Python packages in virtual environment..."
pip install python-binance || {
    echo "Failed to install python-binance."
    exit 1
}
deactivate

# Create script content
cat > /tmp/$SCRIPT_NAME << 'EOL'
#!/usr/bin/env python3
import sys
import os
from binance import Client

def get_current_price(symbol):
    # Read API keys from environment variables
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    if not api_key or not api_secret:
        print("Error: API keys not found. Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")
        sys.exit(1)

    # Use testnet by default (safe for testing)
    client = Client(api_key, api_secret, testnet=True)
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def main():
    if len(sys.argv) != 3 or sys.argv[1] != 'price':
        print(f"Usage: {sys.argv[0]} price <SYMBOL>")
        print(f"Example: {sys.argv[0]} price BTCUSDT")
        sys.exit(1)

    symbol = sys.argv[2].upper()

    try:
        price = get_current_price(symbol)
        print(f"{symbol}: {price}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOL

# Deploy script with virtual environment wrapper
echo "Installing script to $INSTALL_DIR..."
cat > $INSTALL_DIR/$SCRIPT_NAME << 'EOL'
#!/bin/bash
# Wrapper script for Python virtual environment
source /opt/binance_cli_venv/bin/activate
exec /opt/binance_cli_venv/bin/python /opt/binance_cli_venv/bin/binance_price_cli.py "$@"
EOL

# Install the actual Python script
install -m 755 /tmp/$SCRIPT_NAME $VENV_DIR/bin/$SCRIPT_NAME

# Make wrapper executable
chmod 755 $INSTALL_DIR/$SCRIPT_NAME

# Create symlinks
for bin_name in "${BIN_NAMES[@]}"; do
    ln -sf $INSTALL_DIR/$SCRIPT_NAME $INSTALL_DIR/$bin_name
    echo "Created command: $bin_name"
done

# Cleanup
rm /tmp/$SCRIPT_NAME

# Final instructions
echo -e "\nSuccessfully installed Binance Price CLI!"
echo -e "\nAdd your API keys to environment variables:"
echo "  export BINANCE_API_KEY='5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'"
echo "  export BINANCE_API_SECRET='DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'"
echo -e "\nAdd these lines to your ~/.bashrc or ~/.zshrc to make them permanent."
echo -e "\nUsage examples:"
echo "  binance price BTCUSDT"
echo "  bn price ETHUSDT"