"""
YouTube transcript extraction module

Provides functions to extract transcripts from YouTube videos
using the youtube-transcript-api library.
"""

from typing import Optional, List, Dict, Tuple
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def collect_transcript(
    video_id: str, 
    languages: List[str] = None
) -> Optional[Tuple[str, str]]:
    """
    Extract transcript text from YouTube video.
    
    Args:
        video_id: YouTube video ID
        languages: Preferred language order (default: ["ko", "en", "ja"])
        
    Returns:
        Tuple of (transcript_text, language) or None if not available
    """
    if not video_id:
        return None
    
    if languages is None:
        languages = ["ko", "en", "ja"]
    
    try:
        # Get transcript list
        transcript_list = YouTubeTranscriptApi().list(video_id)
        
        # Try to find transcript in preferred language order
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang])
                entries = transcript.fetch()
                
                # Skip if transcript is empty
                if not entries:
                    continue
                
                # Combine all text entries
                text_parts = []
                for entry in entries:
                    if hasattr(entry, 'text'):
                        text_parts.append(entry.text.strip())
                    elif isinstance(entry, dict) and 'text' in entry:
                        text_parts.append(entry['text'].strip())
                
                transcript_text = ' '.join(text_parts).strip()
                
                if transcript_text:
                    return transcript_text, transcript.language_code
                    
            except NoTranscriptFound:
                continue
        
        return None
        
    except (TranscriptsDisabled, Exception):
        return None


def collect_transcript_entries(
    video_id: str,
    languages: List[str] = None
) -> Optional[Tuple[List[Dict], str]]:
    """
    Extract transcript entries with timestamps from YouTube video.
    
    Args:
        video_id: YouTube video ID
        languages: Preferred language order (default: ["ko", "en", "ja"])
        
    Returns:
        Tuple of (transcript_entries, language) or None if not available
        Each entry contains: {"start": float, "duration": float, "text": str}
    """
    if not video_id:
        return None
    
    if languages is None:
        languages = ["ko", "en", "ja"]
    
    try:
        # Get transcript list
        transcript_list = YouTubeTranscriptApi().list(video_id)
        
        # Try to find transcript in preferred language order
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang])
                entries = transcript.fetch()
                
                # Skip if transcript is empty
                if not entries:
                    continue
                
                # Process entries and validate required fields
                processed_entries = []
                for entry in entries:
                    try:
                        # Handle both object attributes and dict access
                        if hasattr(entry, 'start') and hasattr(entry, 'duration') and hasattr(entry, 'text'):
                            # Object-style access
                            start = float(entry.start)
                            duration = float(entry.duration)
                            text = str(entry.text).strip()
                        elif isinstance(entry, dict):
                            # Dict-style access
                            start = float(entry.get('start', 0))
                            duration = float(entry.get('duration', 0))
                            text = str(entry.get('text', '')).strip()
                        else:
                            continue
                        
                        # Skip entries with missing required fields
                        if text:
                            processed_entries.append({
                                "start": start,
                                "duration": duration,
                                "text": text
                            })
                            
                    except (ValueError, TypeError, KeyError):
                        # Skip malformed entries
                        continue
                
                if processed_entries:
                    return processed_entries, transcript.language_code
                    
            except NoTranscriptFound:
                continue
        
        return None
        
    except (TranscriptsDisabled, Exception):
        return None