#!/usr/bin/env python3
"""
YoYakTube 영상 자막 추출 CLI

Usage:
    python -m cli.yyt_transcript <video_url_or_id> [options]
    
Examples:
    python -m cli.yyt_transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python -m cli.yyt_transcript dQw4w9WgXcQ --languages ko,en,ja
    python -m cli.yyt_transcript dQw4w9WgXcQ --format srt --output transcript.srt
    python -m cli.yyt_transcript dQw4w9WgXcQ --timestamps --format json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 부모 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from yoyaktube.transcript import collect_transcript_entries, collect_transcript
from yoyaktube.utils import extract_video_id


def format_timestamp(seconds: float) -> str:
    """초를 SRT 타임스탬프 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')


def format_as_srt(entries: List[Dict]) -> str:
    """자막 엔트리를 SRT 형식으로 변환"""
    srt_content = []
    
    for i, entry in enumerate(entries, 1):
        start = entry['start']
        duration = entry.get('duration', 0)
        end = start + duration
        
        start_time = format_timestamp(start)
        end_time = format_timestamp(end)
        
        srt_content.append(f"{i}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(entry['text'])
        srt_content.append("")  # 빈 줄
    
    return '\n'.join(srt_content)


def format_as_vtt(entries: List[Dict]) -> str:
    """자막 엔트리를 VTT 형식으로 변환"""
    vtt_content = ["WEBVTT", ""]
    
    for entry in entries:
        start = entry['start']
        duration = entry.get('duration', 0)
        end = start + duration
        
        start_time = format_timestamp(start).replace(',', '.')
        end_time = format_timestamp(end).replace(',', '.')
        
        vtt_content.append(f"{start_time} --> {end_time}")
        vtt_content.append(entry['text'])
        vtt_content.append("")
    
    return '\n'.join(vtt_content)


def format_as_text(entries: List[Dict], include_timestamps: bool = False) -> str:
    """자막 엔트리를 텍스트 형식으로 변환"""
    if include_timestamps:
        text_lines = []
        for entry in entries:
            timestamp = f"[{int(entry['start']//60):02d}:{int(entry['start']%60):02d}]"
            text_lines.append(f"{timestamp} {entry['text']}")
        return '\n'.join(text_lines)
    else:
        return '\n'.join(entry['text'] for entry in entries)


def extract_transcript(
    video_id: str,
    languages: List[str] = None,
    format_type: str = 'text',
    include_timestamps: bool = False
):
    """
    자막을 추출하고 지정된 형식으로 변환
    
    Returns:
        (content, detected_language, error_message)
    """
    if languages is None:
        languages = ['ko', 'en', 'ja']
    
    try:
        if format_type in ['srt', 'vtt', 'json'] or include_timestamps:
            # 타임스탬프가 필요한 경우
            result = collect_transcript_entries(video_id, languages)
            if not result:
                return "", "", "자막을 찾을 수 없습니다."
            
            entries, detected_lang = result
            
            if format_type == 'srt':
                content = format_as_srt(entries)
            elif format_type == 'vtt':
                content = format_as_vtt(entries)
            elif format_type == 'json':
                content = json.dumps({
                    'video_id': video_id,
                    'language': detected_lang,
                    'entries': entries
                }, ensure_ascii=False, indent=2)
            else:  # text with timestamps
                content = format_as_text(entries, include_timestamps)
            
        else:
            # 일반 텍스트만 필요한 경우
            result = collect_transcript(video_id, languages)
            if not result:
                return "", "", "자막을 찾을 수 없습니다."
            
            text, detected_lang = result
            content = text
        
        return content, detected_lang, None
        
    except Exception as e:
        return "", "", str(e)


def main():
    parser = argparse.ArgumentParser(
        description='YouTube 영상의 자막을 추출합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('video', help='YouTube 영상 URL 또는 영상 ID')
    parser.add_argument(
        '--languages', '-l',
        default='ko,en,ja',
        help='언어 우선순위 (쉼표로 구분, 기본값: ko,en,ja)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'srt', 'vtt', 'json'],
        default='text',
        help='출력 형식 (기본값: text)'
    )
    parser.add_argument(
        '--timestamps', '-t',
        action='store_true',
        help='텍스트 형식에 타임스탬프 포함'
    )
    parser.add_argument('--output', '-o', help='결과 저장 파일명')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    try:
        # 영상 ID 추출
        video_id = extract_video_id(args.video)
        if not video_id:
            if len(args.video) == 11:  # 영상 ID 형태인 경우
                video_id = args.video
            else:
                raise ValueError("올바른 YouTube URL 또는 영상 ID를 입력하세요.")
        
        languages = [lang.strip() for lang in args.languages.split(',')]
        
        if args.verbose:
            print(f"영상 ID: {video_id}", file=sys.stderr)
            print(f"언어 우선순위: {languages}", file=sys.stderr)
            print(f"형식: {args.format}", file=sys.stderr)
            print("자막을 추출하는 중...", file=sys.stderr)
        
        content, detected_lang, error = extract_transcript(
            video_id, languages, args.format, args.timestamps
        )
        
        if error:
            print(f"오류: {error}", file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print(f"감지된 언어: {detected_lang}", file=sys.stderr)
            print(f"자막 길이: {len(content)} 문자", file=sys.stderr)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(content)
            if args.verbose:
                print(f"결과가 {args.output}에 저장되었습니다.", file=sys.stderr)
        else:
            print(content)
    
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()