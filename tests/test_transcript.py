import pytest
from unittest.mock import patch, Mock, MagicMock
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from typing import List, Dict, Tuple, Optional


class TestCollectTranscript:
    """Tests for collect_transcript function"""

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_success_korean(self, mock_youtube_api, sample_video_id):
        """Test successful transcript collection in Korean"""
        from Core.transcript import collect_transcript

        # Mock FetchedTranscriptSnippet
        class MockSnippet:
            def __init__(self, text, start, duration):
                self.text = text
                self.start = start
                self.duration = duration

        # Mock successful Korean transcript
        mock_api_instance = Mock()
        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ko"
        mock_transcript.is_generated = False

        mock_snippets = [
            MockSnippet(
                "안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다.", 0.0, 4.5
            ),
            MockSnippet(
                "테스트는 소프트웨어 개발에서 매우 중요한 부분입니다.", 4.5, 5.2
            ),
        ]
        mock_transcript.fetch.return_value = mock_snippets
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_api_instance.list.return_value = mock_transcript_list
        mock_youtube_api.return_value = mock_api_instance

        result = collect_transcript(sample_video_id)

        assert result is not None
        text, language = result
        assert "안녕하세요" in text
        assert "테스트" in text
        assert language == "ko"

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_fallback_to_english(
        self, mock_youtube_api, sample_video_id
    ):
        """Test fallback to English when Korean is not available"""
        from Core.transcript import collect_transcript

        # Mock FetchedTranscriptSnippet
        class MockSnippet:
            def __init__(self, text, start, duration):
                self.text = text
                self.start = start
                self.duration = duration

        # Mock Korean not found, English available
        mock_api_instance = Mock()
        mock_transcript_list = Mock()

        def mock_find_transcript(languages):
            if "ko" in languages:
                raise NoTranscriptFound("No Korean transcript", [], sample_video_id)
            elif "en" in languages:
                mock_transcript = Mock()
                mock_transcript.language_code = "en"
                mock_transcript.is_generated = False
                mock_snippets = [
                    MockSnippet("Hello, today we will talk about testing.", 0.0, 4.5),
                    MockSnippet(
                        "Testing is very important part of software development.",
                        4.5,
                        5.2,
                    ),
                ]
                mock_transcript.fetch.return_value = mock_snippets
                return mock_transcript

        mock_transcript_list.find_transcript.side_effect = mock_find_transcript
        mock_api_instance.list.return_value = mock_transcript_list
        mock_youtube_api.return_value = mock_api_instance

        result = collect_transcript(sample_video_id)

        assert result is not None
        text, language = result
        assert "Hello" in text
        assert "testing" in text
        assert language == "en"

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_custom_languages(
        self, mock_youtube_api, sample_video_id
    ):
        """Test transcript collection with custom language preferences"""
        from Core.transcript import collect_transcript

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ja"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = [
            {
                "start": 0.0,
                "duration": 4.5,
                "text": "こんにちは、今日はテストについて話します。",
            }
        ]
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript(sample_video_id, languages=["ja"])

        assert result is not None
        text, language = result
        assert "こんにちは" in text
        assert language == "ja"

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_no_transcript_available(
        self, mock_youtube_api, sample_video_id
    ):
        """Test when no transcript is available"""
        from Core.transcript import collect_transcript

        mock_youtube_api.list_transcripts.side_effect = TranscriptsDisabled(
            sample_video_id
        )

        result = collect_transcript(sample_video_id)

        assert result is None

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_no_requested_languages(
        self, mock_youtube_api, sample_video_id
    ):
        """Test when requested languages are not available"""
        from Core.transcript import collect_transcript

        mock_transcript_list = Mock()
        mock_transcript_list.find_transcript.side_effect = NoTranscriptFound(
            "No transcript found", [], sample_video_id
        )
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript(sample_video_id, languages=["ko", "en", "ja"])

        assert result is None

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_generated_subtitle(
        self, mock_youtube_api, sample_video_id
    ):
        """Test collecting auto-generated transcript"""
        from Core.transcript import collect_transcript

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ko"
        mock_transcript.is_generated = True  # Auto-generated
        mock_transcript.fetch.return_value = [
            {"start": 0.0, "duration": 4.5, "text": "안녕하세요 자동 생성된 자막입니다"}
        ]
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript(sample_video_id)

        assert result is not None
        text, language = result
        assert "자동 생성된" in text
        assert language == "ko"

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_empty_transcript(
        self, mock_youtube_api, sample_video_id
    ):
        """Test handling empty transcript"""
        from Core.transcript import collect_transcript

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ko"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = []  # Empty transcript
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript(sample_video_id)

        assert result is None


class TestCollectTranscriptEntries:
    """Tests for collect_transcript_entries function"""

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_entries_success(
        self, mock_youtube_api, sample_video_id
    ):
        """Test successful transcript entries collection"""
        from Core.transcript import collect_transcript_entries

        expected_entries = [
            {
                "start": 0.0,
                "duration": 4.5,
                "text": "안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다.",
            },
            {
                "start": 4.5,
                "duration": 5.2,
                "text": "테스트는 소프트웨어 개발에서 매우 중요한 부분입니다.",
            },
            {
                "start": 9.7,
                "duration": 6.1,
                "text": "단위 테스트, 통합 테스트, 그리고 엔드투엔드 테스트가 있습니다.",
            },
        ]

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ko"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = expected_entries
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript_entries(sample_video_id)

        assert result is not None
        entries, language = result
        assert len(entries) == 3
        assert entries[0]["start"] == 0.0
        assert entries[0]["duration"] == 4.5
        assert "안녕하세요" in entries[0]["text"]
        assert language == "ko"

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_entries_with_custom_languages(
        self, mock_youtube_api, sample_video_id
    ):
        """Test transcript entries collection with custom languages"""
        from Core.transcript import collect_transcript_entries

        expected_entries = [
            {
                "start": 0.0,
                "duration": 4.5,
                "text": "Hello, today we will talk about testing.",
            }
        ]

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "en"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = expected_entries
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript_entries(sample_video_id, languages=["en"])

        assert result is not None
        entries, language = result
        assert len(entries) == 1
        assert "Hello" in entries[0]["text"]
        assert language == "en"

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_entries_no_transcript(
        self, mock_youtube_api, sample_video_id
    ):
        """Test when no transcript entries are available"""
        from Core.transcript import collect_transcript_entries

        mock_youtube_api.list_transcripts.side_effect = TranscriptsDisabled(
            sample_video_id
        )

        result = collect_transcript_entries(sample_video_id)

        assert result is None

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_entries_empty_list(
        self, mock_youtube_api, sample_video_id
    ):
        """Test handling empty transcript entries list"""
        from Core.transcript import collect_transcript_entries

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ko"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = []
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript_entries(sample_video_id)

        assert result is None

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_entries_malformed_data(
        self, mock_youtube_api, sample_video_id
    ):
        """Test handling malformed transcript entry data"""
        from Core.transcript import collect_transcript_entries

        # Missing required fields
        malformed_entries = [
            {"start": 0.0, "text": "Missing duration field"},
            {"duration": 4.5, "text": "Missing start field"},
            {"start": 9.7, "duration": 3.0},  # Missing text field
        ]

        mock_transcript_list = Mock()
        mock_transcript = Mock()
        mock_transcript.language_code = "ko"
        mock_transcript.is_generated = False
        mock_transcript.fetch.return_value = malformed_entries
        mock_transcript_list.find_transcript.return_value = mock_transcript
        mock_youtube_api.list_transcripts.return_value = mock_transcript_list

        result = collect_transcript_entries(sample_video_id)

        # Should handle malformed data gracefully
        # Implementation should either filter out bad entries or return None
        if result is not None:
            entries, language = result
            # Verify that returned entries have all required fields
            for entry in entries:
                assert "start" in entry
                assert "duration" in entry
                assert "text" in entry

    @patch("yoyaktube.transcript.YouTubeTranscriptApi")
    def test_collect_transcript_entries_invalid_video_id(self, mock_youtube_api):
        """Test handling invalid video ID"""
        from Core.transcript import collect_transcript_entries

        invalid_id = "invalid_video_id"
        mock_youtube_api.list_transcripts.side_effect = Exception("Invalid video ID")

        result = collect_transcript_entries(invalid_id)

        assert result is None
