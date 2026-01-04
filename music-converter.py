#!/usr/bin/env python3
"""
Music Converter - CLI tool for batch converting audio files with metadata preservation

Usage:
    python music-converter.py                    # Interactive mode
    python music-converter.py --force           # Force mode with defaults (MP3 320kbps)
    python music-converter.py --help            # Show help
"""

import click
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os

from src.converter import MusicConverter
from src.metadata import MetadataHandler
from src.ui import MusicConverterUI
from src.reporter import ReportGenerator


@click.command()
@click.option('--source', default='music', help='Source directory containing music files')
@click.option('--target', default='music-converted', help='Target directory for converted files')
@click.option('--force', is_flag=True, help='Force conversion without prompts (MP3 320kbps)')
@click.option('--codec', type=click.Choice(['mp3', 'aac', 'flac', 'opus']), help='Target codec (overrides interactive)')
@click.option('--bitrate', type=int, help='Target bitrate in kbps (ignored for FLAC)')
@click.option('--threads', type=int, help='Number of threads for parallel processing')
@click.option('--dry-run', is_flag=True, help='Show what would be converted without actually converting')
def main(source: str, target: str, force: bool, codec: str, bitrate: int, threads: int, dry_run: bool):
    """
    Batch convert audio files with metadata preservation and smart conversion detection.

    This tool converts audio files from the source directory to the target directory,
    preserving all metadata and skipping files that are already in the target format.
    """
    # Initialize components
    ui = MusicConverterUI()
    metadata_handler = MetadataHandler()
    reporter = ReportGenerator()

    try:
        # Show welcome message
        if not force and not (codec or bitrate):
            ui.show_welcome()

        # Validate source directory
        source_path = Path(source).absolute()
        if not source_path.exists():
            ui.show_error(f"Source directory does not exist: {source_path}")
            return 1

        if not source_path.is_dir():
            ui.show_error(f"Source path is not a directory: {source_path}")
            return 1

        # Set target directory
        target_path = Path(target).absolute()

        # Initialize converter
        converter = MusicConverter(source_path, target_path)

        # Scan for audio files
        with ui.create_loading_spinner("Scanning for audio files...") as live:
            audio_files = converter.scan_directory()

        if not audio_files:
            ui.show_warning("No audio files found in source directory")
            return 0

        ui.show_info(f"Found {len(audio_files)} audio files")

        # Get user preferences or use defaults
        if force or (codec or bitrate):
            # Use provided values or defaults
            target_codec = codec or 'mp3'
            target_bitrate = bitrate or 320
            ui.show_info(f"Using preset: {target_codec.upper()} @ {target_bitrate} kbps")
            # Skip interactive preview if we have command line options
            preview_mode = False
        else:
            # Interactive mode
            target_codec, target_bitrate = ui.get_codec_preferences()
            preview_mode = True

        # Show conversion preview (only in interactive mode or if forced)
        if preview_mode or force:
            ui.show_conversion_preview(
                str(source_path),
                str(target_path),
                len(audio_files),
                target_codec,
                target_bitrate
            )

        # Create target directory
        converter.create_target_directory()

        # Determine thread count
        if force or threads:
            # Use provided value or default (half CPU cores)
            num_threads = threads if threads else max(1, (os.cpu_count() or 1) // 2)
            ui.show_info(f"Using {num_threads} thread(s) for processing")
        else:
            # Interactive mode - ask user
            num_threads = ui.get_thread_count()
            ui.show_info(f"Using {num_threads} thread(s) for processing")

        # Thread-safe lock for progress updates
        progress_lock = threading.Lock()
        completed_count = 0
        total_files = len(audio_files)

        # Process files concurrently with progress bar
        results = []
        with ui.create_progress_bar(total_files) as (progress, task):
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                # Submit all jobs
                future_to_file = {
                    executor.submit(converter.process_file, fp, target_codec, target_bitrate): fp
                    for fp in audio_files
                }

                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]

                    try:
                        result = future.result()

                        # Apply metadata AFTER conversion (sequential, thread-safe)
                        if result.action == 'converted' and not dry_run:
                            metadata_success = metadata_handler.apply_metadata(
                                result.source_path, result.target_path
                            )
                            if not metadata_success:
                                ui.show_warning(f"Could not apply metadata to {file_path.name}")

                        results.append(result)

                        # Show status for the file
                        if result.action == 'converted':
                            ui.show_file_status(
                                result.source_path.name, "converted",
                                result.source_size, result.target_size
                            )
                        elif result.action == 'copied':
                            ui.show_file_status(result.source_path.name, "copied")
                        elif result.action == 'error':
                            ui.show_file_status(result.source_path.name, "error")

                    except Exception as e:
                        ui.show_error(f"Error processing {file_path.name}: {e}")
                        # Create error result
                        from src.converter import ConversionResult
                        error_result = ConversionResult(
                            source_path=file_path,
                            target_path=file_path,
                            action='error',
                            source_size=converter.get_file_size(file_path),
                            target_size=0,
                            source_format={},
                            error_message=str(e)
                        )
                        results.append(error_result)
                        ui.show_file_status(file_path.name, "error")

                    # Thread-safe progress update
                    with progress_lock:
                        completed_count += 1
                        progress.update(
                            task, advance=1,
                            description=f"Processing ({completed_count}/{total_files})"
                        )

        # Calculate and show statistics
        if results:
            # Store results in converter for statistics calculation
            converter.results = results
            stats = converter.get_statistics()
        else:
            stats = {
                'total': 0,
                'converted': 0,
                'copied': 0,
                'errors': 0,
                'total_source_size': 0,
                'total_target_size': 0,
                'space_saved': 0,
                'space_saved_percentage': 0
            }

        if dry_run:
            ui.show_info("\n[bold]Dry Run Complete - No files were actually converted[/bold]")
            ui.show_info("Run without --dry-run to perform the actual conversion")

        ui.show_conversion_summary(stats, target_codec, target_bitrate)

        # Generate report
        if not dry_run:
            report_path = target_path / 'conversion-report.md'
            reporter.generate_report(
                results,
                report_path,
                str(source_path),
                str(target_path),
                target_codec,
                target_bitrate
            )
            reporter.print_report_location(report_path)

        return 0

    except KeyboardInterrupt:
        ui.show_warning("Conversion cancelled by user")
        return 1

    except Exception as e:
        ui.show_error(f"An unexpected error occurred: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())