#!/usr/bin/env python3
"""
Report generation for the music converter.
Creates markdown reports summarizing conversion results.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import os

from src.converter import ConversionResult


class ReportGenerator:
    """Generates markdown reports for music conversion results"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_report(self, results: List[ConversionResult], report_path: Path,
                       source_dir: str, target_dir: str, codec: str, bitrate: int) -> Path:
        """Generate comprehensive markdown report"""
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self._build_report_content(results, source_dir, target_dir, codec, bitrate))

        return report_path

    def _build_report_content(self, results: List[ConversionResult],
                            source_dir: str, target_dir: str,
                            codec: str, bitrate: int) -> str:
        """Build the markdown report content"""
        stats = self._calculate_statistics(results)

        content = []
        content.append("# Music Conversion Report\n")
        content.append(f"**Generated:** {self.timestamp}\n")

        content.append("## Summary\n")
        content.append(f"- **Source Directory:** `{source_dir}`\n")
        content.append(f"- **Target Directory:** `{target_dir}`\n")
        content.append(f"- **Target Codec:** {codec.upper()}\n")
        content.append(f"- **Target Bitrate:** {bitrate if bitrate > 0 else 'Lossless (FLAC)'} kbps\n")

        content.append("\n## Overall Statistics\n")
        content.append(f"- **Total Files:** {stats['total']}\n")
        content.append(f"- **Converted:** {stats['converted']}\n")
        content.append(f"- **Copied (No Conversion Needed):** {stats['copied']}\n")
        content.append(f"- **Errors:** {stats['errors']}\n")
        content.append(f"- **Success Rate:** {stats['success_rate']:.1f}%\n")

        content.append("\n## Space Savings\n")
        content.append(f"- **Original Size:** {self._format_size(stats['original_size'])}\n")
        content.append(f"- **Final Size:** {self._format_size(stats['final_size'])}\n")

        if stats['space_saved'] >= 0:
            content.append(f"- **Space Saved:** {self._format_size(stats['space_saved'])} ")
            content.append(f"({stats['space_saved_percent']:.1f}%)\n")
        else:
            content.append(f"- **Space Increase:** {self._format_size(abs(stats['space_saved']))} ")
            content.append(f"({abs(stats['space_saved_percent']):.1f}%)\n")

        # Converted Files Section
        converted_files = [r for r in results if r.action == 'converted']
        if converted_files:
            content.append("\n## Converted Files\n")
            content.append(f"{len(converted_files)} files were converted from their original format.\n")
            content.append("\n| Original File | Original Format | Target Format | Original Size | Final Size | Reduction |\n")
            content.append("|---------------|----------------|---------------|---------------|------------|----------|\n")

            for result in converted_files:
                original_format = f"{result.source_format.get('codec', 'unknown')} "
                original_bitrate = result.source_format.get('bitrate')
                if original_bitrate:
                    original_format += f"@ {original_bitrate / 1000:.0f}kbps"
                else:
                    original_format += "(VBR)"

                target_bitrate_str = ""
                if bitrate > 0:
                    target_bitrate_str = f"@ {bitrate}kbps"
                else:
                    target_bitrate_str = "(Lossless)"

                target_format = f"{codec.upper()} {target_bitrate_str}"

                reduction = self._format_size(result.source_size - result.target_size)
                content.append(f"| {result.source_path.name} | {original_format} | {target_format} | ")
                content.append(f"{self._format_size(result.source_size)} | {self._format_size(result.target_size)} | {reduction} |\n")

        # Copied Files Section
        copied_files = [r for r in results if r.action == 'copied']
        if copied_files:
            content.append("\n## Copied Files (No Conversion Needed)\n")
            content.append(f"{len(copied_files)} files were already in the target format and were copied directly.\n\n")

            for result in copied_files:
                content.append(f"- `{result.source_path.name}` - ")
                content.append(f"Already {result.source_format.get('codec', 'unknown')} at ")
                original_bitrate = result.source_format.get('bitrate')
                if original_bitrate:
                    content.append(f"{original_bitrate / 1000:.0f}kbps - ")
                content.append("No conversion needed\n")

        # Error Files Section
        error_files = [r for r in results if r.action == 'error']
        if error_files:
            content.append("\n## Errors\n")
            content.append(f"{len(error_files)} files encountered errors during processing.\n\n")

            for result in error_files:
                content.append(f"- `{result.source_path.name}`: ")
                content.append(f"{result.error_message or 'Unknown error'}\n")

        # Conversion Details Section
        content.append("\n## Conversion Details\n\n")
        content.append("### About This Conversion\n\n")

        format_descriptions = {
            'mp3': "MP3 is the most widely supported audio format, compatible with virtually all devices and media players.",
            'aac': "AAC offers better quality than MP3 at the same bitrate and is the standard for Apple devices and streaming services.",
            'flac': "FLAC is a lossless format that provides perfect audio quality while reducing file size by about 40-50% compared to WAV.",
            'opus': "Opus is a modern, highly efficient codec that provides excellent quality at very low bitrates."
        }

        content.append(f"{format_descriptions.get(codec.lower(), 'Unknown format.')}\n\n")

        if codec.lower() == 'flac':
            content.append("Since you selected FLAC (lossless), all conversions preserve the original audio quality exactly.\n\n")
        else:
            content.append(f"The {bitrate}kbps bitrate provides a balance between audio quality and file size.\n\n")

        content.append("---\n")
        content.append("*Report generated by Music Converter CLI Tool*")

        return "".join(content)

    def _calculate_statistics(self, results: List[ConversionResult]) -> Dict[str, Any]:
        """Calculate statistics from conversion results"""
        total = len(results)
        converted = len([r for r in results if r.action == 'converted'])
        copied = len([r for r in results if r.action == 'copied'])
        errors = len([r for r in results if r.action == 'error'])

        original_size = sum(r.source_size for r in results)
        final_size = sum(r.target_size for r in results)

        space_saved = original_size - final_size
        space_saved_percent = (space_saved / original_size * 100) if original_size > 0 else 0

        success_rate = ((total - errors) / total * 100) if total > 0 else 0

        return {
            'total': total,
            'converted': converted,
            'copied': copied,
            'errors': errors,
            'original_size': original_size,
            'final_size': final_size,
            'space_saved': space_saved,
            'space_saved_percent': space_saved_percent,
            'success_rate': success_rate
        }

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes as human-readable size"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def print_report_location(self, report_path: Path):
        """Print information about the report location"""
        print(f"\n📄 Detailed report saved to: {report_path}")
        print(f"   You can open this file to view the complete conversion summary.")
