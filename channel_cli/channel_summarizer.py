#!/usr/bin/env python3
"""
유튜브 채널 특정 기간 영상 요약 CLI 도구

Usage:
    python channel_summarizer.py <channel_url> <date_range> [--info-only] [--max-videos N]

Examples:
    python channel_summarizer.py "https://www.youtube.com/@channelname" 20250810-20250812
    python channel_summarizer.py "https://www.youtube.com/channel/UCxxxx" today --info-only
    python channel_summarizer.py "https://www.youtube.com/@channelname" 7 --max-videos 10
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import yt_dlp
import json
from pathlib import Path

# 기존 YoYakTube 모듈 임포트
sys.path.append(str(Path(__file__).parent))
from GUI.llm import LLMClient
from GUI.transcript import collect_transcript
from GUI.utils import extract_video_id, create_summary_markdown
from GUI.constants import FULL_SUMMARY_PROMPT


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

    if date_str.lower() == "today":
        return today, today + timedelta(days=1)

    elif date_str.lower() == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, today

    elif date_str.isdigit():
        days_ago = int(date_str)
        start_date = today - timedelta(days=days_ago)
        return start_date, today + timedelta(days=1)

    elif "-" in date_str:
        start_str, end_str = date_str.split("-", 1)
        start_date = datetime.strptime(start_str, "%Y%m%d")
        end_date = datetime.strptime(end_str, "%Y%m%d") + timedelta(days=1)
        return start_date, end_date

    else:
        # 단일 날짜
        target_date = datetime.strptime(date_str, "%Y%m%d")
        return target_date, target_date + timedelta(days=1)


def get_channel_videos(
    channel_url: str,
    start_date: datetime,
    end_date: datetime,
    max_videos: Optional[int] = None,
) -> List[Dict]:
    """
    채널에서 특정 기간의 영상 목록을 가져옴
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": max_videos if max_videos else None,
    }

    videos = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 채널 정보 추출
            channel_info = ydl.extract_info(channel_url, download=False)

            if "entries" not in channel_info:
                raise ValueError("채널 영상 목록을 가져올 수 없습니다.")

            print(f"채널: {channel_info.get('title', 'Unknown')}")
            print(
                f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
            )
            print("영상 정보를 가져오는 중...")

            # 각 영상의 상세 정보 가져오기
            for entry in channel_info["entries"]:
                if not entry:
                    continue

                try:
                    # 영상 상세 정보 가져오기
                    video_info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={entry['id']}", download=False
                    )

                    # 업로드 날짜 확인
                    if "upload_date" in video_info:
                        upload_date = datetime.strptime(
                            video_info["upload_date"], "%Y%m%d"
                        )

                        # 날짜 범위 내 확인
                        if start_date <= upload_date < end_date:
                            videos.append(
                                {
                                    "id": entry["id"],
                                    "title": video_info.get("title", "Unknown"),
                                    "url": f"https://www.youtube.com/watch?v={entry['id']}",
                                    "upload_date": upload_date,
                                    "duration": video_info.get("duration", 0),
                                    "view_count": video_info.get("view_count", 0),
                                    "description": (
                                        video_info.get("description", "")[:200] + "..."
                                        if video_info.get("description", "")
                                        else ""
                                    ),
                                }
                            )
                        elif upload_date < start_date:
                            # 더 오래된 영상이면 중단 (최신순 정렬이므로)
                            break

                except Exception as e:
                    print(f"영상 {entry['id']} 처리 중 오류: {e}")
                    continue

    except Exception as e:
        raise ValueError(f"채널 정보를 가져올 수 없습니다: {e}")

    return sorted(videos, key=lambda x: x["upload_date"], reverse=True)


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
        if video["description"]:
            print(f"   설명: {video['description']}")
        print()


def summarize_videos(videos: List[Dict], llm_client: LLMClient) -> Dict[str, str]:
    """영상들을 요약"""
    summaries = {}

    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] 요약 중: {video['title']}")

        try:
            # 트랜스크립트 수집
            transcript_text = collect_transcript(video["id"])

            if not transcript_text:
                print(f"  트랜스크립트를 찾을 수 없습니다.")
                continue

            # 요약 생성
            from GUI.llm import ChatMessage

            messages = [
                ChatMessage(role="system", content=FULL_SUMMARY_PROMPT),
                ChatMessage(
                    role="user",
                    content=f"영상 제목: {video['title']}\n\n트랜스크립트:\n{transcript_text}",
                ),
            ]

            response = llm_client.chat(messages)
            summary = response.content

            summaries[video["id"]] = {
                "title": video["title"],
                "url": video["url"],
                "upload_date": video["upload_date"].isoformat(),
                "summary": summary,
            }

            print(f"  요약 완료")

        except Exception as e:
            print(f"  요약 실패: {e}")
            continue

    return summaries


def save_results(videos: List[Dict], summaries: Dict[str, str], output_file: str):
    """결과를 파일로 저장"""
    result = {
        "generated_at": datetime.now().isoformat(),
        "total_videos": len(videos),
        "summarized_videos": len(summaries),
        "videos": videos,
        "summaries": summaries,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n결과가 {output_file}에 저장되었습니다.")


def main():
    parser = argparse.ArgumentParser(
        description="유튜브 채널의 특정 기간 영상을 요약합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("channel_url", help="유튜브 채널 URL")
    parser.add_argument(
        "date_range",
        help="날짜 범위 (YYYYMMDD-YYYYMMDD, YYYYMMDD, today, yesterday, 숫자)",
    )
    parser.add_argument(
        "--info-only", action="store_true", help="영상 정보만 출력 (요약하지 않음)"
    )
    parser.add_argument("--max-videos", type=int, help="최대 처리할 영상 수")
    parser.add_argument("--output", help="결과 저장 파일명 (JSON)")

    args = parser.parse_args()

    try:
        # 날짜 범위 파싱
        start_date, end_date = parse_date_range(args.date_range)

        # 채널 영상 목록 가져오기
        videos = get_channel_videos(
            args.channel_url, start_date, end_date, args.max_videos
        )

        if not videos:
            print("해당 기간에 업로드된 영상이 없습니다.")
            return

        # 영상 정보 출력
        print_video_info(videos)

        # 요약 모드일 경우
        if not args.info_only:
            # LLM 클라이언트 생성 (환경변수 또는 기본값 사용)

            # 환경변수에서 API 키 가져오기
            openai_key = os.getenv("OPENAI_API_KEY", "")
            gemini_key = os.getenv("GEMINI_API_KEY", "")
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

            # 사용 가능한 첫 번째 제공자 선택
            if openai_key:
                from GUI.llm import OpenAIClient

                llm_client = OpenAIClient(api_key=openai_key, model="gpt-3.5-turbo")
                print("OpenAI 모델을 사용합니다.")
            elif gemini_key:
                from GUI.llm import GeminiClient

                llm_client = GeminiClient(api_key=gemini_key, model="gemini-pro")
                print("Gemini 모델을 사용합니다.")
            else:
                from GUI.llm import OllamaClient

                llm_client = OllamaClient(host=ollama_host, model="llama2")
                print("Ollama 모델을 사용합니다.")

            # 영상 요약
            summaries = summarize_videos(videos, llm_client)

            # 결과 저장
            output_file = (
                args.output
                or f"channel_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            save_results(videos, summaries, output_file)

    except Exception as e:
        print(f"오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
