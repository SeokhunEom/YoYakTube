#!/usr/bin/env python3
"""
YoYakTube AI 모델 라우터 및 관리 CLI

Usage:
    python -m cli.yyt_ai [command] [options]
    
Commands:
    list                     사용 가능한 모델 목록 출력
    test <provider> <model>  모델 연결 테스트
    chat                     모델과 직접 채팅
    benchmark                모델 성능 벤치마크
    
Examples:
    # 모든 사용 가능한 모델 나열
    python -m cli.yyt_ai list
    
    # 특정 제공자 모델만 나열
    python -m cli.yyt_ai list --provider openai
    
    # 모델 연결 테스트
    python -m cli.yyt_ai test openai gpt-5-mini
    
    # 모델과 직접 채팅
    python -m cli.yyt_ai chat --provider gemini --model gemini-2.5-flash
    
    # 모델 성능 벤치마크
    python -m cli.yyt_ai benchmark --models openai:gpt-5-mini,gemini:gemini-2.5-flash
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# 부모 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from yoyaktube.llm import ChatMessage, get_or_create_llm, OpenAIClient, GeminiClient, OllamaClient
from yoyaktube.config import get_config


def get_available_models() -> Dict[str, List[str]]:
    """사용 가능한 모델 목록을 제공자별로 반환"""
    import os
    
    models = {
        'openai': [],
        'gemini': [],
        'ollama': []
    }
    
    # OpenAI 모델
    if os.getenv('OPENAI_API_KEY'):
        models['openai'] = [
            'gpt-5-mini', 'gpt-5', 'gpt-5-nano',
            'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'
        ]
    
    # Gemini 모델
    if os.getenv('GEMINI_API_KEY'):
        models['gemini'] = [
            'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite',
            'gemini-1.5-pro', 'gemini-1.5-flash'
        ]
    
    # Ollama 모델 (동적 조회)
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    try:
        resp = requests.get(f"{ollama_host.rstrip('/')}/api/tags", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        models['ollama'] = [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception:
        models['ollama'] = []
    
    return models


def list_models(provider: Optional[str] = None):
    """모델 목록 출력"""
    models = get_available_models()
    
    if provider:
        if provider not in models:
            print(f"오류: 알 수 없는 제공자 '{provider}'", file=sys.stderr)
            return
        
        provider_models = models[provider]
        print(f"{provider.upper()} 모델:")
        if provider_models:
            for model in provider_models:
                print(f"  - {model}")
        else:
            print("  사용 가능한 모델이 없습니다. API 키를 확인하세요.")
    else:
        for prov, model_list in models.items():
            print(f"{prov.upper()} 모델:")
            if model_list:
                for model in model_list:
                    print(f"  - {model}")
            else:
                print("  사용 가능한 모델이 없습니다.")
            print()


def test_model(provider: str, model: str) -> bool:
    """모델 연결 테스트"""
    import os
    
    print(f"모델 테스트: {provider}/{model}")
    
    try:
        # API 키 확인
        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                return False
        elif provider == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
                return False
        
        # LLM 클라이언트 생성
        openai_key = os.getenv('OPENAI_API_KEY', '')
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        
        llm = get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)
        
        # 간단한 테스트 메시지
        test_message = ChatMessage(role="user", content="Hello! Please respond with 'Test successful'")
        
        print("연결 테스트 중...")
        start_time = time.time()
        
        response = llm.chat([test_message])
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ 테스트 성공!")
        print(f"응답 시간: {response_time:.2f}초")
        print(f"응답 내용: {response.content[:100]}...")
        
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            print(f"토큰 사용량: {usage.get('total_tokens', 'N/A')}")
        
        return True
    
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def interactive_chat(provider: str, model: str):
    """모델과 직접 채팅"""
    import os
    
    print(f"모델과 채팅: {provider}/{model}")
    print("종료하려면 'quit', 'exit', 또는 'q'를 입력하세요.")
    print("=" * 50)
    
    try:
        # LLM 클라이언트 생성
        openai_key = os.getenv('OPENAI_API_KEY', '')
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        
        llm = get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)
        
        messages = []
        
        while True:
            user_input = input("\n사용자: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("채팅을 종료합니다.")
                break
            
            if not user_input:
                continue
            
            messages.append(ChatMessage(role="user", content=user_input))
            
            print("AI: ", end="", flush=True)
            
            try:
                response = llm.chat(messages)
                print(response.content)
                
                messages.append(ChatMessage(role="assistant", content=response.content))
            
            except Exception as e:
                print(f"오류 발생: {e}")
    
    except Exception as e:
        print(f"채팅 초기화 실패: {e}", file=sys.stderr)


def benchmark_models(model_specs: List[str], test_prompt: str = "Explain what AI is in 50 words."):
    """모델 성능 벤치마크"""
    import os
    
    print("모델 성능 벤치마크")
    print("=" * 60)
    print(f"테스트 프롬프트: {test_prompt}")
    print("=" * 60)
    
    results = []
    
    for spec in model_specs:
        try:
            provider, model = spec.split(':', 1)
            print(f"\n테스트 중: {provider}/{model}")
            
            # LLM 클라이언트 생성
            openai_key = os.getenv('OPENAI_API_KEY', '')
            gemini_key = os.getenv('GEMINI_API_KEY', '')
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            
            llm = get_or_create_llm(provider, model, openai_key, gemini_key, ollama_host)
            
            # 성능 측정
            start_time = time.time()
            message = ChatMessage(role="user", content=test_prompt)
            response = llm.chat([message])
            end_time = time.time()
            
            response_time = end_time - start_time
            response_length = len(response.content)
            
            result = {
                'provider': provider,
                'model': model,
                'response_time': response_time,
                'response_length': response_length,
                'response_content': response.content[:200] + "..." if len(response.content) > 200 else response.content,
                'usage': getattr(response, 'usage', {})
            }
            
            results.append(result)
            
            print(f"  응답 시간: {response_time:.2f}초")
            print(f"  응답 길이: {response_length} 문자")
            print(f"  응답 내용: {result['response_content']}")
            
            if result['usage']:
                tokens = result['usage'].get('total_tokens', 'N/A')
                print(f"  토큰 사용량: {tokens}")
        
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            continue
    
    # 결과 요약
    if results:
        print("\n" + "=" * 60)
        print("벤치마크 결과 요약")
        print("=" * 60)
        
        # 응답 시간 순으로 정렬
        results.sort(key=lambda x: x['response_time'])
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['provider']}/{result['model']}: {result['response_time']:.2f}초")
        
        return results
    else:
        print("벤치마크 결과가 없습니다.")
        return []


def main():
    parser = argparse.ArgumentParser(
        description='AI 모델 라우터 및 관리 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='사용할 명령')
    
    # list 명령
    list_parser = subparsers.add_parser('list', help='사용 가능한 모델 목록')
    list_parser.add_argument('--provider', choices=['openai', 'gemini', 'ollama'], help='특정 제공자만 표시')
    
    # test 명령
    test_parser = subparsers.add_parser('test', help='모델 연결 테스트')
    test_parser.add_argument('provider', choices=['openai', 'gemini', 'ollama'], help='AI 제공자')
    test_parser.add_argument('model', help='모델명')
    
    # chat 명령
    chat_parser = subparsers.add_parser('chat', help='모델과 직접 채팅')
    chat_parser.add_argument('--provider', choices=['openai', 'gemini', 'ollama'], required=True, help='AI 제공자')
    chat_parser.add_argument('--model', required=True, help='모델명')
    
    # benchmark 명령
    benchmark_parser = subparsers.add_parser('benchmark', help='모델 성능 벤치마크')
    benchmark_parser.add_argument('--models', required=True, help='테스트할 모델들 (형식: provider:model,provider:model)')
    benchmark_parser.add_argument('--prompt', default="Explain what AI is in 50 words.", help='테스트 프롬프트')
    benchmark_parser.add_argument('--output', help='결과 저장 파일명 (JSON)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            list_models(args.provider)
        
        elif args.command == 'test':
            success = test_model(args.provider, args.model)
            sys.exit(0 if success else 1)
        
        elif args.command == 'chat':
            interactive_chat(args.provider, args.model)
        
        elif args.command == 'benchmark':
            model_specs = [spec.strip() for spec in args.models.split(',')]
            results = benchmark_models(model_specs, args.prompt)
            
            if args.output and results:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump({
                        'test_prompt': args.prompt,
                        'timestamp': time.time(),
                        'results': results
                    }, f, ensure_ascii=False, indent=2, default=str)
                print(f"\n벤치마크 결과가 {args.output}에 저장되었습니다.")
    
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()