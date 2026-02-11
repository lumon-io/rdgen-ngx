# rdgen-ngx

**Next-generation RustDesk Custom Client Generator**

A web-based tool for generating customized RustDesk clients with your own branding, server settings, and configuration. Fork of [bryangerlach/rdgen](https://github.com/bryangerlach/rdgen) with significant enhancements.

## Features

### Core Functionality
- Generate custom RustDesk clients for **Windows** (64/32-bit), **macOS**, **Linux**, and **Android**
- Pre-configure server address, relay key, and API server
- Custom app name, icons, logos, and privacy screens
- Control permissions, security settings, and connection types

### rdgen-ngx Enhancements

| Feature | Description |
|---------|-------------|
| **Build History** | View all past builds at `/builds/` with status and download links |
| **Bookmarkable Status Pages** | Each build gets a unique URL (`/builds/<uuid>/`) you can bookmark |
| **Email Notifications** | Get download links emailed when your build completes |
| **Server-side Configs** | Save and load configurations on the server (including images) |
| **Platform Defaults** | Auto-set recommended options when selecting a platform |
| **Tooltips** | Hover over any option to see a detailed explanation |
| **Fixed macOS Bundle ID** | Custom builds no longer conflict with existing RustDesk installs |

## Quick Start

### Docker Compose (Recommended)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/rdgen-ngx.git
cd rdgen-ngx

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the service
docker compose up -d

# Access at http://localhost:8000
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `GHUSER` | Yes | GitHub username with RustDesk fork |
| `GHBEARER` | Yes | GitHub personal access token |
| `REPONAME` | Yes | GitHub repo name (usually `rustdesk`) |
| `GHBRANCH` | No | Branch to use (default: `master`) |
| `ZIP_PASSWORD` | Yes | Password for encrypting build secrets |
| `GENURL` | Yes | Public URL of your rdgen instance |
| `PROTOCOL` | No | `http` or `https` (default: `https`) |
| `EMAIL_HOST` | No | SMTP server for notifications |
| `EMAIL_PORT` | No | SMTP port (default: `587`) |
| `EMAIL_HOST_USER` | No | SMTP username |
| `EMAIL_HOST_PASSWORD` | No | SMTP password |
| `DEFAULT_FROM_EMAIL` | No | From address for notifications |

## GitHub Setup

rdgen-ngx uses GitHub Actions to build clients. You need:

1. **Fork RustDesk** to your GitHub account
2. Add these **workflow files** to `.github/workflows/`:
   - `generator-windows.yml`
   - `generator-macos.yml`
   - `generator-linux.yml`
   - `generator-android.yml`
   - `bridge.yml`
3. Add **repository secrets**:
   - `GENURL` - Your rdgen URL
   - `ZIP_PASSWORD` - Same as your rdgen ZIP_PASSWORD

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main generator form |
| `/builds/` | GET | Build history list |
| `/builds/<uuid>/` | GET | Single build status |
| `/download` | GET | Download build artifact |
| `/api/configs/` | GET | List saved configurations |
| `/api/configs/save` | POST | Save a configuration |
| `/api/configs/load` | GET | Load a configuration |
| `/api/configs/delete` | POST | Delete a configuration |

## Platform-Specific Recommendations

When you select a platform, rdgen-ngx automatically sets recommended options:

| Platform | Delay Fix | Cycle Monitor | X Offline | Hide Updates |
|----------|-----------|---------------|-----------|--------------|
| Windows 64-bit | - | ✓ | - | ✓ |
| Windows 32-bit | - | ✓ | - | ✓ |
| macOS | ✓ | ✓ | - | ✓ |
| Linux | - | ✓ | ✓ | ✓ |
| Android | - | - | - | ✓ |

## Development

```bash
# Run locally without Docker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Credits

- **rdgen-ngx** by [Jeremy Lynnes](https://github.com/lumon-io)
- Original rdgen by [Bryan Gerlach](https://github.com/bryangerlach/rdgen)
- RustDesk by [RustDesk Team](https://github.com/rustdesk/rustdesk)
