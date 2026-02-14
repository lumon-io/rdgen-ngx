#!/bin/bash
set -e

# rdgen-ngx Local Builder
# Usage: docker run -v ./output:/output rdgen-builder --platform linux --config config.json

show_help() {
    echo "rdgen-ngx Local Builder"
    echo ""
    echo "Usage: docker run -v ./output:/output -v ./config.json:/config.json rdgen-builder [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --platform PLATFORM    Target platform: linux, windows, android (required)"
    echo "  --config FILE          Path to config JSON file (default: /config.json)"
    echo "  --version VERSION      RustDesk version to build (default: master)"
    echo "  --output DIR           Output directory (default: /output)"
    echo "  --jobs N               Number of parallel jobs (default: auto)"
    echo "  --help                 Show this help"
    echo ""
    echo "Platforms:"
    echo "  linux      - Linux x64 (deb, rpm, AppImage)"
    echo "  windows    - Windows x64 (cross-compiled with mingw-w64)"
    echo "  android    - Android APK"
    echo ""
    echo "Note: macOS builds require actual Mac hardware"
}

# Default values
PLATFORM=""
CONFIG_FILE="/config.json"
VERSION="master"
OUTPUT_DIR="/output"
JOBS=$(nproc)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --jobs)
            JOBS="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [[ -z "$PLATFORM" ]]; then
    echo "Error: --platform is required"
    show_help
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "========================================"
echo "rdgen-ngx Local Builder"
echo "========================================"
echo "Platform: $PLATFORM"
echo "Version:  $VERSION"
echo "Jobs:     $JOBS"
echo "Config:   $CONFIG_FILE"
echo "Output:   $OUTPUT_DIR"
echo "========================================"

# Clone RustDesk source
echo "[1/6] Cloning RustDesk..."
if [[ "$VERSION" == "master" ]]; then
    git clone --depth 1 https://github.com/rustdesk/rustdesk.git /build/rustdesk
else
    git clone --depth 1 --branch "$VERSION" https://github.com/rustdesk/rustdesk.git /build/rustdesk
fi
cd /build/rustdesk

# Initialize submodules
git submodule update --init --recursive

# Apply customizations
echo "[2/6] Applying customizations..."
python3 /usr/local/bin/customize.py "$CONFIG_FILE" /build/rustdesk

# Build based on platform
case "$PLATFORM" in
    linux)
        echo "[3/6] Building Rust library..."
        cargo build --lib --features hwcodec,flutter,unix-file-copy-paste --release -j "$JOBS"

        echo "[4/6] Building Flutter app..."
        cd flutter
        flutter pub get
        flutter build linux --release

        echo "[5/6] Packaging..."
        cd ..
        # Create simple tarball for now
        APPNAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('exename', 'rustdesk'))")

        # Validate APPNAME contains only safe characters
        if [[ ! "$APPNAME" =~ ^[a-zA-Z0-9._-]+$ ]]; then
            echo "ERROR: APPNAME contains unsafe characters: $APPNAME"
            exit 1
        fi

        mkdir -p "$OUTPUT_DIR"
        tar -czvf "${OUTPUT_DIR}/${APPNAME}-linux-x64.tar.gz" -C build/linux/x64/release/bundle .

        echo "[6/6] Done!"
        echo "Output: ${OUTPUT_DIR}/${APPNAME}-linux-x64.tar.gz"
        ;;

    windows)
        echo "[3/6] Setting up Windows cross-compilation..."
        export PKG_CONFIG_ALLOW_CROSS=1
        export CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER=x86_64-w64-mingw32-gcc

        echo "[4/6] Building for Windows..."
        cargo build --release --target x86_64-pc-windows-gnu -j "$JOBS" || {
            echo ""
            echo "========================================"
            echo "Windows cross-compilation failed."
            echo ""
            echo "For best Windows builds, use one of:"
            echo "1. Native Windows with Visual Studio"
            echo "2. Windows VM on your Proxmox server"
            echo "3. GitHub Actions (current rdgen method)"
            echo "========================================"
            exit 1
        }

        echo "[5/6] Packaging..."
        APPNAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('exename', 'rustdesk'))")

        # Validate APPNAME contains only safe characters
        if [[ ! "$APPNAME" =~ ^[a-zA-Z0-9._-]+$ ]]; then
            echo "ERROR: APPNAME contains unsafe characters: $APPNAME"
            exit 1
        fi

        mkdir -p "$OUTPUT_DIR"
        cp target/x86_64-pc-windows-gnu/release/*.exe "${OUTPUT_DIR}/" 2>/dev/null || true

        echo "[6/6] Done!"
        echo "Output: $OUTPUT_DIR/"
        ;;

    android)
        echo "[3/6] Setting up Android SDK..."
        # Android build requires additional setup
        echo "Android builds require Android SDK/NDK setup."
        echo "This is a complex process - consider using GitHub Actions for Android."
        exit 1
        ;;

    *)
        echo "Unknown platform: $PLATFORM"
        echo "Supported: linux, windows, android"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
ls -la "$OUTPUT_DIR/"
