# rdgen-ngx Local Builder

Build custom RustDesk clients locally instead of using GitHub Actions. Perfect for homelabbers and MSPs with their own hardware.

## Why Build Locally?

| Method | Build Time | Cost | Requirements |
|--------|------------|------|--------------|
| GitHub Actions | 30-45 min | Free (2000 min/month) | GitHub account |
| **Local (8-core)** | **10-15 min** | Your hardware | Docker |
| **Local (16+ cores)** | **5-10 min** | Your hardware | Docker |

## Supported Platforms

| Platform | Local Build | Notes |
|----------|-------------|-------|
| Linux x64 | ✅ Full support | Native Docker build |
| Linux ARM64 | ✅ Full support | Native or QEMU emulation |
| Windows | ⚠️ Cross-compile | Best with Windows VM |
| Android | ⚠️ Experimental | Requires Android SDK |
| macOS | ❌ Not supported | Requires actual Mac hardware |

## Quick Start

### 1. Create your config

Export a configuration from rdgen-ngx UI, or create `config.json`:

```json
{
  "exename": "MySupport",
  "appname": "My Support Tool",
  "serverIP": "rustdesk.example.com",
  "key": "YOUR_PUBLIC_KEY",
  "compname": "My Company",
  "direction": "incoming",
  "cycleMonitor": true,
  "removeNewVersionNotif": true
}
```

### 2. Build the Docker image (first time only)

```bash
cd local-builder
docker build -t rdgen-builder .
```

This takes 15-20 minutes but only needs to be done once.

### 3. Build your custom client

```bash
# Linux build
docker run -v $(pwd)/output:/output -v $(pwd)/config.json:/config.json rdgen-builder --platform linux

# Windows cross-compile (experimental)
docker run -v $(pwd)/output:/output -v $(pwd)/config.json:/config.json rdgen-builder --platform windows

# Specify version
docker run -v $(pwd)/output:/output -v $(pwd)/config.json:/config.json rdgen-builder --platform linux --version 1.4.5
```

### 4. Find your build

```bash
ls -la output/
# MySupport-linux-x64.tar.gz
```

## Using Docker Compose

```bash
# Edit config.json with your settings
cp config.example.json config.json
nano config.json

# Build Linux client
PLATFORM=linux docker compose up builder

# Build specific version
PLATFORM=linux VERSION=1.4.5 docker compose up builder
```

## Configuration Options

All options from rdgen-ngx web UI are supported:

### General
| Option | Description |
|--------|-------------|
| `exename` | Filename for the executable |
| `appname` | Display name in the app |
| `direction` | `incoming`, `outgoing`, or `both` |
| `compname` | Company name in About dialog |

### Server
| Option | Description |
|--------|-------------|
| `serverIP` | Your RustDesk server address |
| `key` | Public key from your server |
| `apiServer` | API server URL (optional) |

### Features
| Option | Description |
|--------|-------------|
| `delayFix` | Fix connection delay for self-hosted |
| `cycleMonitor` | Add monitor cycle button |
| `removeNewVersionNotif` | Disable update notifications |
| `hidecm` | Hide connection manager window |

### Visual
| Option | Description |
|--------|-------------|
| `_iconBase64` | Custom icon (base64 PNG) |
| `_logoBase64` | Custom logo (base64 PNG) |

## Hardware Requirements

| Build Type | RAM | Disk | CPU |
|------------|-----|------|-----|
| Minimum | 8 GB | 30 GB | 4 cores |
| Recommended | 16 GB | 50 GB | 8+ cores |
| Fast builds | 32 GB | 50 GB | 16+ cores |

## Running on Proxmox

### LXC Container (Recommended)

```bash
# Create Ubuntu 22.04 LXC with:
# - 8 GB RAM minimum
# - 50 GB disk
# - 4+ CPU cores
# - Nested virtualization enabled (for Docker)

# Inside the container:
apt update && apt install -y docker.io docker-compose
git clone https://github.com/lumon-io/rdgen-ngx.git
cd rdgen-ngx/local-builder
docker build -t rdgen-builder .
```

### VM (For Windows builds)

For best Windows builds, create a Windows VM:
1. Windows 10/11 or Server 2019+
2. Install Visual Studio Build Tools
3. Install Rust, Flutter, Python
4. Clone RustDesk and apply customizations manually

## Troubleshooting

### Build fails with out of memory
Increase container/VM RAM or reduce parallel jobs:
```bash
docker run ... rdgen-builder --platform linux --jobs 2
```

### Windows cross-compile fails
Windows cross-compilation is experimental. For production Windows builds:
1. Use GitHub Actions (default rdgen method)
2. Use a Windows VM with native tools
3. Use a Windows machine

### Missing dependencies
Rebuild the Docker image to get latest dependencies:
```bash
docker build --no-cache -t rdgen-builder .
```

## Pre-built Images

Coming soon: Pre-built Docker images on GitHub Container Registry:

```bash
# Pull pre-built image (faster than building locally)
docker pull ghcr.io/lumon-io/rdgen-builder:latest
```

## Contributing

Found a bug or want to add a feature? Open an issue or PR at:
https://github.com/lumon-io/rdgen-ngx

## License

MIT License - See [LICENSE](../LICENSE) for details.
