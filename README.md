# Music Converter CLI

A powerful Python-based command-line tool for batch converting audio files with metadata preservation.

## Features

✅ **Multiple Codec Support**: MP3, AAC, FLAC, Opus
✅ **Interactive UI**: Beautiful terminal interface with Rich library
✅ **Metadata Preservation**: Maintain all song information during conversion
✅ **Smart Conversion**: Automatically skip files already in target format
✅ **Progress Tracking**: Real-time progress bars with file status
✅ **Comprehensive Reports**: Markdown reports with space savings statistics
✅ **Batch Processing**: Convert entire music collections automatically
✅ **Unicode Filename Support**: Handles Chinese characters and special symbols

## Project Structure

```
music-converter/
├── music/                          # Source music files
│   └── (your audio files here)
├── music-converted/                # Converted files
│   └── (converted audio files)
│   └── conversion-report.md
├── src/
│   ├── __init__.py
│   ├── converter.py               # Core conversion logic
│   ├── metadata.py                # Metadata handling with mutagen
│   ├── ui.py                      # Interactive UI with Rich
│   └── reporter.py                # Markdown report generation
├── music-converter.py             # Main entry point
├── requirements.txt               # Python dependencies
└── .gitignore
```

## Installation

### Prerequisites

1. **Python 3.8+**
2. **ffmpeg** - Install via package manager:

```bash
# Ubuntu/Debian
sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

3. **Python Dependencies**:

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install individually
pip install click rich mutagen
```

### Quick Install

```bash
git clone <repository-url>
cd music-converter
pip install -r requirements.txt
chmod +x music-converter.py
```

## Usage

### Interactive Mode (Recommended)

Run without arguments for interactive prompts:

```bash
python3 music-converter.py
```

This will guide you through:
1. Format selection (MP3/AAC/FLAC/Opus)
2. Bitrate selection
3. Preview and confirmation
4. Conversion with progress tracking

### Command Line Mode

For automation and scripts:

```bash
# Convert to MP3 at 320kbps
python3 music-converter.py --source music --target music-converted --codec mp3 --bitrate 320

# Convert to FLAC (lossless, no bitrate)
python3 music-converter.py --source music --target music-converted --codec flac

# Force mode (no prompts, use defaults: MP3 320kbps)
python3 music-converter.py --source music --target music-converted --force

# Dry run (see what would be converted without actually converting)
python3 music-converter.py --source music --target music-converted --dry-run --codec mp3 --bitrate 320
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Source directory | `music` |
| `--target` | Target directory | `music-converted` |
| `--codec` | Target codec (mp3/aac/flac/opus) | Interactive |
| `--bitrate` | Target bitrate in kbps | Interactive |
| `--force` | Skip prompts, use defaults | False |
| `--dry-run` | Preview without converting | False |
| `--help` | Show help message | - |

## Format Details

### MP3 (MPEG Audio Layer 3)
- **Best for**: Maximum compatibility
- **Quality**: Good at 192-320 kbps
- **Size**: Medium compression

### AAC (Advanced Audio Codec)
- **Best for**: Apple devices, streaming
- **Quality**: Better than MP3 at same bitrate
- **Size**: Efficient compression

### FLAC (Free Lossless Audio Codec)
- **Best for**: Archival, audiophiles
- **Quality**: Perfect (no data loss)
- **Size**: ~40-50% smaller than WAV

### Opus
- **Best for**: Modern applications
- **Quality**: Excellent at low bitrates
- **Size**: Very efficient

## Example Output

```
🎵 Music Converter 🎵

Convert your music collection to different formats with metadata preservation.

Features:
• ✓ Multiple codec support (MP3, AAC, FLAC, Opus)
• ✓ Metadata preservation
• • Smart conversion (skip if already in target format)
• • Progress tracking
• • Detailed reports

Found 1 audio files
Using preset: MP3 @ 320 kbps

  Processing music.mp3 ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1/1 0:00:00 100%

🎉 Conversion Complete! 🎉

          Conversion Summary
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Metric          ┃            Value ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ Total Files     │                1 │
│ Files Converted │                1 │
│ Files Copied    │                0 │
│ Errors          │                0 │
│                 │                  │
│ Original Size   │           25.6 MB│
│ Final Size      │           12.8 MB│
│ Space Saved     │       12.8 MB    │
│                 │       (49.9%)    │
└─────────────────┴──────────────────┘

📄 Detailed report saved to: music-converted/conversion-report.md
```

## Report Example

The tool generates a comprehensive markdown report:

```markdown
# Music Conversion Report

**Generated:** 2025-11-25 16:44:21

## Summary
- **Source Directory:** `/home/juntao/Documents/music-converter/music`
- **Target Directory:** `/home/juntao/Documents/music-converter/music-converted`
- **Target Codec:** MP3
- **Target Bitrate:** 320 kbps

## Overall Statistics
- **Total Files:** 1
- **Converted:** 1
- **Copied (No Conversion Needed):** 0
- **Errors:** 0
- **Success Rate:** 100.0%

## Space Savings
- **Original Size:** 25.6 MB
- **Final Size:** 12.8 MB
- **Space Saved:** 12.8 MB (49.9%)

## Converted Files
1 files were converted from their original format.

| Original File | Original Format | Target Format | Original Size | Final Size | Reduction |
|---------------|----------------|---------------|---------------|------------|----------|
| music.m4a | alac @ 891kbps | MP3 @ 320kbps | 25.6 MB | 12.8 MB | 12.8 MB |
```

## Smart Conversion Logic

The tool automatically determines if a file needs conversion:

1. **Convert if**:
   - Source codec ≠ target codec
   - Source bitrate > target bitrate
   - Source is lossless and target is lossy

2. **Copy (skip conversion) if**:
   - Source codec = target codec
   - Source bitrate ≤ target bitrate
   - Already in optimal format

## Metadata Preservation

All metadata is preserved during conversion:
- Title, Artist, Album
- Track number, Disc number
- Year, Genre
- Album Artist
- Comments
- Cover Art (embedded)

Supported formats:
- ID3 tags (MP3)
- MP4 tags (M4A, AAC)
- Vorbis comments (FLAC, Opus, OGG)
- ASF tags (WMA)

## Architecture

### Core Components

1. **converter.py** - MusicConverter class
   - File scanning and discovery
   - Audio info extraction (ffprobe)
   - Conversion decision logic
   - FFmpeg command execution

2. **metadata.py** - MetadataHandler class
   - Extract metadata from various formats
   - Apply metadata to converted files
   - Support for ID3, MP4, Vorbis, ASF tags

3. **ui.py** - MusicConverterUI class
   - Interactive prompts for codec/bitrate selection
   - Progress bars and status display
   - Beautiful terminal formatting with Rich

4. **reporter.py** - ReportGenerator class
   - Generate markdown reports
   - Calculate statistics and space savings
   - Format tables and summaries

### Technologies Used

- **Python 3.8+** - Core language
- **Click** - CLI framework
- **Rich** - Terminal UI and formatting
- **mutagen** - Audio metadata library
- **ffmpeg** - Audio conversion engine

## Testing

### Quick Test

```bash
# Test with dry run
python3 music-converter.py --source music --target test-output --dry-run --codec mp3 --bitrate 320

# Test actual conversion
python3 music-converter.py --source music --target test-output --codec mp3 --bitrate 320

# Test all formats
python3 music-converter.py --source music --target test-flac --codec flac
python3 music-converter.py --source music --target test-aac --codec aac --bitrate 256
python3 music-converter.py --source music --target test-opus --codec opus --bitrate 192
```

### Test Results

Successfully tested with:
- ✅ M4A (ALAC) → MP3 conversion
- ✅ Metadata preservation
- ✅ Space savings calculation (49.9% reduction)
- ✅ Progress tracking
- ✅ Report generation

## Troubleshooting

### Common Issues

**"ffmpeg not found"**
```bash
# Install ffmpeg
sudo apt-get install ffmpeg
```

**"Permission denied"**
```bash
# Make script executable
chmod +x music-converter.py
```

**"No module named click/rich/mutagen"**
```bash
# Install dependencies
pip install -r requirements.txt
```

**"No audio files found"**
- Check source directory path
- Ensure files have supported extensions (.mp3, .m4a, .aac, .flac, .ogg, .wav, .wma)

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions welcome! Areas for improvement:
- Parallel conversion
- GUI interface
- More audio format support
- Playlist generation
- Normalization options

## Author

Created with ❤️ for music lovers who want to manage their collections efficiently.

---

**Version**: 1.0.0
**Python**: 3.8+
**License**: MIT