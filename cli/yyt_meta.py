#!/usr/bin/env python3
"""
YoYakTube 영상 메타데이터 추출 CLI

Usage:
    python -m cli.yyt_meta <video_url_or_id> [options]
    
Examples:
    python -m cli.yyt_meta "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python -m cli.yyt_meta dQw4w9WgXcQ --format json --output metadata.json
    python -m cli.yyt_meta dQw4w9WgXcQ --fields title,uploader,duration,view_count
    python -m cli.yyt_meta dQw4w9WgXcQ --table
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# 부모 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from yoyaktube.metadata import fetch_video_metadata
from yoyaktube.utils import extract_video_id, format_hms


def format_metadata_table(metadata: Dict[str, Any]):
    """메타데이터를 테이블 형태로 출력"""
    if not metadata:
        print("메타데이터가 없습니다.")
        return
    
    print("=" * 80)
    print("YouTube 영상 메타데이터")
    print("=" * 80)
    
    # 주요 필드들을 보기 좋게 정리
    fields = [
        ('제목', 'title'),
        ('채널', 'uploader'),
        ('채널 ID', 'uploader_id'),
        ('채널 URL', 'uploader_url'),
        ('영상 ID', 'id'),
        ('영상 URL', 'webpage_url'),
        ('업로드 날짜', 'upload_date'),
        ('재생 시간', 'duration'),
        ('조회수', 'view_count'),
        ('좋아요', 'like_count'),
        ('카테고리', 'category'),
        ('언어', 'language'),
        ('라이센스', 'license'),
        ('태그', 'tags'),
        ('설명', 'description'),
    ]
    
    for label, key in fields:
        value = metadata.get(key)
        if value is None:
            continue
        
        # 값 포맷팅
        if key == 'duration' and isinstance(value, (int, float)):
            value = format_hms(value)
        elif key in ['view_count', 'like_count'] and isinstance(value, int):
            value = f"{value:,}"
        elif key == 'upload_date' and isinstance(value, str) and len(value) == 8:
            try:
                date_obj = datetime.strptime(value, '%Y%m%d')
                value = date_obj.strftime('%Y-%m-%d')
            except:
                pass
        elif key == 'tags' and isinstance(value, list):
            value = ', '.join(value[:10])  # 처음 10개 태그만
            if len(metadata.get('tags', [])) > 10:
                value += f" (외 {len(metadata.get('tags', [])) - 10}개)"
        elif key == 'description' and isinstance(value, str):
            value = value[:200] + "..." if len(value) > 200 else value
        
        print(f"{label:<12}: {value}")
    
    print("=" * 80)


def format_metadata_json(metadata: Dict[str, Any], fields: Optional[List[str]] = None) -> str:
    """메타데이터를 JSON 형태로 포맷"""
    if fields:
        # 특정 필드만 선택
        filtered_metadata = {field: metadata.get(field) for field in fields if field in metadata}
        return json.dumps(filtered_metadata, ensure_ascii=False, indent=2, default=str)
    else:
        return json.dumps(metadata, ensure_ascii=False, indent=2, default=str)


def get_video_metadata(video_input: str) -> Dict[str, Any]:
    """영상에서 메타데이터를 추출"""
    video_id = extract_video_id(video_input)
    if not video_id:
        if len(video_input) == 11:
            video_id = video_input
        else:
            raise ValueError("올바른 YouTube URL 또는 영상 ID를 입력하세요.")
    
    try:
        metadata = fetch_video_metadata(video_id)
        return metadata or {}
    except Exception as e:
        raise ValueError(f"메타데이터를 가져올 수 없습니다: {e}")


def list_available_fields():
    """사용 가능한 메타데이터 필드 목록 출력"""
    fields = [
        'id', 'title', 'uploader', 'uploader_id', 'uploader_url',
        'webpage_url', 'upload_date', 'duration', 'view_count', 'like_count',
        'category', 'language', 'license', 'tags', 'description',
        'thumbnail', 'thumbnails', 'formats', 'automatic_captions',
        'subtitles', 'chapters', 'webpage_url_basename', 'extractor',
        'extractor_key', 'display_id', 'fulltitle', 'alt_title'
    ]
    
    print("사용 가능한 메타데이터 필드:")
    for i, field in enumerate(fields, 1):
        print(f"{i:2d}. {field}")


def main():
    parser = argparse.ArgumentParser(
        description='YouTube 영상의 메타데이터를 추출합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('video', nargs='?', help='YouTube 영상 URL 또는 영상 ID')
    
    # 출력 형식
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument('--json', action='store_true', help='JSON 형식으로 출력')
    format_group.add_argument('--table', action='store_true', help='테이블 형식으로 출력 (기본값)')
    
    # 필드 선택
    parser.add_argument('--fields', help='출력할 필드 (쉼표로 구분)')
    parser.add_argument('--list-fields', action='store_true', help='사용 가능한 필드 목록 출력')
    
    # 출력 옵션
    parser.add_argument('--output', '-o', help='결과 저장 파일명')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    # 필드 목록 출력
    if args.list_fields:
        list_available_fields()
        return
    
    # 영상 입력 확인
    if not args.video:
        parser.error("영상 URL 또는 영상 ID를 입력해야 합니다.")
    
    try:
        if args.verbose:
            print("메타데이터를 추출하는 중...", file=sys.stderr)
        
        metadata = get_video_metadata(args.video)
        
        if not metadata:
            print("메타데이터를 가져올 수 없습니다.", file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            total_fields = len(metadata)
            print(f"총 {total_fields}개 필드의 메타데이터를 가져왔습니다.", file=sys.stderr)
        
        # 필드 필터링
        fields = None
        if args.fields:
            fields = [field.strip() for field in args.fields.split(',')]
            if args.verbose:
                print(f"선택된 필드: {', '.join(fields)}", file=sys.stderr)
        
        # 출력 형식 결정
        if args.json:
            result = format_metadata_json(metadata, fields)
        else:
            if fields:
                # 특정 필드만 선택한 경우 JSON 형식으로 출력
                result = format_metadata_json(metadata, fields)
            else:
                # 테이블 형식 출력은 stdout이 아닌 직접 출력
                if args.output:
                    # 파일 저장시에는 JSON으로
                    result = format_metadata_json(metadata, fields)
                else:
                    format_metadata_table(metadata)
                    return
        
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