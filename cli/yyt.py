#!/usr/bin/env python3
"""
YoYakTube 통합 CLI 인터페이스

Usage:
    python -m cli.yyt <command> [options]
    
Commands:
    channel         채널 영상 리스트 추출
    transcript      영상 자막 추출  
    meta           영상 메타데이터 추출
    summarize      자막 요약
    chat           자막 기반 Q&A 챗봇
    ai             AI 모델 관리
    config         설정 관리
    pipeline       여러 단계를 연결한 파이프라인 실행
    
Examples:
    # 기본 워크플로우: 영상 URL -> 요약
    python -m cli.yyt summarize "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # 채널의 최근 영상들 요약
    python -m cli.yyt pipeline channel-summary @channelname --days 7
    
    # 설정 확인
    python -m cli.yyt config show
    
    # AI 모델 테스트
    python -m cli.yyt ai test openai gpt-5-mini
    
    # 완전한 파이프라인 실행
    python -m cli.yyt pipeline full-analysis video_url --output-dir ./results
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List

# 부모 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_subcommand(module_name: str, args: List[str]) -> int:
    """서브 명령 실행"""
    try:
        cmd = [sys.executable, '-m', f'cli.{module_name}'] + args
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"명령 실행 실패: {e}", file=sys.stderr)
        return 1


def pipeline_channel_summary(args: argparse.Namespace) -> int:
    """채널 요약 파이프라인"""
    print("채널 영상 일괄 요약 파이프라인 실행 중...")
    
    # 1. 채널 영상 리스트 추출
    channel_args = [args.channel_url]
    if args.days:
        channel_args.extend(['--days', str(args.days)])
    if args.date_range:
        channel_args.extend(['--date-range', args.date_range])
    if args.max_videos:
        channel_args.extend(['--max-videos', str(args.max_videos)])
    
    channel_args.extend(['--format', 'json', '--output', 'temp_videos.json'])
    
    result = run_subcommand('yyt_channel', channel_args)
    if result != 0:
        return result
    
    # 2. 각 영상을 요약 (실제 구현에서는 JSON 파싱 후 반복 처리)
    print("채널 영상 리스트 추출 완료. 개별 영상 요약은 별도 스크립트로 구현 필요.")
    
    return 0


def pipeline_full_analysis(args: argparse.Namespace) -> int:
    """완전한 분석 파이프라인"""
    video_url = args.video_url
    output_dir = Path(args.output_dir or './yyt_results')
    output_dir.mkdir(exist_ok=True)
    
    print(f"완전한 분석 파이프라인 실행 중: {video_url}")
    print(f"결과 디렉토리: {output_dir}")
    
    # 1. 메타데이터 추출
    print("\n1. 메타데이터 추출 중...")
    meta_file = output_dir / 'metadata.json'
    result = run_subcommand('yyt_meta', [video_url, '--json', '--output', str(meta_file)])
    if result != 0:
        print("메타데이터 추출 실패")
        return result
    
    # 2. 자막 추출
    print("\n2. 자막 추출 중...")
    transcript_file = output_dir / 'transcript.txt'
    result = run_subcommand('yyt_transcript', [video_url, '--output', str(transcript_file)])
    if result != 0:
        print("자막 추출 실패")
        return result
    
    # 3. 요약 생성
    print("\n3. 요약 생성 중...")
    summary_file = output_dir / 'summary.md'
    result = run_subcommand('yyt_summarize', [video_url, '--output', str(summary_file)])
    if result != 0:
        print("요약 생성 실패")
        return result
    
    print(f"\n✅ 완전한 분석 완료! 결과는 {output_dir}에 저장되었습니다.")
    print(f"  - 메타데이터: {meta_file}")
    print(f"  - 자막: {transcript_file}")
    print(f"  - 요약: {summary_file}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='YoYakTube 통합 CLI 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='사용할 명령')
    
    # 각 서브모듈에 대한 파서 생성
    subparsers.add_parser('channel', help='채널 영상 리스트 추출')
    subparsers.add_parser('transcript', help='영상 자막 추출')
    subparsers.add_parser('meta', help='영상 메타데이터 추출')
    subparsers.add_parser('summarize', help='자막 요약')
    subparsers.add_parser('chat', help='자막 기반 Q&A 챗봇')
    subparsers.add_parser('ai', help='AI 모델 관리')
    subparsers.add_parser('config', help='설정 관리')
    
    # pipeline 서브파서
    pipeline_parser = subparsers.add_parser('pipeline', help='파이프라인 실행')
    pipeline_subparsers = pipeline_parser.add_subparsers(dest='pipeline_type', help='파이프라인 타입')
    
    # channel-summary 파이프라인
    cs_parser = pipeline_subparsers.add_parser('channel-summary', help='채널 영상 일괄 요약')
    cs_parser.add_argument('channel_url', help='채널 URL')
    cs_parser.add_argument('--days', type=int, help='N일 전부터')
    cs_parser.add_argument('--date-range', help='날짜 범위')
    cs_parser.add_argument('--max-videos', type=int, help='최대 영상 수')
    
    # full-analysis 파이프라인
    fa_parser = pipeline_subparsers.add_parser('full-analysis', help='완전한 영상 분석')
    fa_parser.add_argument('video_url', help='영상 URL')
    fa_parser.add_argument('--output-dir', help='결과 저장 디렉토리')
    
    # 인수가 없으면 도움말 출력
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # 명령어만 있고 추가 인수가 없는 경우 해당 모듈의 도움말 출력
    if len(sys.argv) == 2 and sys.argv[1] in [
        'channel', 'transcript', 'meta', 'summarize', 'chat', 'ai', 'config'
    ]:
        return run_subcommand(f'yyt_{sys.argv[1]}', ['--help'])
    
    args, remaining_args = parser.parse_known_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # pipeline 명령 처리
        if args.command == 'pipeline':
            if args.pipeline_type == 'channel-summary':
                return pipeline_channel_summary(args)
            elif args.pipeline_type == 'full-analysis':
                return pipeline_full_analysis(args)
            else:
                pipeline_parser.print_help()
                return 1
        
        # 일반 서브모듈 명령 처리
        elif args.command in ['channel', 'transcript', 'meta', 'summarize', 'chat', 'ai', 'config']:
            module_name = f'yyt_{args.command}'
            return run_subcommand(module_name, remaining_args)
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\n작업이 중단되었습니다.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())