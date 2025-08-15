#!/usr/bin/env python3
"""
YoYakTube 자막 기반 Q&A 챗봇 CLI

Usage:
    python -m cli.yyt_chat [input_source] [options]
    
Examples:
    # 영상 URL 기반 채팅
    python -m cli.yyt_chat "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # 파일 기반 채팅
    python -m cli.yyt_chat --file transcript.txt
    
    # 대화형 모드
    python -m cli.yyt_chat video_url --interactive
    
    # 단일 질문
    python -m cli.yyt_chat video_url --question "이 영상의 주요 내용은 무엇인가요?"
    
    # AI 모델 지정
    python -m cli.yyt_chat video_url --provider openai --model gpt-5
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# 같은 디렉토리의 core 모듈 import
from .core import (
    ChatMessage, get_or_create_llm, collect_transcript, fetch_video_metadata,
    extract_video_id, create_qa_context, get_config
)

# Add parent directory to Python path to access yoyaktube module
sys.path.insert(0, str(Path(__file__).parent.parent))
from yoyaktube.constants import QA_PROMPT


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
    
    # 메타데이터 추출
    try:
        metadata = fetch_video_metadata(video_id)
    except Exception as e:
        print(f"메타데이터 추출 실패: {e}", file=sys.stderr)
        metadata = None
    
    return transcript_text, metadata


def read_transcript_from_file(file_path: str) -> str:
    """파일에서 자막을 읽음"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"파일을 읽을 수 없습니다: {e}")


def create_llm_client(provider: str = None, model: str = None):
    """LLM 클라이언트를 생성"""
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
    import os
    openai_key = os.getenv('OPENAI_API_KEY', '')
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    
    return get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)


def answer_question(
    transcript: str,
    question: str,
    provider: str = None,
    model: str = None,
    context_history: Optional[List[dict]] = None
) -> str:
    """질문에 대한 답변 생성"""
    
    # LLM 클라이언트 생성
    llm = create_llm_client(provider, model)
    
    # 컨텍스트 생성  
    context = create_qa_context(transcript, context_history or [])
    
    # 메시지 구성
    messages = [
        ChatMessage(role="user", content=QA_PROMPT.format(context=context, question=question))
    ]
    
    response = llm.chat(messages, temperature=0.3)
    return response.content


def interactive_chat(
    transcript: str,
    metadata: dict = None,
    provider: str = None,
    model: str = None
):
    """대화형 채팅 모드"""
    
    print("=" * 60)
    print("YoYakTube Q&A 챗봇")
    print("=" * 60)
    
    if metadata:
        print(f"제목: {metadata.get('title', 'Unknown')}")
        print(f"채널: {metadata.get('uploader', 'Unknown')}")
        print(f"길이: {metadata.get('duration', 0)}초")
        print("=" * 60)
    
    print("질문을 입력하세요. 종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
    print("대화 기록을 저장하려면 'save <파일명>'을 입력하세요.")
    print()
    
    chat_history = []
    
    while True:
        try:
            question = input("질문: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("채팅을 종료합니다.")
                break
            
            if question.startswith('save '):
                filename = question[5:].strip()
                if filename:
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump({
                                'metadata': metadata,
                                'chat_history': chat_history
                            }, f, ensure_ascii=False, indent=2, default=str)
                        print(f"대화 기록이 {filename}에 저장되었습니다.")
                    except Exception as e:
                        print(f"저장 실패: {e}")
                continue
            
            if not question:
                continue
            
            print("답변을 생성하는 중...")
            
            try:
                answer = answer_question(transcript, question, provider, model, context_history=chat_history)
                
                print(f"\n답변: {answer}\n")
                
                # 대화 기록에 추가
                chat_history.append({
                    'question': question,
                    'answer': answer
                })
                
            except Exception as e:
                print(f"답변 생성 실패: {e}\n")
        
        except KeyboardInterrupt:
            print("\n\n채팅을 종료합니다.")
            break
        except EOFError:
            print("\n\n채팅을 종료합니다.")
            break


def main():
    parser = argparse.ArgumentParser(
        description='자막을 기반으로 Q&A 채팅을 진행합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # 입력 소스 (상호 배타적)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('video', nargs='?', help='YouTube 영상 URL 또는 영상 ID')
    input_group.add_argument('--file', '-f', help='자막 텍스트 파일 경로')
    
    # 모드 설정 (상호 배타적)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--interactive', '-i', action='store_true', help='대화형 채팅 모드')
    mode_group.add_argument('--question', '-q', help='단일 질문')
    
    # AI 모델 설정
    parser.add_argument('--provider', choices=['openai', 'gemini', 'ollama'], help='AI 제공자')
    parser.add_argument('--model', help='사용할 모델명')
    
    # 기타 설정
    parser.add_argument('--languages', default='ko,en,ja', help='자막 언어 우선순위 (쉼표로 구분)')
    parser.add_argument('--output', '-o', help='대화 결과 저장 파일명 (JSON)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    # 입력 소스 확인
    if not any([args.video, args.file]):
        parser.error("영상 URL 또는 파일 경로를 지정해야 합니다.")
    
    # 모드 설정 확인
    if not args.interactive and not args.question:
        args.interactive = True  # 기본값은 대화형 모드
    
    try:
        # 자막 추출
        transcript = None
        metadata = None
        
        if args.video:
            if args.verbose:
                print("영상에서 자막을 추출하는 중...", file=sys.stderr)
            
            languages = [lang.strip() for lang in args.languages.split(',')]
            transcript, metadata = get_transcript_from_video(args.video, languages)
            
            if args.verbose and metadata:
                print(f"제목: {metadata.get('title', 'Unknown')}", file=sys.stderr)
                print(f"채널: {metadata.get('uploader', 'Unknown')}", file=sys.stderr)
                print(f"길이: {metadata.get('duration', 0)}초", file=sys.stderr)
        
        elif args.file:
            if args.verbose:
                print(f"파일에서 자막을 읽는 중: {args.file}", file=sys.stderr)
            transcript = read_transcript_from_file(args.file)
        
        if not transcript:
            raise ValueError("자막을 가져올 수 없습니다.")
        
        if args.verbose:
            print(f"자막 길이: {len(transcript)} 문자", file=sys.stderr)
            print(f"AI 제공자: {args.provider or '자동'}", file=sys.stderr)
            print(f"모델: {args.model or '자동'}", file=sys.stderr)
        
        # 모드별 실행
        if args.interactive:
            interactive_chat(transcript, metadata, args.provider, args.model)
        
        elif args.question:
            if args.verbose:
                print("답변을 생성하는 중...", file=sys.stderr)
            
            answer = answer_question(transcript, args.question, args.provider, args.model)
            
            result = {
                'question': args.question,
                'answer': answer,
                'metadata': metadata
            }
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                if args.verbose:
                    print(f"결과가 {args.output}에 저장되었습니다.", file=sys.stderr)
            else:
                print(answer)
    
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()