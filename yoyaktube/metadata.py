"""
YouTube video metadata extraction module

Provides functions to extract video metadata using yt-dlp.
"""

from typing import Optional, Dict, Any
import yt_dlp
import logging


def fetch_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract video metadata using yt-dlp.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary containing video metadata or None if extraction fails
        
    Metadata includes:
        - title: Video title
        - uploader: Channel name
        - duration: Duration in seconds
        - view_count: View count
        - upload_date: Upload date (YYYYMMDD format)
        - description: Video description
        - thumbnail: Thumbnail URL
        - webpage_url: Full YouTube URL
    """
    if not video_id:
        return None
    
    # Construct YouTube URL
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Configure yt-dlp options
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extractaudio': False,
        'format': 'worst',  # Don't download video, just extract metadata
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata without downloading
            info = ydl.extract_info(video_url, download=False)
            
            if not info:
                return None
            
            # Extract relevant metadata fields
            metadata = {
                'id': info.get('id'),
                'title': info.get('title'),
                'uploader': info.get('uploader') or info.get('channel'),
                'duration': info.get('duration'),
                'view_count': info.get('view_count'),
                'upload_date': info.get('upload_date'),
                'description': info.get('description'),
                'thumbnail': info.get('thumbnail'),
                'webpage_url': info.get('webpage_url'),
                'channel_id': info.get('channel_id'),
                'channel_url': info.get('channel_url'),
                'tags': info.get('tags', []),
                'categories': info.get('categories', []),
                'like_count': info.get('like_count'),
                'comment_count': info.get('comment_count')
            }
            
            # Clean up None values and ensure basic fields exist
            cleaned_metadata = {}
            for key, value in metadata.items():
                if value is not None:
                    cleaned_metadata[key] = value
            
            # Ensure we have at least an ID
            if 'id' not in cleaned_metadata:
                cleaned_metadata['id'] = video_id
            
            return cleaned_metadata
            
    except Exception as e:
        # Log error but don't raise exception
        logging.debug(f"Failed to extract metadata for video {video_id}: {e}")
        return None