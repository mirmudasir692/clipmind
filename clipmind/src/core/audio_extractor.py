import ffmpeg
from pathlib import Path


from ..utils.validation import validate_video_file, validate_ffmpeg
from ..cli.interface import validate_and_get_output_path
from ..utils.resolution import RESOLUTION_PROFILES


def extract_audio(video_path, output_path, audio_format='mp3', start=None, end=None):
    try:
        audio_codec = 'mp3' if audio_format.lower() == 'mp3' else 'pcm_s16le'

        input_kwargs = {}
        if start is not None:
            input_kwargs['ss'] = start
        if end is not None:
            input_kwargs['to'] = end

        stream = ffmpeg.input(str(video_path), **input_kwargs)
        stream = ffmpeg.output(stream, str(output_path), acodec=audio_codec, loglevel='quiet')

        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        return True

    except ImportError:
        return False
    except ffmpeg.Error as e:
        return False
    except Exception as e:
        return False

def get_default_output_path(video_path, audio_format='mp3'):
    video_path = Path(video_path)
    output_filename = video_path.stem + '.' + audio_format
    return video_path.parent / output_filename


def get_audio_from_video(video_path, output_path=None, audio_format='mp3', start=None, end=None):
    """
    Library function to extract audio from video.
    
    Args:
        video_path (str): Path to the input video file
        output_path (str, optional): Path for the output audio file
        audio_format (str): Audio format ('mp3' or 'wav')
        start (float/str, optional): Start time of the slice (e.g., 10.5 or "00:00:10")
        end (float/str, optional): End time of the slice (e.g., 15.0 or "00:00:15")
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    if not validate_video_file(video_path):
        return False
    
    if not validate_ffmpeg():
        return False
    
    output_path = validate_and_get_output_path(video_path, output_path, audio_format)
    
    return extract_audio(video_path, str(output_path), audio_format, start, end)

def chunk_video_adaptive(video_path, output_dir=None, resolutions=None, segment_duration=10):
    """
    Break video into HLS chunks at multiple resolutions with master manifest.
    Works with both local paths and URLs (http/https).
    
    Args:
        video_path (str): Path or URL to input video
        output_dir (str, optional): Directory for output chunks. Default: ./video_chunks/
        resolutions (list): List of resolution keys (e.g., ['360p', '720p']). Default: ['360p', '720p', '1080p']
        segment_duration (int): Target duration of each segment in seconds. Default: 10
        
    Returns:
        dict or False: On success returns {
            'master_manifest': Path,           # Path to master.m3u8
            'output_dir': Path,                # Root output directory
            'variants': {                      # Dict of generated variants
                '360p': {
                    'manifest': Path,          # Path to variant playlist
                    'segments_dir': Path,      # Directory containing .ts files
                    'segment_count': int       # Number of segments generated
                },
                ...
            }
        }, returns False on failure
    """
    try:
        if not validate_ffmpeg():
            return False
        
        # Setup paths
        video_path_str = str(video_path)
        if output_dir is None:
            # Extract filename from URL or path for default naming
            base_name = Path(video_path_str.split('?')[0]).stem or 'video'
            output_dir = Path(f"{base_name}_chunks")
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default resolutions if not specified
        if resolutions is None:
            resolutions = ['360p', '720p', '1080p']
        
        # Validate resolutions
        for res in resolutions:
            if res not in RESOLUTION_PROFILES:
                return False
        
        variants = {}
        
        # Generate chunks for each resolution
        for res_key in resolutions:
            profile = RESOLUTION_PROFILES[res_key]
            
            # Create subdirectory for this resolution
            res_dir = output_dir / res_key
            res_dir.mkdir(exist_ok=True)
            
            manifest_path = res_dir / "playlist.m3u8"
            segment_pattern = str(res_dir / "segment_%03d.ts")
            
            # Build ffmpeg stream
            stream = ffmpeg.input(video_path_str)
            
            # Apply scaling and encoding settings
            stream = ffmpeg.filter(stream, 'scale', profile['width'], profile['height'])
            
            # HLS output settings
            stream = ffmpeg.output(
                stream,
                str(manifest_path),
                format='hls',
                start_number=0,
                hls_time=segment_duration,
                hls_playlist_type='vod',
                hls_segment_filename=segment_pattern,
                hls_base_url=f"{res_key}/",  # Relative path for client resolution
                vcodec='h264',
                acodec='aac',
                video_bitrate=profile['video_bitrate'],
                audio_bitrate=profile['audio_bitrate'],
                preset='fast',
                pix_fmt='yuv420p',
                loglevel='quiet'
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Count generated segments
            segments = list(res_dir.glob("segment_*.ts"))
            
            variants[res_key] = {
                'manifest': manifest_path,
                'segments_dir': res_dir,
                'segment_count': len(segments)
            }
        
        # Generate master playlist
        master_manifest = output_dir / "master.m3u8"
        _write_master_playlist(master_manifest, resolutions, variants)
        
        return {
            'master_manifest': master_manifest,
            'output_dir': output_dir,
            'variants': variants
        }
        
    except ImportError:
        return False
    except ffmpeg.Error as e:
        return False
    except Exception as e:
        return False


def _write_master_playlist(master_path, resolutions, variants):
    """Generate master HLS playlist referencing all variant playlists."""
    lines = ["#EXTM3U"]
    
    for res_key in resolutions:
        profile = RESOLUTION_PROFILES[res_key]
        # Relative path to variant playlist (e.g., "360p/playlist.m3u8")
        variant_path = f"{res_key}/playlist.m3u8"
        
        lines.append(
            f"#EXT-X-STREAM-INF:"
            f"BANDWIDTH={profile['bandwidth']},"
            f"RESOLUTION={profile['width']}x{profile['height']},"
            f"NAME=\"{res_key}\""
        )
        lines.append(variant_path)
    
    master_path.write_text('\n'.join(lines) + '\n')


def chunk_video_single(video_path, output_dir=None, resolution='720p', segment_duration=10):
    """
    Generate HLS chunks for single resolution only.
    
    Args:
        video_path (str): Path or URL to input video
        output_dir (str, optional): Output directory
        resolution (str): Single resolution (e.g., '720p')
        segment_duration (int): Seconds per segment
        
    Returns:
        dict or False: {'manifest': Path, 'segments_dir': Path, 'output_dir': Path} or False
    """
    result = chunk_video_adaptive(
        video_path=video_path,
        output_dir=output_dir,
        resolutions=[resolution],
        segment_duration=segment_duration
    )
    
    if result:
        return {
            'manifest': result['variants'][resolution]['manifest'],
            'segments_dir': result['variants'][resolution]['segments_dir'],
            'output_dir': result['output_dir']
        }
    return False