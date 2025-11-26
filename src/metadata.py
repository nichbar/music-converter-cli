#!/usr/bin/env python3
"""
Metadata handling for the music converter.
Extracts and applies metadata using mutagen library.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

try:
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wave import WAVE
    from mutagen.asf import ASF
except ImportError:
    print("Mutagen library not installed. Run: pip install mutagen")
    raise


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataHandler:
    """Handles metadata extraction and application for audio files"""

    def __init__(self):
        self.logger = logger

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from an audio file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        try:
            if suffix == '.mp3':
                return self._extract_mp3_metadata(file_path)
            elif suffix in ['.m4a', '.aac']:
                return self._extract_mp4_metadata(file_path)
            elif suffix == '.flac':
                return self._extract_flac_metadata(file_path)
            elif suffix == '.ogg':
                return self._extract_ogg_metadata(file_path)
            elif suffix == '.wav':
                return self._extract_wav_metadata(file_path)
            elif suffix == '.wma':
                return self._extract_wma_metadata(file_path)
            else:
                self.logger.warning(f"Unsupported file format for metadata: {suffix}")
                return {}
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {file_path.name}: {e}")
            return {}

    def _extract_mp3_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from MP3 file"""
        try:
            audio = MP3(file_path)
            tags = {}

            if audio.tags:
                # Standard ID3 tags
                tag_mapping = {
                    'TIT2': 'title',
                    'TPE1': 'artist',
                    'TALB': 'album',
                    'TRCK': 'track',
                    'TDRC': 'year',
                    'TCON': 'genre',
                    'TPE2': 'albumartist',
                    'TPOS': 'discnumber',
                    'COMM::eng': 'comment',
                    'TIT3': 'subtitle'
                }

                for id3_tag, tag_name in tag_mapping.items():
                    if id3_tag in audio.tags:
                        value = audio.tags[id3_tag]
                        if hasattr(value, 'text'):
                            tags[tag_name] = str(value.text[0])
                        else:
                            tags[tag_name] = str(value)

                # Handle artwork
                if 'APIC:' in audio.tags:
                    artwork_data = audio.tags['APIC:'].data
                    tags['artwork'] = artwork_data

            return tags
        except Exception as e:
            self.logger.error(f"Error extracting MP3 metadata: {e}")
            return {}

    def _extract_mp4_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from M4A/AAC file"""
        try:
            audio = MP4(file_path)
            tags = {}

            if audio.tags:
                # MP4 tag mapping
                tag_mapping = {
                    '\xa9nam': 'title',
                    '\xa9ART': 'artist',
                    '\xa9alb': 'album',
                    'trkn': 'track',
                    '\xa9day': 'year',
                    '\xa9gen': 'genre',
                    'aART': 'albumartist',
                    'disk': 'discnumber',
                    '\xa9cmt': 'comment',
                    '\xa9lyr': 'lyrics'
                }

                for mp4_tag, tag_name in tag_mapping.items():
                    if mp4_tag in audio.tags:
                        value = audio.tags[mp4_tag]
                        if isinstance(value, list) and value:
                            if tag_name in ['track', 'discnumber']:
                                # Handle track/disk numbers (tuple)
                                if isinstance(value[0], tuple) and len(value[0]) >= 1:
                                    tags[tag_name] = str(value[0][0])
                            else:
                                tags[tag_name] = str(value[0])
                        else:
                            tags[tag_name] = str(value)

                # Handle artwork
                if 'covr' in audio.tags:
                    artwork_data = audio.tags['covr'][0]
                    tags['artwork'] = artwork_data

            return tags
        except Exception as e:
            self.logger.error(f"Error extracting MP4 metadata: {e}")
            return {}

    def _extract_flac_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from FLAC file"""
        try:
            audio = FLAC(file_path)
            tags = {}

            if audio.tags:
                # FLAC/Vorbis tag mapping (case-insensitive)
                tag_mapping = {
                    'title': 'title',
                    'artist': 'artist',
                    'album': 'album',
                    'tracknumber': 'track',
                    'date': 'year',
                    'genre': 'genre',
                    'albumartist': 'albumartist',
                    'discnumber': 'discnumber',
                    'comment': 'comment',
                    'lyrics': 'lyrics'
                }

                for flac_tag, tag_name in tag_mapping.items():
                    # Vorbis comments are case-insensitive
                    for key in audio.tags:
                        if key.lower() == flac_tag.lower():
                            value = audio.tags[key]
                            if isinstance(value, list) and value:
                                tags[tag_name] = str(value[0])
                            else:
                                tags[tag_name] = str(value)
                            break

                # Handle artwork (FLAC can have multiple pictures)
                if audio.pictures:
                    tags['artwork'] = audio.pictures[0].data

            return tags
        except Exception as e:
            self.logger.error(f"Error extracting FLAC metadata: {e}")
            return {}

    def _extract_ogg_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from OGG file"""
        try:
            audio = OggVorbis(file_path)
            tags = {}

            if audio.tags:
                tag_mapping = {
                    'title': 'title',
                    'artist': 'artist',
                    'album': 'album',
                    'tracknumber': 'track',
                    'date': 'year',
                    'genre': 'genre',
                    'albumartist': 'albumartist',
                    'discnumber': 'discnumber',
                    'comment': 'comment'
                }

                for ogg_tag, tag_name in tag_mapping.items():
                    for key in audio.tags:
                        if key.lower() == ogg_tag.lower():
                            value = audio.tags[key]
                            if isinstance(value, list) and value:
                                tags[tag_name] = str(value[0])
                            else:
                                tags[tag_name] = str(value)
                            break

            return tags
        except Exception as e:
            self.logger.error(f"Error extracting OGG metadata: {e}")
            return {}

    def _extract_wav_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from WAV file"""
        try:
            audio = WAVE(file_path)
            tags = {}

            # WAV files often have limited metadata in ID3 chunks
            if audio.tags:
                # Similar to MP3 but with WAV-specific handling
                tag_mapping = {
                    'TIT2': 'title',
                    'TPE1': 'artist',
                    'TALB': 'album',
                    'TRCK': 'track',
                    'TDRC': 'year',
                    'TCON': 'genre'
                }

                for id3_tag, tag_name in tag_mapping.items():
                    if id3_tag in audio.tags:
                        value = audio.tags[id3_tag]
                        if hasattr(value, 'text'):
                            tags[tag_name] = str(value.text[0])
                        else:
                            tags[tag_name] = str(value)

            return tags
        except Exception as e:
            self.logger.error(f"Error extracting WAV metadata: {e}")
            return {}

    def _extract_wma_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from WMA file"""
        try:
            audio = ASF(file_path)
            tags = {}

            if audio.tags:
                # WMA/ASF tag mapping
                tag_mapping = {
                    'Title': 'title',
                    'Author': 'artist',
                    'Album': 'album',
                    'WM/TrackNumber': 'track',
                    'WM/Year': 'year',
                    'WM/Genre': 'genre',
                    'WM/AlbumArtist': 'albumartist',
                    'WM/PartOfSet': 'discnumber',
                    'Description': 'comment'
                }

                for wma_tag, tag_name in tag_mapping.items():
                    if wma_tag in audio.tags:
                        value = audio.tags[wma_tag]
                        if isinstance(value, list) and value:
                            tags[tag_name] = str(value[0])
                        else:
                            tags[tag_name] = str(value)

            return tags
        except Exception as e:
            self.logger.error(f"Error extracting WMA metadata: {e}")
            return {}

    def apply_metadata(self, source_path: Path, target_path: Path) -> bool:
        """Apply metadata from source file to target file"""
        try:
            # Extract metadata from source
            metadata = self.extract_metadata(source_path)

            if not metadata:
                self.logger.info(f"No metadata found in {source_path.name}")
                return True  # Not an error, just no metadata

            # Apply metadata to target
            return self._apply_metadata_to_file(target_path, metadata)

        except Exception as e:
            self.logger.error(f"Error applying metadata: {e}")
            return False

    def _apply_metadata_to_file(self, target_path: Path, metadata: Dict[str, Any]) -> bool:
        """Apply metadata to target file"""
        suffix = target_path.suffix.lower()

        try:
            if suffix == '.mp3':
                return self._apply_mp3_metadata(target_path, metadata)
            elif suffix in ['.m4a', '.aac']:
                return self._apply_mp4_metadata(target_path, metadata)
            elif suffix == '.flac':
                return self._apply_flac_metadata(target_path, metadata)
            elif suffix == '.opus':
                return self._apply_opus_metadata(target_path, metadata)
            else:
                self.logger.warning(f"Metadata application not supported for format: {suffix}")
                return False
        except Exception as e:
            self.logger.error(f"Error applying metadata to {target_path.name}: {e}")
            return False

    def _apply_mp3_metadata(self, target_path: Path, metadata: Dict[str, Any]) -> bool:
        """Apply metadata to MP3 file"""
        try:
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, TCON, TPE2, TPOS, COMM, APIC

            audio = MP3(target_path)

            # Ensure tags exist
            if audio.tags is None:
                audio.add_tags()

            # Apply text tags
            tag_mapping = {
                'title': TIT2,
                'artist': TPE1,
                'album': TALB,
                'track': TRCK,
                'year': TDRC,
                'genre': TCON,
                'albumartist': TPE2,
                'discnumber': TPOS
            }

            for field, tag_class in tag_mapping.items():
                if field in metadata:
                    audio.tags[tag_class.__name__] = tag_class(encoding=3, text=str(metadata[field]))

            # Add comment
            if 'comment' in metadata:
                audio.tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=str(metadata['comment']))

            # Add artwork if present
            if 'artwork' in metadata:
                audio.tags['APIC:'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=metadata['artwork']
                )

            audio.save()
            return True

        except Exception as e:
            self.logger.error(f"Error applying MP3 metadata: {e}")
            return False

    def _apply_mp4_metadata(self, target_path: Path, metadata: Dict[str, Any]) -> bool:
        """Apply metadata to MP4/M4A file"""
        try:
            audio = MP4(target_path)

            # Apply tags
            tag_mapping = {
                'title': '\xa9nam',
                'artist': '\xa9ART',
                'album': '\xa9alb',
                'track': 'trkn',
                'year': '\xa9day',
                'genre': '\xa9gen',
                'albumartist': 'aART',
                'discnumber': 'disk',
                'comment': '\xa9cmt',
                'lyrics': '\xa9lyr'
            }

            for field, mp4_tag in tag_mapping.items():
                if field in metadata:
                    if field in ['track', 'discnumber']:
                        # Handle track/disc as (current, total) tuple
                        try:
                            value = int(metadata[field])
                            audio.tags[mp4_tag] = [(value, 0)]  # 0 for unknown total
                        except ValueError:
                            audio.tags[mp4_tag] = [(1, 1)]  # Default if parsing fails
                    else:
                        audio.tags[mp4_tag] = [str(metadata[field])]

            # Add artwork if present
            if 'artwork' in metadata:
                audio.tags['covr'] = [metadata['artwork']]

            audio.save()
            return True

        except Exception as e:
            self.logger.error(f"Error applying MP4 metadata: {e}")
            return False

    def _apply_flac_metadata(self, target_path: Path, metadata: Dict[str, Any]) -> bool:
        """Apply metadata to FLAC file"""
        try:
            audio = FLAC(target_path)

            # Apply tags (FLAC uses Vorbis comments)
            tag_mapping = {
                'title': 'TITLE',
                'artist': 'ARTIST',
                'album': 'ALBUM',
                'track': 'TRACKNUMBER',
                'year': 'DATE',
                'genre': 'GENRE',
                'albumartist': 'ALBUMARTIST',
                'discnumber': 'DISCNUMBER',
                'comment': 'COMMENT',
                'lyrics': 'LYRICS'
            }

            for field, flac_tag in tag_mapping.items():
                if field in metadata:
                    audio.tags[flac_tag] = str(metadata[field])

            # Add artwork if present
            if 'artwork' in metadata and hasattr(audio, 'clear_pictures'):
                from mutagen.flac import Picture
                audio.clear_pictures()

                picture = Picture()
                picture.type = 3  # Cover (front)
                picture.mime = 'image/jpeg'
                picture.data = metadata['artwork']
                audio.add_picture(picture)

            audio.save()
            return True

        except Exception as e:
            self.logger.error(f"Error applying FLAC metadata: {e}")
            return False

    def _apply_opus_metadata(self, target_path: Path, metadata: Dict[str, Any]) -> bool:
        """Apply metadata to Opus file"""
        try:
            audio = OggVorbis(target_path)  # Opus uses similar tag structure

            # Apply tags (case-insensitive)
            tag_mapping = {
                'title': 'TITLE',
                'artist': 'ARTIST',
                'album': 'ALBUM',
                'track': 'TRACKNUMBER',
                'year': 'DATE',
                'genre': 'GENRE',
                'albumartist': 'ALBUMARTIST',
                'discnumber': 'DISCNUMBER',
                'comment': 'COMMENT'
            }

            for field, opus_tag in tag_mapping.items():
                if field in metadata:
                    audio.tags[opus_tag] = str(metadata[field])

            audio.save()
            return True

        except Exception as e:
            self.logger.error(f"Error applying Opus metadata: {e}")
            return False

    def get_metadata_summary(self, metadata: Dict[str, Any]) -> str:
        """Get a human-readable summary of metadata"""
        if not metadata:
            return "No metadata found"

        summary_parts = []

        if 'title' in metadata:
            summary_parts.append(f"Title: {metadata['title']}")
        if 'artist' in metadata:
            summary_parts.append(f"Artist: {metadata['artist']}")
        if 'album' in metadata:
            summary_parts.append(f"Album: {metadata['album']}")
        if 'year' in metadata:
            summary_parts.append(f"Year: {metadata['year']}")
        if 'genre' in metadata:
            summary_parts.append(f"Genre: {metadata['genre']}")

        return " | ".join(summary_parts) if summary_parts else "Limited metadata"