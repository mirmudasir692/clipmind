import argparse
import sys
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="clipmind",
        description="clipmind - Extract audio from video files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clipmind -i video.mp4                    # Extract to video.mp3
  clipmind -i video.mp4 -o audio.wav      # Extract to audio.wav
  clipmind -i video.mkv -f mp3            # Extract to video.mp3
        """
    )

    parser.add_argument('-i', '--input', required=True, help='Input video file path')
    parser.add_argument('-o', '--output', help='Output audio file path (optional)')
    parser.add_argument('-f', '--format', choices=['mp3', 'wav'], default='mp3',
                       help='Output audio format (default: mp3)')

    return parser.parse_args()


def show_usage_instructions():
    print("clipmind - Audio Extraction Tool")
    print("==============================")
    print("This tool extracts audio from video files using FFmpeg.")
    print()
    print("Usage: clipmind -i <input_video> [-o <output_audio>] [-f <format>]")
    print()
    print("Options:")
    print("  -i, --input   Input video file path (required)")
    print("  -o, --output  Output audio file path (optional)")
    print("  -f, --format  Output format: mp3 or wav (default: mp3)")
    print()
    print("Example: clipmind -i video.mp4 -o audio.mp3")


def validate_and_get_output_path(input_path, output_path=None, audio_format='mp3'):
    if output_path:
        output_path = Path(output_path)
    else:
        input_path = Path(input_path)
        output_filename = input_path.stem + '.' + audio_format
        output_path = input_path.parent / output_filename

    output_dir = output_path.parent
    if not output_dir.exists():
        print(f"Error: Output directory does not exist: {output_dir}")
        sys.exit(1)

    return output_path


def main():
    from ..core.audio_extractor import get_audio_from_video
    args = parse_arguments()
    
    success = get_audio_from_video(
        args.input, 
        args.output, 
        args.format
    )
    
    if success:
        print(f"Successfully extracted audio to: {args.output if args.output else 'default path'}")
        sys.exit(0)
    else:
        print("Error: Audio extraction failed.")
        sys.exit(1)
