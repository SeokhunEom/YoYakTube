#!/usr/bin/env python3
"""
유튜브 채널 특정 기간 영상 요약 CLI 도구 (독립 버전)

Usage:
    python channel_cli.py <channel_url> <date_range> [--info-only] [--max-videos N]
    
Examples:
    python channel_cli.py "https://www.youtube.com/@channelname" 20250810-20250812
    python channel_cli.py "https://www.youtube.com/channel/UCxxxx" today --info-only
    python channel_cli.py "https://www.youtube.com/@channelname" 7 --max-videos 10
"""

import argparse
import sys
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import yt_dlp
import json
from dataclasses import dataclass
from youtube_transcript_api import YouTubeTranscriptApi


# 요약 프롬프트 (constants.py에서 복사)
FULL_SUMMARY_PROMPT = """
당신은 YouTube 영상의 한국어 자막을 분석하여 구조화된 요약을 제공하는 전문가입니다.

주어진 영상 자막을 바탕으로 다음 형식으로 요약해주세요:

## 📝 영상 요약

### 🔑 핵심 내용
- 영상의 주요 포인트를 3-5개 bullet point로 정리
- 각 포인트는 구체적이고 명확하게 작성

### 📋 상세 내용
영상의 흐름에 따라 섹션별로 정리:

**[주제1]** (타임스탬프: 00:00-05:30)
- 해당 구간의 핵심 내용
- 중요한 세부사항

**[주제2]** (타임스탬프: 05:30-12:15)  
- 해당 구간의 핵심 내용
- 중요한 세부사항

### 💡 인사이트 및 결론
- 영상에서 얻을 수 있는 주요 인사이트
- 결론 또는 행동 방안

---

**요약 시 주의사항:**
1. 한국어로 작성
2. 타임스탬프는 대략적인 구간으로 표시
3. 영상의 핵심 가치와 실용성을 강조
4. 구조화되고 읽기 쉽게 작성
5. 불필요한 내용은 생략하고 핵심만 추출
"""


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass 
class ChatResponse:
    content: str
    usage: Dict[str, int]
    model: str


def extract_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 영상 ID 추출"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:v\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def collect_transcript(video_id: str, languages: List[str] = ['ko', 'en', 'ja']) -> Optional[str]:
    """영상의 자막 수집"""
    try:
        # 사용 가능한 자막 목록 가져오기
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 우선순위에 따라 자막 시도
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang])
                entries = transcript.fetch()
                return ' '.join([entry['text'] for entry in entries])
            except:
                continue
        
        # 자동생성 자막 시도  
        try:
            transcript = transcript_list.find_generated_transcript(languages)
            entries = transcript.fetch()
            return ' '.join([entry['text'] for entry in entries])
        except:
            pass
            
    except Exception as e:
        print(f"자막 수집 실패: {e}")
    
    return None


def parse_date_range(date_str: str) -> Tuple[datetime, datetime]:
    """
    날짜 범위 문자열을 파싱하여 시작일과 종료일을 반환
    
    지원 형식:
    - YYYYMMDD-YYYYMMDD: 특정 기간
    - YYYYMMDD: 해당 날짜만
    - today: 오늘
    - yesterday: 어제
    - 숫자: N일 전부터 오늘까지
    """
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
        # 단일 날짜
        target_date = datetime.strptime(date_str, '%Y%m%d')
        return target_date, target_date + timedelta(days=1)


def get_channel_videos(channel_url: str, start_date: datetime, end_date: datetime, max_videos: Optional[int] = None) -> List[Dict]:
    """
    채널에서 특정 기간의 영상 목록을 가져옴
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlistend': max_videos if max_videos else None,
    }
    
    videos = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 채널 정보 추출
            channel_info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' not in channel_info:
                raise ValueError("채널 영상 목록을 가져올 수 없습니다.")
            
            print(f"채널: {channel_info.get('title', 'Unknown')}")
            print(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
            print("영상 정보를 가져오는 중...")
            
            # 각 영상의 상세 정보 가져오기 (중첩 구조 처리)
            for entry in channel_info['entries']:
                if not entry:
                    continue
                    
                # entry가 playlist인 경우 하위 entries 처리
                if entry.get('_type') == 'playlist' and 'entries' in entry:
                    sub_entries = entry['entries'][:max_videos] if max_videos else entry['entries']
                else:
                    sub_entries = [entry]
                
                for sub_entry in sub_entries:
                    if not sub_entry:
                        continue
                        
                    # entry에서 올바른 영상 ID 추출
                    video_id = sub_entry.get('id')
                    if not video_id or len(video_id) != 11:
                        continue
                    
                    try:
                        # 영상 상세 정보 가져오기
                        video_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                        
                        # 업로드 날짜 확인
                        if 'upload_date' in video_info:
                            upload_date = datetime.strptime(video_info['upload_date'], '%Y%m%d')
                            
                            # 날짜 범위 내 확인
                            if start_date <= upload_date < end_date:
                                videos.append({
                                    'id': video_id,
                                    'title': video_info.get('title', 'Unknown'),
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'upload_date': upload_date,
                                    'duration': video_info.get('duration', 0),
                                    'view_count': video_info.get('view_count', 0),
                                    'description': video_info.get('description', '')[:200] + '...' if video_info.get('description', '') else '',
                                })
                            elif upload_date < start_date:
                                # 더 오래된 영상이면 중단 (최신순 정렬이므로)
                                break
                    
                    except Exception as e:
                        print(f"영상 {video_id} 처리 중 오류: {e}")
                        continue
    
    except Exception as e:
        raise ValueError(f"채널 정보를 가져올 수 없습니다: {e}")
    
    return sorted(videos, key=lambda x: x['upload_date'], reverse=True)


def print_video_info(videos: List[Dict]):
    """영상 정보를 출력"""
    print(f"\n찾은 영상 수: {len(videos)}")
    print("=" * 80)
    
    for i, video in enumerate(videos, 1):
        print(f"{i}. {video['title']}")
        print(f"   업로드: {video['upload_date'].strftime('%Y-%m-%d')}")
        print(f"   재생시간: {video['duration']//60}분 {video['duration']%60}초")
        print(f"   조회수: {video['view_count']:,}")
        print(f"   URL: {video['url']}")
        if video['description']:
            print(f"   설명: {video['description']}")
        print()


def simple_openai_chat(api_key: str, messages: List[ChatMessage], model: str = "gpt-3.5-turbo") -> str:
    """간단한 OpenAI API 호출 (외부 라이브러리 없이)"""
    import requests
    import json
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    data = {
        'model': model,
        'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
        'temperature': 0.2
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise Exception(f"OpenAI API 호출 실패: {e}")


def summarize_videos(videos: List[Dict], api_key: str) -> Dict[str, str]:
    """영상들을 요약 (OpenAI API 사용)"""
    summaries = {}
    
    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] 요약 중: {video['title']}")
        
        try:
            # 트랜스크립트 수집
            transcript_text = collect_transcript(video['id'])
            
            if not transcript_text:
                print(f"  트랜스크립트를 찾을 수 없습니다.")
                continue
            
            # 요약 생성
            messages = [
                ChatMessage(role="system", content=FULL_SUMMARY_PROMPT),
                ChatMessage(role="user", content=f"영상 제목: {video['title']}\n\n트랜스크립트:\n{transcript_text}")
            ]
            
            summary = simple_openai_chat(api_key, messages)
            
            summaries[video['id']] = {
                'title': video['title'],
                'url': video['url'],
                'upload_date': video['upload_date'].isoformat(),
                'summary': summary
            }
            
            print(f"  요약 완료")
            
        except Exception as e:
            print(f"  요약 실패: {e}")
            continue
    
    return summaries


def save_results(videos: List[Dict], summaries: Dict[str, str], output_file: str):
    """결과를 파일로 저장"""
    result = {
        'generated_at': datetime.now().isoformat(),
        'total_videos': len(videos),
        'summarized_videos': len(summaries),
        'videos': videos,
        'summaries': summaries
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n결과가 {output_file}에 저장되었습니다.")


def main():
    parser = argparse.ArgumentParser(
        description='유튜브 채널의 특정 기간 영상을 요약합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('channel_url', help='유튜브 채널 URL')
    parser.add_argument('date_range', help='날짜 범위 (YYYYMMDD-YYYYMMDD, YYYYMMDD, today, yesterday, 숫자)')
    parser.add_argument('--info-only', action='store_true', help='영상 정보만 출력 (요약하지 않음)')
    parser.add_argument('--max-videos', type=int, help='최대 처리할 영상 수')
    parser.add_argument('--output', help='결과 저장 파일명 (JSON)')
    parser.add_argument('--api-key', help='OpenAI API 키 (또는 OPENAI_API_KEY 환경변수 사용)')
    
    args = parser.parse_args()
    
    try:
        # 날짜 범위 파싱
        start_date, end_date = parse_date_range(args.date_range)
        
        # 채널 영상 목록 가져오기
        videos = get_channel_videos(args.channel_url, start_date, end_date, args.max_videos)
        
        if not videos:
            print("해당 기간에 업로드된 영상이 없습니다.")
            return
        
        # 영상 정보 출력
        print_video_info(videos)
        
        # 요약 모드일 경우
        if not args.info_only:
            # API 키 가져오기
            api_key = args.api_key or os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                print("오류: OpenAI API 키가 필요합니다.")
                print("--api-key 옵션을 사용하거나 OPENAI_API_KEY 환경변수를 설정하세요.")
                sys.exit(1)
            
            print("OpenAI API를 사용하여 요약을 생성합니다.")
            
            # 영상 요약
            summaries = summarize_videos(videos, api_key)
            
            # 결과 저장
            output_file = args.output or f"channel_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_results(videos, summaries, output_file)
    
    except Exception as e:
        print(f"오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()