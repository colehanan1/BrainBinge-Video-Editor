# Caption Fonts

This directory contains custom fonts for caption styling.

## Recommended Fonts for Social Media Captions

### Primary Font: Montserrat
- **Style**: Bold, modern sans-serif
- **Why**: Clean, readable, popular on TikTok/Instagram
- **Download**: [Google Fonts - Montserrat](https://fonts.google.com/specimen/Montserrat)
- **Files needed**: `Montserrat-Bold.ttf` or `Montserrat-ExtraBold.ttf`

### Alternative Fonts

1. **Poppins**
   - Bold, geometric sans-serif
   - Download: [Google Fonts - Poppins](https://fonts.google.com/specimen/Poppins)
   - Files: `Poppins-Bold.ttf`

2. **Bebas Neue**
   - All-caps, condensed display font
   - Great for short, punchy captions
   - Download: [Google Fonts - Bebas Neue](https://fonts.google.com/specimen/Bebas+Neue)
   - Files: `BebasNeue-Regular.ttf`

3. **Oswald**
   - Condensed sans-serif, high impact
   - Download: [Google Fonts - Oswald](https://fonts.google.com/specimen/Oswald)
   - Files: `Oswald-Bold.ttf`

## Installation

### Option 1: Download Directly

1. Visit the font download link above
2. Click "Download family"
3. Extract the ZIP file
4. Copy the `.ttf` file(s) to this directory (`data/fonts/`)

### Option 2: Google Fonts Helper Script

```bash
# Download Montserrat Bold
cd data/fonts/
curl -o Montserrat-Bold.ttf "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
```

### Option 3: System Installation (macOS/Linux)

**macOS:**
```bash
# Copy to system fonts
cp data/fonts/Montserrat-Bold.ttf ~/Library/Fonts/
```

**Linux:**
```bash
# Copy to user fonts
mkdir -p ~/.local/share/fonts
cp data/fonts/Montserrat-Bold.ttf ~/.local/share/fonts/
fc-cache -f -v
```

**Windows:**
1. Right-click the `.ttf` file
2. Select "Install" or "Install for all users"

## Font Fallback

If a custom font is not available, the system will automatically fall back to:
1. **Arial Bold** (Windows/macOS default)
2. **Helvetica Bold** (macOS)
3. **DejaVu Sans Bold** (Linux)

## Font Configuration

Specify your font in `config/brand_example.yaml`:

```yaml
captions:
  font:
    family: "Montserrat-Bold"  # Font family name
    size: 28                    # Font size in points
    weight: "bold"              # Font weight (bold, normal)
```

## Font Testing

Test if a font is working correctly:

```bash
# Generate captions with your font
heygen-clipper process \
  --video data/input/video.mp4 \
  --script data/input/script.txt \
  --config config/brand_example.yaml

# Play the styled ASS file in VLC/MPV to verify font rendering
vlc data/output/styled/video.ass
```

## Font Licensing

All recommended fonts are available under the **SIL Open Font License (OFL)**:
- ✅ Free for commercial use
- ✅ Can be bundled with software
- ✅ Can be modified
- ❌ Cannot be sold by itself

Always check the license file included with the font for specific terms.

## Troubleshooting

### Font Not Displaying Correctly

1. **Verify font is installed:**
   ```bash
   # macOS/Linux
   fc-list | grep -i montserrat

   # Or check this directory
   ls -lh data/fonts/
   ```

2. **Check font name in ASS file:**
   - Open `data/output/styled/video.ass` in a text editor
   - Look for the `Style:` line
   - Verify `Fontname` matches your installed font

3. **Use exact font family name:**
   - Font family name must match exactly (case-sensitive)
   - Example: `Montserrat-Bold`, not `Montserrat Bold` or `montserrat-bold`

### Font Fallback Warning

If you see a warning about font fallback:
```
Font 'Montserrat-Bold' not found, using Arial fallback
```

This means the specified font is not installed. Install it following the instructions above.

## Custom Fonts

To add your own custom font:

1. Place the `.ttf` or `.otf` file in this directory
2. Update your config file with the exact font family name
3. Test the output to ensure it renders correctly

**Note**: The exact font family name can be found by:
- Opening the font file
- Checking the "Font name" or "Family" field
- Or using a tool like `fc-scan` on Linux:
  ```bash
  fc-scan data/fonts/YourFont.ttf | grep family
  ```
