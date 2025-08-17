import pytest
import json
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner


class TestTranscriptCLI:
    """Tests for transcript CLI commands"""
    
    @patch('cli.yyt_transcript.collect_transcript')
    def test_transcript_command_basic(self, mock_collect_transcript, cli_runner, sample_video_id):
        """Test basic transcript extraction command"""
        # Mock successful transcript collection
        mock_collect_transcript.return_value = ("안녕하세요, 테스트입니다.", "ko")
        
        # Import after mocking to avoid import-time execution
        from cli.yyt_transcript import main as transcript_main
        
        result = cli_runner.invoke(transcript_main, [f"https://www.youtube.com/watch?v={sample_video_id}"])
        
        assert result.exit_code == 0
        assert "안녕하세요" in result.output
        mock_collect_transcript.assert_called_once_with(sample_video_id, ["ko", "en", "ja"])
    
    @patch('cli.yyt_transcript.collect_transcript_entries')
    def test_transcript_command_json_format(self, mock_collect_entries, cli_runner, sample_video_id, tmp_path):
        """Test transcript extraction with JSON format"""
        # Mock transcript entries
        mock_entries = [
            {"start": 0.0, "duration": 4.5, "text": "안녕하세요, 테스트입니다."},
            {"start": 4.5, "duration": 3.2, "text": "JSON 형식으로 출력합니다."}
        ]
        mock_collect_entries.return_value = (mock_entries, "ko")
        
        from cli.yyt_transcript import main as transcript_main
        
        output_file = tmp_path / "transcript.json"
        result = cli_runner.invoke(transcript_main, [
            f"https://www.youtube.com/watch?v={sample_video_id}",
            "--format", "json",
            "--output", str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]["text"] == "안녕하세요, 테스트입니다."
        assert data[1]["text"] == "JSON 형식으로 출력합니다."
    
    @patch('cli.yyt_transcript.collect_transcript_entries')
    def test_transcript_command_srt_format(self, mock_collect_entries, cli_runner, sample_video_id, tmp_path):
        """Test transcript extraction with SRT format"""
        mock_entries = [
            {"start": 0.0, "duration": 4.5, "text": "안녕하세요, 테스트입니다."},
            {"start": 4.5, "duration": 3.2, "text": "SRT 형식으로 출력합니다."}
        ]
        mock_collect_entries.return_value = (mock_entries, "ko")
        
        from cli.yyt_transcript import main as transcript_main
        
        output_file = tmp_path / "transcript.srt"
        result = cli_runner.invoke(transcript_main, [
            f"https://www.youtube.com/watch?v={sample_video_id}",
            "--format", "srt",
            "--output", str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify SRT content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "1\n00:00:00,000 --> 00:00:04,500" in content
        assert "안녕하세요, 테스트입니다." in content
        assert "2\n00:00:04,500 --> 00:00:07,700" in content
        assert "SRT 형식으로 출력합니다." in content
    
    @patch('cli.yyt_transcript.collect_transcript')
    def test_transcript_command_custom_languages(self, mock_collect_transcript, cli_runner, sample_video_id):
        """Test transcript extraction with custom language preferences"""
        mock_collect_transcript.return_value = ("Hello, this is a test.", "en")
        
        from cli.yyt_transcript import main as transcript_main
        
        result = cli_runner.invoke(transcript_main, [
            f"https://www.youtube.com/watch?v={sample_video_id}",
            "--languages", "en,ja"
        ])
        
        assert result.exit_code == 0
        assert "Hello" in result.output
        mock_collect_transcript.assert_called_once_with(sample_video_id, ["en", "ja"])
    
    @patch('cli.yyt_transcript.collect_transcript')
    def test_transcript_command_no_transcript_found(self, mock_collect_transcript, cli_runner, sample_video_id):
        """Test handling when no transcript is found"""
        mock_collect_transcript.return_value = None
        
        from cli.yyt_transcript import main as transcript_main
        
        result = cli_runner.invoke(transcript_main, [f"https://www.youtube.com/watch?v={sample_video_id}"])
        
        assert result.exit_code != 0
        assert "자막을 찾을 수 없습니다" in result.output or "No transcript found" in result.output


class TestSummarizeCLI:
    """Tests for summarize CLI commands"""
    
    @patch('cli.yyt_summarize.get_or_create_llm')
    @patch('cli.yyt_summarize.collect_transcript')
    @patch('cli.yyt_summarize.fetch_video_metadata')
    def test_summarize_command_basic(self, mock_fetch_metadata, mock_collect_transcript, 
                                   mock_get_llm, cli_runner, sample_video_id, sample_video_metadata):
        """Test basic video summarization command"""
        # Mock dependencies
        mock_collect_transcript.return_value = ("테스트 자막 내용입니다.", "ko")
        mock_fetch_metadata.return_value = sample_video_metadata
        
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "# 영상 요약\n\n이 영상은 테스트에 대한 내용입니다.",
            "usage": {"total_tokens": 150}
        }
        mock_get_llm.return_value = mock_llm
        
        from cli.yyt_summarize import main as summarize_main
        
        result = cli_runner.invoke(summarize_main, [
            f"https://www.youtube.com/watch?v={sample_video_id}",
            "--provider", "openai",
            "--model", "gpt-4"
        ])
        
        assert result.exit_code == 0
        assert "영상 요약" in result.output
        assert "테스트" in result.output
        mock_get_llm.assert_called_once()
        mock_llm.chat.assert_called_once()
    
    @patch('cli.yyt_summarize.get_or_create_llm')
    def test_summarize_command_from_file(self, mock_get_llm, cli_runner, temp_transcript_file):
        """Test summarization from transcript file"""
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "# 파일 기반 요약\n\n파일에서 읽은 자막을 요약했습니다.",
            "usage": {"total_tokens": 100}
        }
        mock_get_llm.return_value = mock_llm
        
        from cli.yyt_summarize import main as summarize_main
        
        result = cli_runner.invoke(summarize_main, [
            "--file", temp_transcript_file,
            "--provider", "openai",
            "--model", "gpt-4"
        ])
        
        assert result.exit_code == 0
        assert "파일 기반 요약" in result.output
        mock_llm.chat.assert_called_once()
    
    @patch('cli.yyt_summarize.get_or_create_llm')
    def test_summarize_command_with_output_file(self, mock_get_llm, cli_runner, 
                                              sample_video_id, tmp_path):
        """Test summarization with output file"""
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "# 저장된 요약\n\n이 요약은 파일로 저장됩니다.",
            "usage": {"total_tokens": 120}
        }
        mock_get_llm.return_value = mock_llm
        
        with patch('cli.yyt_summarize.collect_transcript') as mock_transcript:
            mock_transcript.return_value = ("테스트 자막", "ko")
            
            from cli.yyt_summarize import main as summarize_main
            
            output_file = tmp_path / "summary.md"
            result = cli_runner.invoke(summarize_main, [
                f"https://www.youtube.com/watch?v={sample_video_id}",
                "--provider", "openai",
                "--model", "gpt-4",
                "--output", str(output_file)
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "저장된 요약" in content


class TestChatCLI:
    """Tests for chat CLI commands"""
    
    @patch('cli.yyt_chat.get_or_create_llm')
    @patch('cli.yyt_chat.collect_transcript')
    def test_chat_command_single_question(self, mock_collect_transcript, mock_get_llm, 
                                        cli_runner, sample_video_id):
        """Test chat command with single question"""
        mock_collect_transcript.return_value = ("테스트 관련 자막 내용입니다.", "ko")
        
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "이 영상은 소프트웨어 테스트 방법론에 대해 설명합니다.",
            "usage": {"total_tokens": 80}
        }
        mock_get_llm.return_value = mock_llm
        
        from cli.yyt_chat import main as chat_main
        
        result = cli_runner.invoke(chat_main, [
            f"https://www.youtube.com/watch?v={sample_video_id}",
            "--question", "이 영상의 주제는 무엇인가요?",
            "--provider", "openai",
            "--model", "gpt-4"
        ])
        
        assert result.exit_code == 0
        assert "테스트 방법론" in result.output
        mock_llm.chat.assert_called_once()
    
    @patch('cli.yyt_chat.get_or_create_llm')
    def test_chat_command_from_file(self, mock_get_llm, cli_runner, temp_transcript_file):
        """Test chat command using transcript file"""
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "파일에서 읽은 자막을 바탕으로 답변드립니다.",
            "usage": {"total_tokens": 90}
        }
        mock_get_llm.return_value = mock_llm
        
        from cli.yyt_chat import main as chat_main
        
        result = cli_runner.invoke(chat_main, [
            "--file", temp_transcript_file,
            "--question", "자막의 내용은 무엇인가요?",
            "--provider", "openai",
            "--model", "gpt-4"
        ])
        
        assert result.exit_code == 0
        assert "답변드립니다" in result.output


class TestAiCLI:
    """Tests for AI management CLI commands"""
    
    @patch('cli.yyt_ai.get_or_create_llm')
    def test_ai_test_command_success(self, mock_get_llm, cli_runner, api_keys):
        """Test AI model connection test - success"""
        mock_llm = Mock()
        mock_llm.chat.return_value = {
            "content": "테스트 응답입니다.",
            "usage": {"total_tokens": 20}
        }
        mock_get_llm.return_value = mock_llm
        
        from cli.yyt_ai import main as ai_main
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": api_keys["openai"]}):
            result = cli_runner.invoke(ai_main, [
                "test", "openai", "gpt-4"
            ])
        
        assert result.exit_code == 0
        assert "성공" in result.output or "Success" in result.output
        mock_get_llm.assert_called_once_with(
            provider="openai",
            model="gpt-4",
            openai_key=api_keys["openai"],
            gemini_key="",
            ollama_host=""
        )
    
    @patch('cli.yyt_ai.get_or_create_llm')
    def test_ai_test_command_failure(self, mock_get_llm, cli_runner):
        """Test AI model connection test - failure"""
        mock_get_llm.side_effect = Exception("Connection failed")
        
        from cli.yyt_ai import main as ai_main
        
        result = cli_runner.invoke(ai_main, [
            "test", "openai", "gpt-4"
        ])
        
        assert result.exit_code != 0
        assert "실패" in result.output or "Failed" in result.output
    
    def test_ai_list_command(self, cli_runner):
        """Test AI model list command"""
        from cli.yyt_ai import main as ai_main
        
        result = cli_runner.invoke(ai_main, ["list"])
        
        assert result.exit_code == 0
        assert "openai" in result.output.lower()
        # Should show available OpenAI models
        assert "gpt" in result.output.lower() or "model" in result.output.lower()


class TestMainCLI:
    """Tests for main CLI interface"""
    
    def test_main_cli_help(self, cli_runner):
        """Test main CLI help command"""
        from cli.yyt import main as yyt_main
        
        result = cli_runner.invoke(yyt_main, ["--help"])
        
        assert result.exit_code == 0
        assert "transcript" in result.output
        assert "summarize" in result.output
        assert "chat" in result.output
        assert "ai" in result.output
    
    @patch('cli.yyt.transcript_main')
    def test_main_cli_transcript_subcommand(self, mock_transcript_main, cli_runner, sample_video_id):
        """Test main CLI transcript subcommand delegation"""
        mock_transcript_main.return_value = None
        
        from cli.yyt import main as yyt_main
        
        result = cli_runner.invoke(yyt_main, [
            "transcript", f"https://www.youtube.com/watch?v={sample_video_id}"
        ])
        
        # Should delegate to transcript command
        mock_transcript_main.assert_called_once()
    
    @patch('cli.yyt.summarize_main')
    def test_main_cli_summarize_subcommand(self, mock_summarize_main, cli_runner, sample_video_id):
        """Test main CLI summarize subcommand delegation"""
        mock_summarize_main.return_value = None
        
        from cli.yyt import main as yyt_main
        
        result = cli_runner.invoke(yyt_main, [
            "summarize", f"https://www.youtube.com/watch?v={sample_video_id}"
        ])
        
        # Should delegate to summarize command
        mock_summarize_main.assert_called_once()


class TestCLIErrorHandling:
    """Tests for CLI error handling"""
    
    def test_invalid_video_url(self, cli_runner):
        """Test handling invalid video URL"""
        from cli.yyt_transcript import main as transcript_main
        
        result = cli_runner.invoke(transcript_main, ["invalid-url"])
        
        assert result.exit_code != 0
        assert "잘못된" in result.output or "Invalid" in result.output
    
    def test_missing_api_key(self, cli_runner, sample_video_id):
        """Test handling missing API key"""
        from cli.yyt_summarize import main as summarize_main
        
        with patch.dict(os.environ, {}, clear=True):
            result = cli_runner.invoke(summarize_main, [
                f"https://www.youtube.com/watch?v={sample_video_id}",
                "--provider", "openai",
                "--model", "gpt-4"
            ])
        
        assert result.exit_code != 0
        assert "API" in result.output or "키" in result.output
    
    def test_file_not_found(self, cli_runner):
        """Test handling file not found error"""
        from cli.yyt_summarize import main as summarize_main
        
        result = cli_runner.invoke(summarize_main, [
            "--file", "/nonexistent/file.txt",
            "--provider", "openai",
            "--model", "gpt-4"
        ])
        
        assert result.exit_code != 0
        assert "파일" in result.output or "file" in result.output.lower()