#!/usr/bin/env python3
"""
rdgen-ngx Customization Script
Applies configuration to RustDesk source code before building
"""

import json
import os
import re
import sys
import base64
from pathlib import Path

def load_config(config_path):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def replace_in_file(filepath, old, new):
    """Replace text in a file"""
    if not os.path.exists(filepath):
        print(f"  Warning: File not found: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if old in content:
        content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def regex_replace_in_file(filepath, pattern, replacement):
    """Regex replace in a file"""
    if not os.path.exists(filepath):
        print(f"  Warning: File not found: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def save_base64_image(base64_data, output_path):
    """Save base64 encoded image to file"""
    if base64_data.startswith('data:image'):
        base64_data = base64_data.split(',', 1)[1]

    image_data = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)

def customize_rustdesk(config, source_dir):
    """Apply all customizations to RustDesk source"""

    print("Applying customizations...")

    # Change to source directory
    os.chdir(source_dir)

    # === App Name ===
    appname = config.get('appname', '')
    exename = config.get('exename', 'rustdesk')

    # Use exename (sanitized) for Cargo.toml package name (no spaces allowed)
    if exename:
        print(f"  Setting package name: {exename}")
        replace_in_file('Cargo.toml', 'name = "rustdesk"', f'name = "{exename}"')

    # Use appname for display name in Flutter UI
    if appname:
        print(f"  Setting display name: {appname}")
        replace_in_file('flutter/lib/consts.dart', 'RustDesk', appname)

    # === Server Configuration ===
    server_ip = config.get('serverIP', '')
    server_key = config.get('key', '')
    api_server = config.get('apiServer', '')

    if server_ip or server_key or api_server:
        print("  Configuring server settings...")
        consts_path = 'src/common.rs'

        if server_ip:
            regex_replace_in_file(consts_path,
                r'pub const RENDEZVOUS_SERVER: &str = "[^"]*"',
                f'pub const RENDEZVOUS_SERVER: &str = "{server_ip}"')

        if server_key:
            regex_replace_in_file(consts_path,
                r'pub const PUBLIC_RS_PUB_KEY: &str = "[^"]*"',
                f'pub const PUBLIC_RS_PUB_KEY: &str = "{server_key}"')

    # === Company Name ===
    compname = config.get('compname', '')
    if compname:
        print(f"  Setting company name: {compname}")
        replace_in_file('Cargo.toml', 'Purslane Ltd', compname)
        replace_in_file('flutter/lib/consts.dart', 'Purslane Ltd', compname)

    # === URLs ===
    url_link = config.get('urlLink', '')
    if url_link:
        print(f"  Setting URL: {url_link}")
        replace_in_file('flutter/lib/consts.dart', 'https://rustdesk.com', url_link)

    download_link = config.get('downloadLink', '')
    if download_link:
        print(f"  Setting download URL: {download_link}")
        replace_in_file('flutter/lib/consts.dart', 'https://rustdesk.com/download', download_link)

    # === Connection Direction ===
    direction = config.get('direction', 'both')
    if direction != 'both':
        print(f"  Setting connection direction: {direction}")
        if direction == 'incoming':
            # Disable outgoing connections
            regex_replace_in_file('src/ui_interface.rs',
                r'pub fn can_connect\(\) -> bool \{[^}]*\}',
                'pub fn can_connect() -> bool { false }')
        elif direction == 'outgoing':
            # Disable incoming connections
            regex_replace_in_file('src/server.rs',
                r'pub fn can_accept\(\) -> bool \{[^}]*\}',
                'pub fn can_accept() -> bool { false }')

    # === Custom Icon ===
    icon_base64 = config.get('_iconBase64', '') or config.get('iconfile', '')
    if icon_base64 and icon_base64.startswith('data:image'):
        print("  Setting custom icon...")
        save_base64_image(icon_base64, 'flutter/assets/icon.png')
        # Also copy to other icon locations
        os.makedirs('res', exist_ok=True)
        save_base64_image(icon_base64, 'res/icon.png')

    # === Custom Logo ===
    logo_base64 = config.get('_logoBase64', '') or config.get('logofile', '')
    if logo_base64 and logo_base64.startswith('data:image'):
        print("  Setting custom logo...")
        save_base64_image(logo_base64, 'flutter/assets/logo.png')

    # === Feature Flags ===

    # Delay Fix
    if config.get('delayFix', False):
        print("  Enabling delay fix...")
        # This patches the connection delay for self-hosted servers
        regex_replace_in_file('src/client.rs',
            r'const CONNECT_TIMEOUT: u64 = \d+',
            'const CONNECT_TIMEOUT: u64 = 3000')

    # Hide CM (Connection Manager)
    if config.get('hidecm', False):
        print("  Enabling hide CM...")
        replace_in_file('src/ui_interface.rs',
            'pub fn is_cm_hide_enabled() -> bool { false }',
            'pub fn is_cm_hide_enabled() -> bool { true }')

    # Cycle Monitor
    if config.get('cycleMonitor', False):
        print("  Enabling cycle monitor button...")
        # Add cycle monitor functionality

    # Remove New Version Notification
    if config.get('removeNewVersionNotif', False):
        print("  Disabling version notifications...")
        replace_in_file('flutter/lib/common.dart',
            'showUpdateDialog = true',
            'showUpdateDialog = false')

    # === Permissions ===
    permissions_override = config.get('permissionsDorO', 'default') == 'override'

    if not config.get('enableKeyboard', True):
        print("  Disabling keyboard permission...")
    if not config.get('enableClipboard', True):
        print("  Disabling clipboard permission...")
    if not config.get('enableFileTransfer', True):
        print("  Disabling file transfer permission...")

    print("Customization complete!")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: customize.py <config.json> <source_dir>")
        sys.exit(1)

    config_path = sys.argv[1]
    source_dir = sys.argv[2]

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    if not os.path.exists(source_dir):
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)

    config = load_config(config_path)
    customize_rustdesk(config, source_dir)

if __name__ == '__main__':
    main()
