# ClipPy - Video to Audio Converter

A simple and efficient Python tool to extract audio from video files using FFmpeg.

## Features

- 🎵 Extract high-quality audio (MP3, WAV)
- ✂️ Video tools: merge, crop, overlay, resolve conversion
- ✅ File validation and error handling
- 🖥️ CLI interface and Python library API
- 🛠️ Minimal dependencies

## Installation

### Prerequisites

1. **Python 3.6+**
2. **FFmpeg** (must be in system PATH)

### Install Dependencies

```bash
pip install ffmpeg-python
```

## Usage

### Method 1: Command Line Interface

Once installed, use the `clippy` command:

```bash
clippy -i video.mp4 [-o audio.mp3] [-f mp3]
```

#### Examples:

```bash
# Basic extraction
clippy -i video.mp4

# Custom output format
clippy -i video.mkv -f wav
```

### Method 2: Python Library

```python
from clippy import get_audio_from_video

# Extract audio
success = get_audio_from_video("video.mp4", "audio.mp3")

# Advanced video tools
from clippy import merge_videos, crop_video
merge_videos("part1.mp4", "part2.mp4", "merged.mp4")
```

## Project Structure

```
clippy/
├── clippy/               # Core package
│   └── src/
│       ├── cli/          # CLI implementation
│       ├── core/         # Audio & Video tools
│       └── utils/        # Validations
├── pyproject.toml        # Build configuration
└── README.md             # Documentation
```

## License

MIT