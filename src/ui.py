#!/usr/bin/env python3
"""
Interactive user interface for the music converter.
Handles user prompts, progress bars, and terminal output using Rich.
"""

from typing import Dict, Any, List, Tuple
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn, MofNCompleteColumn, TimeRemainingColumn, SpinnerColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from contextlib import contextmanager
import sys


class MusicConverterUI:
    """Interactive UI for music converter"""

    def __init__(self):
        self.console = Console()
        self.progress = None

    def show_welcome(self):
        """Display welcome message"""
        welcome_text = """
🎵 [bold blue]Music Converter[/bold blue] 🎵

Convert your music collection to different formats with metadata preservation.

Features:
• [green]✓[/green] Multiple codec support (MP3, AAC, FLAC, Opus)
• [green]✓[/green] Metadata preservation
• [green]✓[/green] Smart conversion (skip if already in target format)
• [green]✓[/green] Progress tracking
• [green]✓[/green] Detailed reports
        """
        self.console.print(Panel(welcome_text.strip(), title="Welcome", border_style="blue"))

    def get_codec_preferences(self) -> Tuple[str, int]:
        """Get user preferences for codec and bitrate"""
        self.console.print("\n[bold]Select Target Format:[/bold]")

        # Create format selection table
        format_table = Table(title="Available Formats", show_header=True)
        format_table.add_column("Code", style="cyan", width=6)
        format_table.add_column("Format", style="magenta")
        format_table.add_column("Description", style="white")
        format_table.add_column("Best For", style="green")

        format_table.add_row("1", "MP3", "MPEG Audio Layer 3", "Maximum compatibility")
        format_table.add_row("2", "AAC", "Advanced Audio Codec", "Apple devices, streaming")
        format_table.add_row("3", "FLAC", "Free Lossless Audio Codec", "Archival, audiophiles")
        format_table.add_row("4", "Opus", "Open, royalty-free codec", "Modern applications")

        self.console.print(format_table)

        # Get codec selection
        codec_choices = {
            "1": ("mp3", [128, 192, 256, 320]),
            "2": ("aac", [128, 192, 256, 320]),
            "3": ("flac", []),  # Lossless, no bitrate
            "4": ("opus", [64, 96, 128, 192, 256])
        }

        while True:
            choice = Prompt.ask(
                "\n[bold]Select format (1-4)[/bold]",
                choices=["1", "2", "3", "4"],
                default="1"
            )

            target_codec, available_bitrates = codec_choices[choice]

            # Show format info
            format_info = self._get_format_info(target_codec)
            self.console.print(Panel(format_info, title=f"Selected: {target_codec.upper()}", border_style="green"))

            if not available_bitrates:
                self.console.print(f"[green]✓[/green] {target_codec.upper()} is lossless - no bitrate needed")
                return target_codec, 0

            # Get bitrate selection
            bitrate = self._get_bitrate_selection(target_codec, available_bitrates)

            if Confirm.ask(f"\n[bold]Convert to {target_codec.upper()} at {bitrate} kbps?[/bold]", default=True):
                return target_codec, bitrate

    def _get_format_info(self, codec: str) -> str:
        """Get detailed information about a format"""
        format_info = {
            "mp3": """
MP3 (MPEG Audio Layer 3)
• Most widely supported audio format
• Good quality at reasonable file sizes
• Compatible with virtually all devices
• Recommended bitrate: 192-320 kbps
            """,
            "aac": """
AAC (Advanced Audio Codec)
• Better quality than MP3 at same bitrate
• Standard for Apple devices and streaming
• Good compression efficiency
• Recommended bitrate: 256 kbps
            """,
            "flac": """
FLAC (Free Lossless Audio Codec)
• Perfect quality, no data loss
• Half the size of original WAV
• Full metadata support
• Best for music archives and audiophiles
            """,
            "opus": """
Opus
• Modern, highly efficient codec
• Excellent quality at low bitrates
• Open and royalty-free
• Recommended bitrate: 128-192 kbps
            """
        }

        return format_info.get(codec, "Unknown format")

    def _get_bitrate_selection(self, codec: str, available_bitrates: List[int]) -> int:
        """Get bitrate selection from user"""
        self.console.print(f"\n[bold]Select Bitrate for {codec.upper()}:[/bold]")

        # Create bitrate options
        bitrate_descriptions = {
            128: "Good quality (small files)",
            192: "Better quality",
            256: "Excellent quality",
            320: "Maximum quality (larger files)",
            64: "Low bitrate (very small files)",
            96: "Low quality",
            128: "Good quality (Opus)",
            192: "Excellent quality (Opus)",
            256: "Maximum quality (Opus)"
        }

        bitrate_table = Table(show_header=False)
        bitrate_table.add_column("Option", style="cyan", width=4)
        bitrate_table.add_column("Bitrate", style="magenta")
        bitrate_table.add_column("Description", style="white")

        for i, bitrate in enumerate(available_bitrates, 1):
            description = bitrate_descriptions.get(bitrate, f"{bitrate} kbps")
            bitrate_table.add_row(str(i), f"{bitrate} kbps", description)

        self.console.print(bitrate_table)

        # Get user choice
        choices = [str(i) for i in range(1, len(available_bitrates) + 1)]
        choice = Prompt.ask("[bold]Select bitrate[/bold]", choices=choices, default="2")
        return available_bitrates[int(choice) - 1]

    def show_conversion_preview(self, source_dir: str, target_dir: str, total_files: int,
                              target_codec: str, target_bitrate: int):
        """Show conversion preview before starting"""
        self.console.print("\n[bold]Conversion Preview:[/bold]")

        preview_table = Table(show_header=False, box=None)
        preview_table.add_column("Property", style="cyan")
        preview_table.add_column("Value", style="white")

        preview_table.add_row("Source Directory:", source_dir)
        preview_table.add_row("Target Directory:", target_dir)
        preview_table.add_row("Files to Process:", str(total_files))
        preview_table.add_row("Target Codec:", target_codec.upper())
        preview_table.add_row("Target Bitrate:", f"{target_bitrate} kbps" if target_bitrate > 0 else "Lossless")

        self.console.print(preview_table)

        if not Confirm.ask("\n[bold]Start conversion?[/bold]", default=True):
            self.console.print("[yellow]Conversion cancelled.[/yellow]")
            sys.exit(0)

    @contextmanager
    def create_progress_bar(self, total_files: int):
        """Create and manage progress bar context"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Processing music files...", total=total_files)
            yield progress, task

    def update_progress(self, progress, task_id: int, description: str, advance: int = 1):
        """Update progress bar"""
        progress.update(task_id, description=description, advance=advance)

    def show_file_status(self, filename: str, action: str, size_before: int = 0, size_after: int = 0):
        """Show status for individual file processing"""
        action_colors = {
            "converting": "yellow",
            "copied": "green",
            "skipped": "blue",
            "error": "red"
        }

        color = action_colors.get(action.lower(), "white")

        if action.lower() in ["copied", "skipped"]:
            self.console.print(f"  • {filename} - [{color}]{action}[/{color}]")
        elif action.lower() == "converting":
            size_change = f" ({self._format_size(size_before)} → {self._format_size(size_after)})"
            self.console.print(f"  • {filename} - [{color}]converted[/{color}]{size_change}")
        elif action.lower() == "error":
            self.console.print(f"  • {filename} - [{color}]error[/{color}]")

    def show_conversion_summary(self, stats: Dict[str, Any], codec: str, bitrate: int):
        """Display final conversion summary"""
        self.console.print("\n[bold green]🎉 Conversion Complete! 🎉[/bold green]\n")

        # Create summary table
        summary_table = Table(title="Conversion Summary", show_header=True)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white", justify="right")

        summary_table.add_row("Total Files", str(stats.get('total', 0)))
        summary_table.add_row("Files Converted", f"[green]{stats.get('converted', 0)}[/green]")
        summary_table.add_row("Files Copied", f"[blue]{stats.get('copied', 0)}[/blue]")
        summary_table.add_row("Errors", f"[red]{stats.get('errors', 0)}[/red]")
        summary_table.add_row("", "")  # Separator
        summary_table.add_row("Original Size", self._format_size(stats.get('total_source_size', 0)))
        summary_table.add_row("Final Size", self._format_size(stats.get('total_target_size', 0)))

        if stats.get('space_saved', 0) > 0:
            space_saved_color = "green"
            space_saved_text = f"-{self._format_size(stats['space_saved'])} ({stats.get('space_saved_percentage', 0):.1f}%)"
        else:
            space_saved_color = "red"
            space_saved_text = f"+{self._format_size(abs(stats.get('space_saved', 0)))} (increased)"

        summary_table.add_row("Space Saved", f"[{space_saved_color}]{space_saved_text}[/{space_saved_color}]")

        self.console.print(summary_table)

        # Show target format info
        format_text = f"Target Format: {codec.upper()} @ {bitrate} kbps" if bitrate > 0 else f"Target Format: {codec.upper()} (Lossless)"
        self.console.print(f"\n[dim]{format_text}[/dim]")

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

    def show_error(self, message: str):
        """Display error message"""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def show_warning(self, message: str):
        """Display warning message"""
        self.console.print(f"[bold yellow]Warning:[/bold yellow] {message}")

    def show_info(self, message: str):
        """Display info message"""
        self.console.print(f"[dim]{message}[/dim]")

    def show_success(self, message: str):
        """Display success message"""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def create_loading_spinner(self, description: str = "Processing..."):
        """Create loading spinner for long operations"""
        from rich.live import Live
        from rich.spinner import Spinner

        spinner = Spinner("dots", text=description)
        return Live(spinner, console=self.console, transient=True)

    def ask_confirmation(self, question: str, default: bool = False) -> bool:
        """Ask user a yes/no question"""
        return Confirm.ask(question, default=default)

    def prompt_for_input(self, question: str, default: str = "", choices: List[str] = None) -> str:
        """Prompt user for input"""
        return Prompt.ask(question, default=default, choices=choices)

    def get_thread_count(self) -> int:
        """Get number of threads for parallel processing"""
        import os
        default_threads = max(1, (os.cpu_count() or 1) // 2)

        self.console.print(f"\n[bold]Parallel Processing Settings:[/bold]")
        self.console.print(f"[dim]Your system has {os.cpu_count() or 1} CPU cores.[/dim]")
        self.console.print(f"[dim]Recommended: {default_threads} threads (half of CPU cores)[/dim]")

        while True:
            choice = IntPrompt.ask(
                "\n[bold]Number of threads[/bold]",
                default=default_threads
            )
            if choice >= 1:
                return choice
            self.console.print("[red]Please enter a valid number (minimum 1)[/red]")