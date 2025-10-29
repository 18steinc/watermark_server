# Watermark Server

A **lightweight, self-hosted Flask app** to add a semi-transparent watermark to photos — ideal for photographers, studios, or anyone needing fast bulk watermarking.

**No quality loss. No color shift. No format conversion.**  
Preserves **HEIC, PNG, JPG** exactly — only overlays your logo.

---

## Features

- Upload multiple images (HEIC, JPG, PNG)
- Auto-corrects orientation (no sideways iPhone photos)
- **100% quality output** — no compression, no dimming
- Preserves **original file format** (HEIC → HEIC, PNG → PNG)
- Semi-transparent watermark (50% opacity) in bottom-right
- Auto-delete files after 24 hours
- Mobile-friendly UI with **Water.css**
- Success confetti animation
- Clean design 

---

## Requirements

- Python 3.9+
- `logo.png` — **your watermark image** (added by you, not in repo)

---

## Quick Start

### 1. Clone the repo
git clone https://github.com/18steinc/watermark_server.git
cd watermark_server

### 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

### 3. Install dependencies
pip install Flask Pillow pillow-heif

### 4. Add your watermark
- Place your logo as 'logo.png' in the project root
- This file is in .gitignore — it will not be committed
- cp /path/to/your/logo.png logo.png

### 5. Run the server
- `python app.py`

- Server runs on: `http://localhost:5000`

---


## Running on your local server 

### 1. Created required folders 
- `mkdir -p Uploads watermarked logs templates static`

### 2. Create MacOS LaunchAgent
- Save as `~/Library/LaunchAgents/com.watermarkserver.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.watermarkserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/absolute/path/to/watermark_server/.venv/bin/python</string>
        <string>/absolute/path/to/watermark_server/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/absolute/path/to/watermark_server/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/absolute/path/to/watermark_server/logs/stderr.log</string>
</dict>
</plist>
```



### 3. Load it 
- `launchctl load ~/Library/LaunchAgents/com.watermarkserver.plist`

---

## Customization 

- Watermark Size: Edit 0.2 in app.py (watermark_width = int(base_image.width * 0.2))
- Opacity: Edit 0.5 in alpha.point(lambda p: int(p * 0.5))
- Position: Edit 20 in position = (..., 20)
- Auto-delete time: Edit hours=24 in cleanup_old_files()

---

## Troubleshooting

- "No module named pillow_heif" → pip install pillow-heif
- HEIC not saving → Ensure pillow-heif is installed
- Images dimmed → Recent version fixes it. Use quality=100
- Server not starting → Check logs: cat logs/stderr.log
