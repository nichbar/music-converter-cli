#!/usr/bin/env python3
"""
Core conversion logic for the music converter.
Handles file scanning, conversion decision making, and ffmpeg execution.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of processing a single audio file"""
    source_path: Path
    target_path: Path
    action: str  # 'converted', 'copied', 'error'
    source_size: int  # bytes
    target_size: int  # bytes
    source_format: Dict[str, Any]
    error_message: Optional[str] = None

    @property
    def size_saved(self) -> int:
        """Calculate space saved in bytes"""
        return self.source_size - self.target_size

    @property
    def size_saved_mb(self) -> float:
        """Calculate space saved in MB"""
        return self.size_saved / (1024 * 1024)


@dataclass
class AudioInfo:
    """Audio file information"""
    codec: str
    bitrate: Optional[int]
    sample_rate: Optional[int]
    duration: Optional[float]
    channels: Optional[int]


class MusicConverter:
    """Main music conversion class"""

    # Supported audio file extensions
    AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.aac', '.flac', '.ogg', '.wav', '.wma'}

    # Output format extensions
    FORMAT_EXTENSIONS = {
        'mp3': '.mp3',
        'aac': '.m4a',
        'flac': '.flac',
        'opus': '.opus'
    }

    def __init__(self, source_dir: Path, target_dir: Path):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.results: List[ConversionResult] = []

    def scan_directory(self) -> List[Path]:
        """Recursively scan for audio files in source directory"""
        audio_files = []

        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {self.source_dir}")

        for file_path in self.source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.AUDIO_EXTENSIONS:
                audio_files.append(file_path)

        return sorted(audio_files)

    def get_audio_info(self, file_path: Path) -> AudioInfo:
        """Extract audio information using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # Find audio stream
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break

            if not audio_stream:
                raise ValueError("No audio stream found in file")

            # Extract information
            codec = audio_stream.get('codec_name', 'unknown')
            bitrate_str = audio_stream.get('bit_rate') or data.get('format', {}).get('bit_rate')
            bitrate = int(bitrate_str) if bitrate_str else None
            sample_rate = int(audio_stream.get('sample_rate', 0)) if audio_stream.get('sample_rate') else None
            duration = float(data.get('format', {}).get('duration', 0)) if data.get('format', {}).get('duration') else None
            channels = audio_stream.get('channels')

            return AudioInfo(
                codec=codec,
                bitrate=bitrate,
                sample_rate=sample_rate,
                duration=duration,
                channels=channels
            )

        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to analyze audio file: {e.stderr}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse ffprobe output: {e}")

    def needs_conversion(self, audio_info: AudioInfo, target_codec: str, target_bitrate: int) -> bool:
        """Determine if a file needs conversion"""
        source_codec = audio_info.codec.lower()
        source_bitrate = audio_info.bitrate if audio_info.bitrate else 0
        target_bitrate_bps = target_bitrate * 1000

        # If codec doesn't match, may still need conversion
        if source_codec != target_codec.lower():
            # Lossless source to lossy target - always convert
            if source_codec == 'flac':
                return True

            # Lossy source to lossy target
            if source_codec in ['mp3', 'aac', 'mp3', 'wma', 'ogg'] and target_codec.lower() in ['mp3', 'aac', 'opus', 'wma', 'ogg']:
                # Check if bitrates are similar (within 10% tolerance)
                bitrate_diff_percent = abs(source_bitrate - target_bitrate_bps) / source_bitrate * 100 if source_bitrate > 0 else 0

                # If bitrates are similar and source is already lossy, skip conversion
                # to avoid quality loss from re-encoding
                if bitrate_diff_percent < 10:  # Within 10% tolerance
                    return False

                # Otherwise convert (upgrading quality or changing format)
                return True

            # Different codec types (e.g., lossy to lossless, or non-standard codecs)
            return True

        # Same codec - check bitrate
        if source_bitrate > target_bitrate_bps:
            # Downsampling - convert to reduce file size
            return True
        elif source_bitrate < target_bitrate_bps:
            # Upsampling - don't convert to avoid unnecessary re-encoding
            return False
        else:
            # Identical codec and bitrate - no conversion needed
            return False

    def build_ffmpeg_command(self, input_path: Path, output_path: Path,
                           target_codec: str, target_bitrate: int) -> List[str]:
        """Build ffmpeg command for conversion"""
        base_cmd = ['ffmpeg', '-i', str(input_path), '-y']  # -y to overwrite

        # Codec-specific settings
        if target_codec.lower() == 'mp3':
            cmd = base_cmd + ['-c:a', 'libmp3lame', '-b:a', f'{target_bitrate}k']
        elif target_codec.lower() == 'aac':
            cmd = base_cmd + ['-c:a', 'aac', '-b:a', f'{target_bitrate}k']
            # For AAC with M4A container, we need to handle album art properly
            # Use mp4 container format and handle embedded artwork
            cmd.extend(['-c:v', 'copy'])  # Copy album art as-is
        elif target_codec.lower() == 'flac':
            cmd = base_cmd + ['-c:a', 'flac', '-compression_level', '8']
        elif target_codec.lower() == 'opus':
            cmd = base_cmd + ['-c:a', 'libopus', '-b:a', f'{target_bitrate}k']
        else:
            raise ValueError(f"Unsupported target codec: {target_codec}")

        # Preserve metadata
        cmd.extend(['-map_metadata', '0'])

        # For AAC/M4A, ensure proper container format
        if target_codec.lower() == 'aac':
            cmd.extend(['-movflags', '+faststart'])  # Optimize for streaming
            # Force mp4 container format
            cmd.extend(['-f', 'mp4'])

        # Output path
        cmd.append(str(output_path))

        return cmd

    def convert_file(self, input_path: Path, output_path: Path,
                    target_codec: str, target_bitrate: int) -> bool:
        """Convert audio file using ffmpeg"""
        cmd = self.build_ffmpeg_command(input_path, output_path, target_codec, target_bitrate)

        try:
            # Run ffmpeg with suppressed output but allow error messages
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            # Print error for debugging but don't crash
            print(f"FFmpeg error for {input_path.name}: {e.stderr}")
            return False

    def copy_file(self, input_path: Path, output_path: Path) -> bool:
        """Copy file without conversion"""
        try:
            import shutil
            shutil.copy2(input_path, output_path)
            return True
        except Exception as e:
            print(f"Copy error for {input_path.name}: {e}")
            return False

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except FileNotFoundError:
            return 0

    def process_file(self, input_path: Path, target_codec: str, target_bitrate: int) -> ConversionResult:
        """Process a single audio file"""
        try:
            # Get source file info
            audio_info = self.get_audio_info(input_path)
            source_size = self.get_file_size(input_path)

            # Calculate relative path and output path
            relative_path = input_path.relative_to(self.source_dir)

            # Change extension based on target format
            target_ext = self.FORMAT_EXTENSIONS.get(target_codec.lower(), f'.{target_codec}')
            output_path = self.target_dir / relative_path.with_suffix(target_ext)

            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine action
            needs_conversion_result = self.needs_conversion(audio_info, target_codec, target_bitrate)

            if needs_conversion_result:
                # Convert file
                success = self.convert_file(input_path, output_path, target_codec, target_bitrate)
                action = 'converted' if success else 'error'
            else:
                # Copy file
                success = self.copy_file(input_path, output_path)
                action = 'copied' if success else 'error'

            # Get target file size
            target_size = self.get_file_size(output_path) if success else 0

            # Create source format info dict
            source_format = {
                'codec': audio_info.codec,
                'bitrate': audio_info.bitrate,
                'sample_rate': audio_info.sample_rate,
                'duration': audio_info.duration
            }

            result = ConversionResult(
                source_path=input_path,
                target_path=output_path,
                action=action,
                source_size=source_size,
                target_size=target_size,
                source_format=source_format,
                error_message=None if success else f"{'Conversion' if needs_conversion_result else 'Copy'} failed"
            )

            return result

        except Exception as e:
            # Error processing file
            return ConversionResult(
                source_path=input_path,
                target_path=input_path,  # No target path
                action='error',
                source_size=self.get_file_size(input_path),
                target_size=0,
                source_format={},
                error_message=str(e)
            )

    def process_all_files(self, audio_files: List[Path], target_codec: str, target_bitrate: int) -> List[ConversionResult]:
        """Process all audio files"""
        results = []
        for input_path in audio_files:
            result = self.process_file(input_path, target_codec, target_bitrate)
            results.append(result)

        self.results = results
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if not self.results:
            return {}

        total_files = len(self.results)
        converted_files = len([r for r in self.results if r.action == 'converted'])
        copied_files = len([r for r in self.results if r.action == 'copied'])
        error_files = len([r for r in self.results if r.action == 'error'])

        total_source_size = sum(r.source_size for r in self.results)
        total_target_size = sum(r.target_size for r in self.results)
        space_saved = total_source_size - total_target_size

        return {
            'total': total_files,
            'converted': converted_files,
            'copied': copied_files,
            'errors': error_files,
            'total_source_size': total_source_size,
            'total_target_size': total_target_size,
            'space_saved': space_saved,
            'space_saved_percentage': (space_saved / total_source_size * 100) if total_source_size > 0 else 0
        }

    def create_target_directory(self):
        """Create the target directory if it doesn't exist"""
        self.target_dir.mkdir(parents=True, exist_ok=True)
