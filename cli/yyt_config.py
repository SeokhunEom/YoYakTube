#!/usr/bin/env python3
"""
YoYakTube 설정 관리 CLI

Usage:
    python -m cli.yyt_config [command] [options]
    
Commands:
    show                    현재 설정 출력
    init                    기본 설정 파일 생성
    set <key> <value>       설정 값 변경
    get <key>               특정 설정 값 조회
    validate               설정 유효성 검사
    
Examples:
    # 현재 설정 보기
    python -m cli.yyt_config show
    
    # 설정 파일 생성
    python -m cli.yyt_config init
    
    # 제공자 설정
    python -m cli.yyt_config set providers "openai,gemini"
    
    # 특정 값 조회
    python -m cli.yyt_config get providers
    
    # 설정 유효성 검사
    python -m cli.yyt_config validate
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 부모 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from yoyaktube.config import get_config, get_available_providers


def get_config_file_path() -> Path:
    """설정 파일 경로 반환"""
    # YYT_CONFIG 환경변수 확인
    env_config = os.getenv('YYT_CONFIG')
    if env_config:
        return Path(env_config)
    
    # 현재 작업 디렉토리의 yoyaktube.config.json
    return Path.cwd() / 'yoyaktube.config.json'


def load_config_file() -> Dict[str, Any]:
    """설정 파일 로드"""
    config_path = get_config_file_path()
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"설정 파일을 읽을 수 없습니다: {e}")


def save_config_file(config: Dict[str, Any]):
    """설정 파일 저장"""
    config_path = get_config_file_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"설정이 {config_path}에 저장되었습니다.")
    except Exception as e:
        raise ValueError(f"설정 파일을 저장할 수 없습니다: {e}")


def get_default_config() -> Dict[str, Any]:
    """기본 설정 반환"""
    return {
        "providers": ["openai", "gemini", "ollama"],
        "models": {
            "openai": "gpt-5-mini",
            "gemini": "gemini-2.5-flash",
            "ollama": "llama2"
        },
        "api_settings": {
            "timeout": 60,
            "retry_attempts": 3,
            "temperature": 0.2
        },
        "transcript_settings": {
            "languages": ["ko", "en", "ja"],
            "cache_ttl": 3600
        },
        "output_settings": {
            "default_format": "markdown",
            "include_timestamps": True
        }
    }


def show_config():
    """현재 설정 출력"""
    print("=" * 60)
    print("YoYakTube 현재 설정")
    print("=" * 60)
    
    # 설정 파일 경로
    config_path = get_config_file_path()
    print(f"설정 파일: {config_path}")
    print(f"파일 존재: {'예' if config_path.exists() else '아니오'}")
    
    # 환경변수 확인
    print("\n[환경변수]")
    env_vars = [
        'YYT_CONFIG', 'YYT_PROVIDERS', 'OPENAI_API_KEY', 
        'GEMINI_API_KEY', 'OLLAMA_HOST'
    ]
    for var in env_vars:
        value = os.getenv(var, '')
        if var.endswith('_KEY'):
            display_value = '*' * len(value) if value else '(없음)'
        else:
            display_value = value if value else '(없음)'
        print(f"  {var}: {display_value}")
    
    # 실제 적용되는 설정
    print("\n[적용되는 설정]")
    try:
        config = get_config()
        print(json.dumps(config, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"설정을 가져올 수 없습니다: {e}")
    
    # 사용 가능한 제공자
    print("\n[사용 가능한 제공자]")
    try:
        providers = get_available_providers()
        print(f"  {', '.join(providers)}")
    except Exception as e:
        print(f"제공자 정보를 가져올 수 없습니다: {e}")


def init_config():
    """기본 설정 파일 생성"""
    config_path = get_config_file_path()
    
    if config_path.exists():
        response = input(f"설정 파일이 이미 존재합니다 ({config_path}). 덮어쓰시겠습니까? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("설정 파일 생성을 취소했습니다.")
            return
    
    default_config = get_default_config()
    save_config_file(default_config)
    
    print("기본 설정 파일이 생성되었습니다.")
    print("\n설정을 완료하려면 다음 환경변수를 설정하세요:")
    print("  export OPENAI_API_KEY='your-openai-api-key'")
    print("  export GEMINI_API_KEY='your-gemini-api-key'")
    print("  export OLLAMA_HOST='http://localhost:11434'  # 필요한 경우")


def set_config_value(key: str, value: str):
    """설정 값 변경"""
    config = load_config_file()
    
    # 키가 중첩된 경우 처리 (예: models.openai)
    keys = key.split('.')
    current = config
    
    # 마지막 키를 제외한 경로 생성
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # 값 타입 변환
    final_key = keys[-1]
    
    # 특수 처리가 필요한 값들
    if key == 'providers':
        # 쉼표로 구분된 리스트로 변환
        current[final_key] = [p.strip() for p in value.split(',')]
    elif key in ['api_settings.timeout', 'api_settings.retry_attempts', 'transcript_settings.cache_ttl']:
        # 정수 값
        current[final_key] = int(value)
    elif key == 'api_settings.temperature':
        # 실수 값
        current[final_key] = float(value)
    elif key == 'transcript_settings.languages':
        # 언어 리스트
        current[final_key] = [lang.strip() for lang in value.split(',')]
    elif value.lower() in ['true', 'false']:
        # 불린 값
        current[final_key] = value.lower() == 'true'
    else:
        # 문자열 값
        current[final_key] = value
    
    save_config_file(config)
    print(f"설정 '{key}'가 '{value}'로 변경되었습니다.")


def get_config_value(key: str):
    """특정 설정 값 조회"""
    try:
        config = get_config()
        
        # 키가 중첩된 경우 처리
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                print(f"설정 키 '{key}'를 찾을 수 없습니다.")
                return
        
        if isinstance(current, list):
            print(','.join(str(item) for item in current))
        else:
            print(current)
    
    except Exception as e:
        print(f"설정을 가져올 수 없습니다: {e}")


def validate_config():
    """설정 유효성 검사"""
    print("설정 유효성 검사 중...")
    
    try:
        config = get_config()
        issues = []
        
        # 제공자 검사
        providers = config.get('providers', [])
        if not providers:
            issues.append("제공자가 설정되지 않았습니다.")
        
        valid_providers = ['openai', 'gemini', 'ollama']
        for provider in providers:
            if provider not in valid_providers:
                issues.append(f"알 수 없는 제공자: {provider}")
        
        # API 키 검사
        if 'openai' in providers and not os.getenv('OPENAI_API_KEY'):
            issues.append("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        if 'gemini' in providers and not os.getenv('GEMINI_API_KEY'):
            issues.append("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        # 모델 설정 검사
        models = config.get('models', {})
        for provider in providers:
            if provider not in models:
                issues.append(f"{provider} 제공자의 모델이 설정되지 않았습니다.")
        
        # 결과 출력
        if issues:
            print("\n❌ 발견된 문제:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ 설정이 올바릅니다.")
        
        return len(issues) == 0
    
    except Exception as e:
        print(f"❌ 설정 검사 중 오류 발생: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='YoYakTube 설정 관리 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='사용할 명령')
    
    # show 명령
    subparsers.add_parser('show', help='현재 설정 출력')
    
    # init 명령
    subparsers.add_parser('init', help='기본 설정 파일 생성')
    
    # set 명령
    set_parser = subparsers.add_parser('set', help='설정 값 변경')
    set_parser.add_argument('key', help='설정 키 (예: providers, models.openai)')
    set_parser.add_argument('value', help='설정 값')
    
    # get 명령
    get_parser = subparsers.add_parser('get', help='특정 설정 값 조회')
    get_parser.add_argument('key', help='설정 키')
    
    # validate 명령
    subparsers.add_parser('validate', help='설정 유효성 검사')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'show':
            show_config()
        
        elif args.command == 'init':
            init_config()
        
        elif args.command == 'set':
            set_config_value(args.key, args.value)
        
        elif args.command == 'get':
            get_config_value(args.key)
        
        elif args.command == 'validate':
            success = validate_config()
            sys.exit(0 if success else 1)
    
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()