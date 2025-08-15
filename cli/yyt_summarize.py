#!/usr/bin/env python3
"""
YoYakTube 자막 요약 CLI

Usage:
    python -m cli.yyt_summarize [input_source] [options]
    
Examples:
    # 영상 URL로 요약
    python -m cli.yyt_summarize "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # 파일에서 자막 읽어서 요약
    python -m cli.yyt_summarize --file transcript.txt
    
    # 표준 입력에서 자막 읽어서 요약
    cat transcript.txt | python -m cli.yyt_summarize --stdin
    
    # AI 모델 지정
    python -m cli.yyt_summarize video_url --provider openai --model gpt-5-mini
    
    # 결과를 파일로 저장
    python -m cli.yyt_summarize video_url --output summary.md
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# 같은 디렉토리의 core 모듈 import
from .core import (
    ChatMessage, get_or_create_llm, collect_transcript, collect_transcript_entries,
    fetch_video_metadata, extract_video_id, build_llm_summary_context, get_config,
    SYS_KO, FULL_SUMMARY_PROMPT
)


def get_transcript_from_video(video_input: str, languages: list = None):
    """영상에서 자막과 메타데이터를 추출"""
    if languages is None:
        languages = ['ko', 'en', 'ja']
    
    video_id = extract_video_id(video_input)
    if not video_id:
        if len(video_input) == 11:
            video_id = video_input
        else:
            raise ValueError("올바른 YouTube URL 또는 영상 ID를 입력하세요.")
    
    # 자막 추출
    transcript_result = collect_transcript(video_id, languages)
    if not transcript_result:
        raise ValueError("자막을 찾을 수 없습니다.")
    
    transcript_text, _ = transcript_result
    
    # 타임스탬프 엔트리 추출 (선택적)
    entries_result = collect_transcript_entries(video_id, languages)
    entries = entries_result[0] if entries_result else None
    
    # 메타데이터 추출
    try:
        metadata = fetch_video_metadata(video_id)
    except Exception as e:
        print(f"메타데이터 추출 실패: {e}", file=sys.stderr)
        metadata = None
    
    return transcript_text, metadata, entries


def read_transcript_from_file(file_path: str) -> str:
    """파일에서 자막을 읽음"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"파일을 읽을 수 없습니다: {e}")


def read_transcript_from_stdin() -> str:
    """표준 입력에서 자막을 읽음"""
    try:
        return sys.stdin.read().strip()
    except Exception as e:
        raise ValueError(f"표준 입력을 읽을 수 없습니다: {e}")


def create_llm_client(provider: str = None, model: str = None):
    """LLM 클라이언트를 생성"""
    import os
    
    config = get_config()
    
    # 기본값 설정
    if not provider:
        providers = config.get('providers', ['openai', 'gemini', 'ollama'])
        provider = providers[0] if providers else 'openai'
    
    if not model:
        model_map = {
            'openai': 'gpt-5-mini',
            'gemini': 'gemini-2.5-flash',
            'ollama': 'llama2'
        }
        model = model_map.get(provider, 'gpt-5-mini')
    
    # API 키 정보 가져오기
    openai_key = os.getenv('OPENAI_API_KEY', '')
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    
    return get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)


def summarize_transcript(
    transcript: str,
    metadata: dict = None,
    entries: list = None,
    provider: str = None,
    model: str = None,
    temperature: float = 0.2
) -> str:
    """자막을 요약"""
    
    # LLM 클라이언트 생성
    llm = create_llm_client(provider, model)
    
    # 컨텍스트 구성
    if metadata and entries:
        source_url = metadata.get('webpage_url')
        duration_sec = metadata.get('duration')
        upload_date = metadata.get('upload_date')
        
        enriched_context = build_llm_summary_context(
            source_url=source_url,
            duration_sec=duration_sec,
            upload_date=upload_date,
            transcript_entries=entries,
            plain_transcript=transcript
        )
    else:
        enriched_context = transcript
    
    # 요약 생성
    messages = [
        ChatMessage(role="system", content=SYS_KO),
        ChatMessage(role="user", content=FULL_SUMMARY_PROMPT.format(transcript=enriched_context))
    ]
    
    response = llm.chat(messages, temperature=temperature)
    return response.content


def main():
    parser = argparse.ArgumentParser(
        description='자막을 AI로 요약합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # 입력 소스 (상호 배타적)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('video', nargs='?', help='YouTube 영상 URL 또는 영상 ID')
    input_group.add_argument('--file', '-f', help='자막 텍스트 파일 경로')
    input_group.add_argument('--stdin', action='store_true', help='표준 입력에서 자막 읽기')
    
    # AI 모델 설정
    parser.add_argument('--provider', choices=['openai', 'gemini', 'ollama'], help='AI 제공자')
    parser.add_argument('--model', help='사용할 모델명')
    parser.add_argument('--temperature', type=float, default=0.2, help='생성 온도 (기본값: 0.2)')
    
    # 출력 설정
    parser.add_argument('--output', '-o', help='결과 저장 파일명 (.md 권장)')
    parser.add_argument('--format', choices=['markdown', 'text'], default='markdown', help='출력 형식')
    parser.add_argument('--languages', default='ko,en,ja', help='자막 언어 우선순위 (쉼표로 구분)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    # 입력 소스 확인
    if not any([args.video, args.file, args.stdin]):
        parser.error("영상 URL, 파일 경로, 또는 --stdin 중 하나를 지정해야 합니다.")
    
    try:
        # 자막 추출
        transcript = None
        metadata = None
        entries = None
        
        if args.video:
            if args.verbose:
                print("영상에서 자막을 추출하는 중...", file=sys.stderr)
            
            languages = [lang.strip() for lang in args.languages.split(',')]
            transcript, metadata, entries = get_transcript_from_video(args.video, languages)
            
            if args.verbose and metadata:
                print(f"제목: {metadata.get('title', 'Unknown')}", file=sys.stderr)
                print(f"채널: {metadata.get('uploader', 'Unknown')}", file=sys.stderr)
                print(f"길이: {metadata.get('duration', 0)}초", file=sys.stderr)
        
        elif args.file:
            if args.verbose:
                print(f"파일에서 자막을 읽는 중: {args.file}", file=sys.stderr)
            transcript = read_transcript_from_file(args.file)
        
        elif args.stdin:
            if args.verbose:
                print("표준 입력에서 자막을 읽는 중...", file=sys.stderr)
            transcript = read_transcript_from_stdin()
        
        if not transcript:
            raise ValueError("자막을 가져올 수 없습니다.")
        
        if args.verbose:
            print(f"자막 길이: {len(transcript)} 문자", file=sys.stderr)
            print(f"AI 제공자: {args.provider or '자동'}", file=sys.stderr)
            print(f"모델: {args.model or '자동'}", file=sys.stderr)
            print("요약을 생성하는 중...", file=sys.stderr)
        
        # 요약 생성
        summary = summarize_transcript(
            transcript, metadata, entries, 
            args.provider, args.model, args.temperature
        )
        
        # 출력 형식 처리
        if args.format == 'markdown' and metadata:
            # 메타데이터가 있으면 마크다운 형식으로 포맷
            result = create_summary_markdown(summary, metadata)
        else:
            result = summary
        
        # 결과 출력
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            if args.verbose:
                print(f"결과가 {args.output}에 저장되었습니다.", file=sys.stderr)
        else:
            print(result)
    
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()