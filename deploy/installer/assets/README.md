# CasareRPA Installer Assets

This directory contains assets required for building the Windows installer.

## Required Files

### Icon (casarerpa.ico)

Application icon used for:
- Executable icon
- Start Menu shortcuts
- Desktop shortcuts
- Windows taskbar

**Specifications:**
- Format: ICO (Windows Icon)
- Sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256 (all in one ICO file)
- Color depth: 32-bit (RGBA)

**Tools to create:**
- GIMP (free, open-source)
- IcoFX (paid)
- Greenfish Icon Editor Pro (free)
- Online: https://convertico.com/

### NSIS Banner Images

**installer-banner.bmp**
- Used on: Welcome and Finish pages (left panel)
- Size: 164 x 314 pixels
- Format: BMP (24-bit)

**installer-header.bmp**
- Used on: All other pages (top header)
- Size: 150 x 57 pixels
- Format: BMP (24-bit)

**Design guidelines:**
- Use dark theme colors to match installer
- Include CasareRPA logo/branding
- Keep text minimal
- Recommended colors:
  - Background: #1e1e1e (dark gray)
  - Accent: #5a8a9a (teal)
  - Text: #e0e0e0 (light gray)

### License (LICENSE.txt)

- Copied from project root LICENSE file
- Displayed on License Agreement page

## Placeholder Files

The build script (`build.ps1`) will create placeholder files if these are missing.
Replace placeholders with proper assets before release.

## Creating Assets

### Quick Icon Creation (Python)

```python
from PIL import Image

# Create a simple icon
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
icon = Image.new('RGBA', (256, 256), (45, 90, 122, 255))  # Teal background

# Add text/logo here with ImageDraw

# Save as ICO
icon.save('casarerpa.ico', format='ICO', sizes=[(s[0], s[1]) for s in sizes])
```

### Quick BMP Creation (Python)

```python
from PIL import Image

# Banner (164x314)
banner = Image.new('RGB', (164, 314), (30, 30, 30))
banner.save('installer-banner.bmp')

# Header (150x57)
header = Image.new('RGB', (150, 57), (30, 30, 30))
header.save('installer-header.bmp')
```

## File Checklist

Before building release installer:

- [ ] casarerpa.ico - Professional icon with all sizes
- [ ] installer-banner.bmp - 164x314 branded banner
- [ ] installer-header.bmp - 150x57 branded header
- [ ] LICENSE.txt - Updated copyright year
