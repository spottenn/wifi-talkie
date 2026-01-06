#!/usr/bin/env python3
"""
WiFi Walkie-Talkie Configuration Script

Reads .env file and generates include/config_local.h for compilation.
Run this before building the firmware.

Usage:
    python configure.py
"""

import os
import sys
from pathlib import Path


def read_env_file(env_path=".env"):
    """Read .env file and return dictionary of values"""
    config = {}

    if not os.path.exists(env_path):
        print(f"❌ Error: {env_path} file not found!")
        print(f"📝 Please copy .env.example to .env and fill in your WiFi credentials")
        print(f"\n   cp .env.example .env")
        print(f"   nano .env  # or use your favorite editor\n")
        return None

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                config[key] = value

    return config


def escape_string(s):
    """Escape special characters for C string"""
    return s.replace('\\', '\\\\').replace('"', '\\"')


def generate_config_header(config, output_path="include/config_local.h"):
    """Generate config_local.h from configuration dictionary"""

    # Create include directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("// Auto-generated configuration file\n")
        f.write("// DO NOT EDIT MANUALLY - Edit .env and run configure.py\n")
        f.write("// This file is in .gitignore and will not be committed\n\n")
        f.write("#ifndef CONFIG_LOCAL_H\n")
        f.write("#define CONFIG_LOCAL_H\n\n")

        # WiFi Networks
        for i in range(1, 4):
            ssid_key = f"WIFI_SSID_{i}"
            password_key = f"WIFI_PASSWORD_{i}"

            ssid = config.get(ssid_key, "")
            password = config.get(password_key, "")

            if ssid and password:
                f.write(f'#define {ssid_key} "{escape_string(ssid)}"\n')
                f.write(f'#define {password_key} "{escape_string(password)}"\n')
                f.write("\n")

        # WebSocket Server - parse URL to extract host and port
        server = config.get("WEBSOCKET_SERVER", "")
        if server:
            f.write(f'#define WEBSOCKET_SERVER "{escape_string(server)}"\n')
            # Extract port from URL if present (e.g., ws://host:8280)
            import re
            port_match = re.search(r':(\d+)', server.replace('ws://', '').replace('wss://', ''))
            if port_match:
                port = port_match.group(1)
                f.write(f'#define WEBSOCKET_PORT {port}\n')

        # Device Name
        device_name = config.get("DEVICE_NAME", "")
        if device_name:
            f.write(f'#define DEVICE_NAME "{escape_string(device_name)}"\n')

        f.write("\n#endif // CONFIG_LOCAL_H\n")

    print(f"✅ Generated {output_path}")


def validate_config(config):
    """Validate configuration and warn about issues"""
    issues = []

    # Check primary WiFi credentials
    if not config.get("WIFI_SSID_1"):
        issues.append("❌ WIFI_SSID_1 is required (your home network)")

    if not config.get("WIFI_PASSWORD_1"):
        issues.append("❌ WIFI_PASSWORD_1 is required")
    elif config.get("WIFI_PASSWORD_1") == "your_password_here":
        issues.append("⚠️  WIFI_PASSWORD_1 still has default value - please update")

    # Check server configuration
    if not config.get("WEBSOCKET_SERVER"):
        issues.append("⚠️  WEBSOCKET_SERVER not set - using default")
    elif config.get("WEBSOCKET_SERVER") == "ws://192.168.1.100:8080":
        issues.append("⚠️  WEBSOCKET_SERVER has default value - update with your server IP")

    # Check device name
    if not config.get("DEVICE_NAME"):
        issues.append("⚠️  DEVICE_NAME not set - will use default")

    return issues


def main():
    """Main configuration script"""
    print("=" * 60)
    print("WiFi Walkie-Talkie Configuration")
    print("=" * 60)
    print()

    # Read .env file
    config = read_env_file()
    if config is None:
        sys.exit(1)

    print("📖 Read configuration from .env")
    print()

    # Validate configuration
    issues = validate_config(config)
    if issues:
        print("Configuration Issues:")
        for issue in issues:
            print(f"  {issue}")
        print()

        # Fatal errors
        if any(issue.startswith("❌") for issue in issues):
            print("❌ Cannot continue with critical errors. Please fix .env file.")
            sys.exit(1)

    # Show configuration summary
    print("Configuration Summary:")
    print(f"  Primary WiFi: {config.get('WIFI_SSID_1', 'NOT SET')}")
    print(f"  Server: {config.get('WEBSOCKET_SERVER', 'NOT SET')}")
    print(f"  Device Name: {config.get('DEVICE_NAME', 'NOT SET')}")

    # Show additional networks
    for i in range(2, 4):
        ssid = config.get(f"WIFI_SSID_{i}", "")
        if ssid and ssid != f"FamilyNetwork{i}":
            print(f"  Extra WiFi {i}: {ssid}")

    print()

    # Generate header file
    generate_config_header(config)

    print()
    print("✅ Configuration complete!")
    print()
    print("Next steps:")
    print("  1. Build firmware:   pio run")
    print("  2. Upload to device: pio run --target upload")
    print("  3. Monitor output:   pio device monitor")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
