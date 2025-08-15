#!/usr/bin/env python3
"""
YoYakTube 채널 영상 리스트 추출 CLI

Usage:
    python -m cli.yyt_channel <channel_url> [options]
    
Examples:
    python -m cli.yyt_channel "https://www.youtube.com/@channelname" --days 7
    python -m cli.yyt_channel "https://www.youtube.com/channel/UCxxxx" --date-range 20250810-20250812
    python -m cli.yyt_channel "https://www.youtube.com/@channelname" --max-videos 10 --format json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import yt_dlp

# 부모 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# No utilities needed for this module


def parse_date_range(date_str: str) -> Tuple[datetime, datetime]:
    """날짜 범위 문자열을 파싱하여 시작일과 종료일을 반환"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date_str.lower() == 'today':
        return today, today + timedelta(days=1)
    elif date_str.lower() == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, today
    elif date_str.isdigit():
        days_ago = int(date_str)
        start_date = today - timedelta(days=days_ago)
        return start_date, today + timedelta(days=1)
    elif '-' in date_str:
        start_str, end_str = date_str.split('-', 1)
        start_date = datetime.strptime(start_str, '%Y%m%d')
        end_date = datetime.strptime(end_str, '%Y%m%d') + timedelta(days=1)
        return start_date, end_date
    else:
        target_date = datetime.strptime(date_str, '%Y%m%d')
        return target_date, target_date + timedelta(days=1)


def get_channel_videos(
    channel_url: str, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    max_videos: Optional[int] = None
) -> List[Dict]:
    """채널에서 영상 목록을 가져옴"""
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlistend': max_videos if max_videos else None,
    }
    
    videos = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            channel_info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' not in channel_info:
                raise ValueError("채널 영상 목록을 가져올 수 없습니다.")
            
            channel_title = channel_info.get('title', 'Unknown')
            channel_id = channel_info.get('id', 'Unknown')
            
            print(f"채널: {channel_title} (ID: {channel_id})", file=sys.stderr)
            if start_date and end_date:
                print(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}", file=sys.stderr)
            print("영상 정보를 가져오는 중...", file=sys.stderr)
            
            for entry in channel_info['entries']:
                if not entry:
                    continue
                    
                # 중첩 구조 처리
                if entry.get('_type') == 'playlist' and 'entries' in entry:
                    sub_entries = entry['entries'][:max_videos] if max_videos else entry['entries']
                else:
                    sub_entries = [entry]
                
                for sub_entry in sub_entries:
                    if not sub_entry:
                        continue
                        
                    video_id = sub_entry.get('id')
                    if not video_id or len(video_id) != 11:
                        continue
                    
                    try:
                        # 상세 정보가 필요한 경우만 추가 요청
                        if start_date or end_date:
                            video_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                            
                            if 'upload_date' in video_info:
                                upload_date = datetime.strptime(video_info['upload_date'], '%Y%m%d')
                                
                                if start_date and end_date:
                                    if not (start_date <= upload_date < end_date):
                                        if upload_date < start_date:
                                            break  # 더 오래된 영상이면 중단
                                        continue
                                
                                video_data = {
                                    'id': video_id,
                                    'title': video_info.get('title', 'Unknown'),
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'upload_date': upload_date.isoformat(),
                                    'duration': video_info.get('duration', 0),
                                    'view_count': video_info.get('view_count', 0),
                                    'description': video_info.get('description', ''),
                                    'channel': channel_title,
                                    'channel_id': channel_id
                                }
                            else:
                                continue
                        else:
                            # 기본 정보만 사용
                            video_data = {
                                'id': video_id,
                                'title': sub_entry.get('title', 'Unknown'),
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'channel': channel_title,
                                'channel_id': channel_id
                            }
                        
                        videos.append(video_data)
                        
                    except Exception as e:
                        print(f"영상 {video_id} 처리 중 오류: {e}", file=sys.stderr)
                        continue
    
    except Exception as e:
        raise ValueError(f"채널 정보를 가져올 수 없습니다: {e}")
    
    return videos


def print_videos_table(videos: List[Dict]):
    """영상 목록을 테이블 형태로 출력"""
    if not videos:
        print("영상이 없습니다.")
        return
    
    print(f"\n총 {len(videos)}개 영상")
    print("=" * 120)
    print(f"{'번호':<4} {'제목':<50} {'업로드일':<12} {'조회수':<10} {'시간':<8}")
    print("=" * 120)
    
    for i, video in enumerate(videos, 1):
        title = video['title'][:47] + "..." if len(video['title']) > 50 else video['title']
        upload_date = video.get('upload_date', 'N/A')[:10] if video.get('upload_date') else 'N/A'
        view_count = f"{video.get('view_count', 0):,}" if video.get('view_count') else 'N/A'
        duration = video.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else 'N/A'
        
        print(f"{i:<4} {title:<50} {upload_date:<12} {view_count:<10} {duration_str:<8}")


def main():
    parser = argparse.ArgumentParser(
        description='YouTube 채널의 영상 리스트를 추출합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('channel_url', help='YouTube 채널 URL')
    
    # 날짜 관련 옵션 (상호 배타적)
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--days', type=int, help='N일 전부터 오늘까지')
    date_group.add_argument('--date-range', help='날짜 범위 (YYYYMMDD-YYYYMMDD, YYYYMMDD, today, yesterday)')
    
    parser.add_argument('--max-videos', type=int, help='최대 추출할 영상 수')
    parser.add_argument('--format', choices=['json', 'table'], default='table', help='출력 형식')
    parser.add_argument('--output', help='결과 저장 파일명 (JSON만 가능)')
    
    args = parser.parse_args()
    
    try:
        start_date = None
        end_date = None
        
        if args.days:
            start_date, end_date = parse_date_range(str(args.days))
        elif args.date_range:
            start_date, end_date = parse_date_range(args.date_range)
        
        videos = get_channel_videos(args.channel_url, start_date, end_date, args.max_videos)
        
        if args.format == 'json':
            result = {
                'channel_url': args.channel_url,
                'extracted_at': datetime.now().isoformat(),
                'filters': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'max_videos': args.max_videos
                },
                'total_videos': len(videos),
                'videos': videos
            }
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                print(f"결과가 {args.output}에 저장되었습니다.", file=sys.stderr)
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        else:
            print_videos_table(videos)
    
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()