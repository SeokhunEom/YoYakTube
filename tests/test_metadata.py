import pytest
from unittest.mock import patch, Mock, MagicMock
import yt_dlp
from typing import Dict, Any, Optional


class TestFetchVideoMetadata:
    """Tests for fetch_video_metadata function"""
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_success(self, mock_yt_dlp, sample_video_id, sample_video_metadata):
        """Test successful metadata extraction"""
        from yoyaktube.metadata import fetch_video_metadata
        
        # Mock yt-dlp context manager
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = sample_video_metadata
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is not None
        assert result["id"] == sample_video_id
        assert result["title"] == sample_video_metadata["title"]
        assert result["uploader"] == sample_video_metadata["uploader"]
        assert result["duration"] == sample_video_metadata["duration"]
        assert result["view_count"] == sample_video_metadata["view_count"]
        
        # Verify yt-dlp was called with correct parameters
        mock_yt_dlp.assert_called_once()
        mock_ydl_instance.extract_info.assert_called_once_with(
            f"https://www.youtube.com/watch?v={sample_video_id}",
            download=False
        )
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_with_minimal_data(self, mock_yt_dlp, sample_video_id):
        """Test metadata extraction with minimal available data"""
        from yoyaktube.metadata import fetch_video_metadata
        
        minimal_metadata = {
            "id": sample_video_id,
            "title": "Test Video",
            "uploader": "Test Channel"
            # Missing optional fields like duration, view_count, etc.
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = minimal_metadata
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is not None
        assert result["id"] == sample_video_id
        assert result["title"] == "Test Video"
        assert result["uploader"] == "Test Channel"
        # Should handle missing fields gracefully
        assert result.get("duration") is None or isinstance(result.get("duration"), (int, float))
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_private_video(self, mock_yt_dlp, sample_video_id):
        """Test handling private video error"""
        from yoyaktube.metadata import fetch_video_metadata
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.side_effect = yt_dlp.DownloadError("Private video")
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is None
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_video_not_found(self, mock_yt_dlp, sample_video_id):
        """Test handling video not found error"""
        from yoyaktube.metadata import fetch_video_metadata
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.side_effect = yt_dlp.DownloadError("Video unavailable")
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is None
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_network_error(self, mock_yt_dlp, sample_video_id):
        """Test handling network error"""
        from yoyaktube.metadata import fetch_video_metadata
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.side_effect = yt_dlp.DownloadError("Network error")
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is None
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_invalid_video_id(self, mock_yt_dlp):
        """Test handling invalid video ID"""
        from yoyaktube.metadata import fetch_video_metadata
        
        invalid_id = "invalid_id"
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.side_effect = yt_dlp.DownloadError("Invalid video ID")
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(invalid_id)
        
        assert result is None
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_empty_video_id(self, mock_yt_dlp):
        """Test handling empty video ID"""
        from yoyaktube.metadata import fetch_video_metadata
        
        result = fetch_video_metadata("")
        
        assert result is None
        # Should not call yt-dlp for empty ID
        mock_yt_dlp.assert_not_called()
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_none_video_id(self, mock_yt_dlp):
        """Test handling None video ID"""
        from yoyaktube.metadata import fetch_video_metadata
        
        result = fetch_video_metadata(None)
        
        assert result is None
        # Should not call yt-dlp for None ID
        mock_yt_dlp.assert_not_called()
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_age_restricted_video(self, mock_yt_dlp, sample_video_id):
        """Test handling age-restricted video"""
        from yoyaktube.metadata import fetch_video_metadata
        
        age_restricted_metadata = {
            "id": sample_video_id,
            "title": "Age Restricted Video",
            "uploader": "Test Channel",
            "age_limit": 18,
            "duration": 120
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = age_restricted_metadata
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is not None
        assert result["id"] == sample_video_id
        assert result["title"] == "Age Restricted Video"
        assert result.get("age_limit") == 18
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_live_stream(self, mock_yt_dlp, sample_video_id):
        """Test handling live stream metadata"""
        from yoyaktube.metadata import fetch_video_metadata
        
        live_stream_metadata = {
            "id": sample_video_id,
            "title": "Live Stream Title",
            "uploader": "Live Channel",
            "is_live": True,
            "duration": None  # Live streams have no fixed duration
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = live_stream_metadata
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is not None
        assert result["id"] == sample_video_id
        assert result["title"] == "Live Stream Title"
        assert result.get("is_live") is True
        assert result.get("duration") is None
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_with_chapters(self, mock_yt_dlp, sample_video_id):
        """Test metadata extraction with video chapters"""
        from yoyaktube.metadata import fetch_video_metadata
        
        metadata_with_chapters = {
            "id": sample_video_id,
            "title": "Video with Chapters",
            "uploader": "Test Channel",
            "duration": 600,
            "chapters": [
                {"start_time": 0, "end_time": 120, "title": "Introduction"},
                {"start_time": 120, "end_time": 300, "title": "Main Content"},
                {"start_time": 300, "end_time": 600, "title": "Conclusion"}
            ]
        }
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = metadata_with_chapters
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is not None
        assert result["id"] == sample_video_id
        assert "chapters" in result
        assert len(result["chapters"]) == 3
        assert result["chapters"][0]["title"] == "Introduction"
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_unexpected_exception(self, mock_yt_dlp, sample_video_id):
        """Test handling unexpected exception during metadata extraction"""
        from yoyaktube.metadata import fetch_video_metadata
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.side_effect = Exception("Unexpected error")
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        result = fetch_video_metadata(sample_video_id)
        
        assert result is None
    
    @patch('yoyaktube.metadata.yt_dlp.YoutubeDL')
    def test_fetch_metadata_ydl_configuration(self, mock_yt_dlp, sample_video_id, sample_video_metadata):
        """Test that yt-dlp is configured correctly"""
        from yoyaktube.metadata import fetch_video_metadata
        
        mock_ydl_instance = Mock()
        mock_ydl_instance.extract_info.return_value = sample_video_metadata
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_yt_dlp.return_value.__exit__.return_value = None
        
        fetch_video_metadata(sample_video_id)
        
        # Verify yt-dlp is configured with appropriate options
        call_args = mock_yt_dlp.call_args
        ydl_opts = call_args[0][0] if call_args and call_args[0] else {}
        
        # Should be configured to not download actual video files
        assert ydl_opts.get("skip_download", True) is True
        # Should have quiet mode enabled for cleaner output
        assert "quiet" in ydl_opts or "verbose" not in ydl_opts