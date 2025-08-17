import pytest
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any, Optional, Tuple


@pytest.fixture
def sample_video_id():
    """Real YouTube video ID for testing"""
    return "sJPgXV350ug"


@pytest.fixture  
def sample_video_urls():
    """Sample YouTube URLs in various formats using real video"""
    return {
        "watch": "https://www.youtube.com/watch?v=sJPgXV350ug",
        "youtu_be": "https://youtu.be/sJPgXV350ug",
        "shorts": "https://www.youtube.com/shorts/sJPgXV350ug",
        "with_params": "https://www.youtube.com/watch?v=sJPgXV350ug&t=30s",
        "mobile": "https://m.youtube.com/watch?v=sJPgXV350ug"
    }


@pytest.fixture
def invalid_video_urls():
    """Invalid YouTube URLs for error testing"""
    return [
        "https://www.youtube.com/watch?v=invalid",
        "https://not-youtube.com/watch?v=sJPgXV350ug",
        "not-a-url",
        "",
        None
    ]


@pytest.fixture
def sample_video_metadata():
    """Expected video metadata structure"""
    return {
        "id": "sJPgXV350ug",
        "title": "Sample Video Title",
        "uploader": "Sample Channel",
        "uploader_id": "SampleChannelID",
        "upload_date": "20231201",
        "duration": 300,
        "view_count": 1000000,
        "like_count": 50000,
        "description": "This is a sample video description for testing purposes.",
        "thumbnail": "https://i.ytimg.com/vi/sJPgXV350ug/maxresdefault.jpg",
        "webpage_url": "https://www.youtube.com/watch?v=sJPgXV350ug"
    }


@pytest.fixture
def sample_transcript_text():
    """Sample plain transcript text"""
    return """안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다. 
테스트는 소프트웨어 개발에서 매우 중요한 부분입니다.
단위 테스트, 통합 테스트, 그리고 엔드투엔드 테스트가 있습니다.
각각의 테스트는 서로 다른 목적을 가지고 있습니다."""


@pytest.fixture
def sample_transcript_entries():
    """Sample transcript entries with timestamps"""
    return [
        {"start": 0.0, "duration": 4.5, "text": "안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다."},
        {"start": 4.5, "duration": 5.2, "text": "테스트는 소프트웨어 개발에서 매우 중요한 부분입니다."},
        {"start": 9.7, "duration": 6.1, "text": "단위 테스트, 통합 테스트, 그리고 엔드투엔드 테스트가 있습니다."},
        {"start": 15.8, "duration": 4.8, "text": "각각의 테스트는 서로 다른 목적을 가지고 있습니다."}
    ]


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for LLM testing"""
    return [
        {"role": "user", "content": "이 영상의 주요 내용은 무엇인가요?"},
        {"role": "assistant", "content": "이 영상은 소프트웨어 테스트의 중요성과 다양한 테스트 유형에 대해 설명합니다."}
    ]


@pytest.fixture
def sample_chat_response():
    """Sample OpenAI chat response"""
    return {
        "content": "이 영상은 소프트웨어 개발에서의 테스트 방법론을 다루며, 단위 테스트부터 통합 테스트까지 다양한 테스트 기법을 설명합니다.",
        "usage": {"prompt_tokens": 200, "completion_tokens": 50, "total_tokens": 250}
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = Mock()
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "이 영상은 테스트 방법론에 대한 포괄적인 설명을 제공합니다."
    response.usage = Mock()
    response.usage.prompt_tokens = 150
    response.usage.completion_tokens = 30
    response.usage.total_tokens = 180
    client.chat.completions.create.return_value = response
    return client


@pytest.fixture
def api_keys():
    """API keys for testing (OpenAI only)"""
    return {
        "openai": "sk-test-openai-key-1234567890abcdef"
    }


@pytest.fixture
def temp_transcript_file(tmp_path, sample_transcript_text):
    """Create a temporary transcript file for testing"""
    file_path = tmp_path / "test_transcript.txt"
    file_path.write_text(sample_transcript_text, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def temp_json_file(tmp_path, sample_transcript_entries):
    """Create a temporary JSON file for testing"""
    import json
    file_path = tmp_path / "test_transcript.json"
    file_path.write_text(json.dumps(sample_transcript_entries, ensure_ascii=False), encoding='utf-8')
    return str(file_path)


@pytest.fixture
def temp_srt_file(tmp_path):
    """Create a temporary SRT file for testing"""
    srt_content = """1
00:00:00,000 --> 00:00:04,500
안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다.

2
00:00:04,500 --> 00:00:09,700
테스트는 소프트웨어 개발에서 매우 중요한 부분입니다.

3
00:00:09,700 --> 00:00:15,800
단위 테스트, 통합 테스트, 그리고 엔드투엔드 테스트가 있습니다.
"""
    file_path = tmp_path / "test_transcript.srt"
    file_path.write_text(srt_content, encoding='utf-8')
    return str(file_path)


@pytest.fixture
def mock_youtube_transcript_api():
    """Mock youtube_transcript_api for testing (올바른 API 구조)"""
    # Mock FetchedTranscriptSnippet 클래스
    class MockSnippet:
        def __init__(self, text, start, duration):
            self.text = text
            self.start = start
            self.duration = duration
        
        def __getitem__(self, key):
            return getattr(self, key)
        
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    # Mock FetchedTranscript 클래스 (리스트처럼 동작)
    class MockFetchedTranscript(list):
        def __init__(self, snippets, video_id, language_code, language, is_generated):
            super().__init__(snippets)
            self.video_id = video_id
            self.language_code = language_code
            self.language = language
            self.is_generated = is_generated
    
    # Mock Transcript 클래스
    mock_transcript = Mock()
    mock_transcript.language_code = "ko"
    mock_transcript.language = "Korean (auto-generated)"
    mock_transcript.is_generated = True
    mock_transcript.video_id = "sJPgXV350ug"
    mock_transcript.is_translatable = True
    
    # Mock fetch 메서드가 FetchedTranscript를 반환하도록 설정
    mock_snippets = [
        MockSnippet("안녕하세요, 오늘은 테스트에 대해 이야기해보겠습니다.", 0.0, 4.5),
        MockSnippet("테스트는 소프트웨어 개발에서 매우 중요한 부분입니다.", 4.5, 5.2)
    ]
    mock_fetched_transcript = MockFetchedTranscript(
        mock_snippets, "sJPgXV350ug", "ko", "Korean (auto-generated)", True
    )
    mock_transcript.fetch.return_value = mock_fetched_transcript
    
    # Mock TranscriptList 클래스
    mock_transcript_list = Mock()
    mock_transcript_list.__iter__.return_value = [mock_transcript]
    mock_transcript_list.find_transcript.return_value = mock_transcript
    mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
    mock_transcript_list.find_generated_transcript.return_value = mock_transcript
    
    # Mock YouTubeTranscriptApi 클래스
    mock_api = Mock()
    mock_api_instance = Mock()
    mock_api_instance.list.return_value = mock_transcript_list
    mock_api.return_value = mock_api_instance
    
    return mock_api


@pytest.fixture
def mock_yt_dlp():
    """Mock yt-dlp for testing"""
    mock_ydl = Mock()
    mock_ydl_instance = Mock()
    mock_ydl_instance.extract_info.return_value = {
        "id": "sJPgXV350ug",
        "title": "테스트 방법론 완벽 가이드",
        "uploader": "개발자 채널",
        "uploader_id": "DeveloperChannel",
        "upload_date": "20231201",
        "duration": 300,
        "view_count": 1000000,
        "like_count": 50000,
        "description": "소프트웨어 테스트의 모든 것을 다루는 완벽한 가이드입니다.",
        "webpage_url": "https://www.youtube.com/watch?v=sJPgXV350ug"
    }
    mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
    return mock_ydl


@pytest.fixture
def env_vars():
    """Set up environment variables for testing"""
    original_env = os.environ.copy()
    test_env = {
        "OPENAI_API_KEY": "sk-test-openai-key-1234567890abcdef",
        "YYT_PROVIDERS": "openai",
        "YYT_CONFIG": ""
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Cleanup
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def cli_runner():
    """Click CLI test runner"""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for CLI testing"""
    import subprocess
    original_run = subprocess.run
    
    def mock_run(*args, **kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = "Mock CLI output"
        result.stderr = ""
        return result
    
    subprocess.run = mock_run
    yield mock_run
    subprocess.run = original_run


@pytest.fixture
def sample_summary_context():
    """Sample context for LLM summary generation"""
    return {
        "source_url": "https://www.youtube.com/watch?v=sJPgXV350ug",
        "duration_sec": 300.0,
        "upload_date": "2023-12-01",
        "title": "테스트 방법론 완벽 가이드",
        "uploader": "개발자 채널"
    }


@pytest.fixture
def expected_summary_output():
    """Expected summary output format"""
    return """# 테스트 방법론 완벽 가이드

**채널**: 개발자 채널  
**업로드 날짜**: 2023-12-01  
**재생시간**: 5:00  
**원본 링크**: https://www.youtube.com/watch?v=sJPgXV350ug

## 요약

이 영상은 소프트웨어 개발에서의 테스트 방법론에 대한 포괄적인 설명을 제공합니다.

### 주요 내용
- 단위 테스트의 중요성과 작성 방법
- 통합 테스트를 통한 모듈 간 상호작용 검증
- 엔드투엔드 테스트로 전체 시스템 검증

### 핵심 포인트
- [00:00] 테스트의 기본 개념 소개
- [04:30] 다양한 테스트 유형 설명
- [09:42] 실제 테스트 코드 작성 예시"""