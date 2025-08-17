#!/usr/bin/env python3
"""
테스트 실행 도우미 스크립트

TDD 개발 과정에서 테스트 실행 및 결과 분석을 도와줍니다.
"""

import subprocess
import sys
import os

def run_pytest_with_summary():
    """pytest 실행하고 결과 요약"""
    print("🚀 YoYakTube 테스트 실행 시작\n")
    
    # pytest 실행
    try:
        result = subprocess.run([
            "pytest", "tests/", 
            "-v", 
            "--tb=short",  # 짧은 트레이스백
            "--disable-warnings"  # 경고 숨기기
        ], capture_output=True, text=True, timeout=60)
        
        print("📊 테스트 실행 결과:")
        print("=" * 50)
        
        # 성공/실패 개수 파싱
        output_lines = result.stdout.split('\n')
        summary_line = [line for line in output_lines if 'failed' in line and 'in' in line]
        
        if summary_line:
            print(summary_line[-1])
        
        # 실패한 테스트들 카테고리별로 분류
        failed_tests = {}
        
        for line in output_lines:
            if "FAILED" in line and "::" in line:
                # "tests/test_cli.py::TestClass::test_method FAILED" 형태에서 파일명만 추출
                test_path = line.split("::")[0].strip()
                
                # tests/ 경로가 있으면 제거하여 파일명만 남김
                if test_path.startswith("tests/"):
                    test_file = test_path[6:]  # "tests/" 제거
                else:
                    test_file = test_path
                
                if test_file not in failed_tests:
                    failed_tests[test_file] = 0
                failed_tests[test_file] += 1
        
        print("\n📋 실패한 테스트 파일별 현황:")
        for file_name, count in failed_tests.items():
            print(f"  - {file_name}: {count}개 실패")
        
        print(f"\n📈 총 실패한 테스트 파일: {len(failed_tests)}개")
        
        # 주요 에러 유형 분석
        error_types = {}
        stderr_lines = result.stderr.split('\n')
        
        for line in stderr_lines:
            if "ModuleNotFoundError" in line:
                module = line.split("'")[1] if "'" in line else "unknown"
                error_types[f"ModuleNotFoundError: {module}"] = error_types.get(f"ModuleNotFoundError: {module}", 0) + 1
            elif "ImportError" in line:
                error_types["ImportError"] = error_types.get("ImportError", 0) + 1
        
        if error_types:
            print("\n🔍 주요 에러 유형:")
            for error, count in error_types.items():
                print(f"  - {error}: {count}회")
        
        print("\n" + "=" * 50)
        print("🎯 현재 상태: TDD Red Phase (테스트 실패 단계)")
        print("📝 다음 단계: 실제 모듈 구현 (Green Phase)")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ 테스트 실행 시간 초과 (60초)")
        return False
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        return False

def analyze_test_structure():
    """테스트 구조 분석"""
    print("\n🔍 테스트 구조 분석:")
    print("=" * 30)
    
    test_files = []
    tests_dir = "tests"
    
    if os.path.exists(tests_dir):
        for file in os.listdir(tests_dir):
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(file)
    
    print(f"📁 테스트 파일 개수: {len(test_files)}")
    for file in sorted(test_files):
        file_path = os.path.join(tests_dir, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 테스트 클래스와 메서드 개수 세기
        test_classes = content.count("class Test")
        test_methods = content.count("def test_")
        
        print(f"  - {file}: {test_classes}개 클래스, {test_methods}개 테스트")

def show_next_steps():
    """다음 단계 안내"""
    print("\n📋 TDD 다음 단계 가이드:")
    print("=" * 40)
    print("1. 🔴 Red Phase (현재): 테스트 작성 완료, 모든 테스트 실패")
    print("2. 🟢 Green Phase (다음): 최소한의 코드로 테스트 통과시키기")
    print("3. 🔵 Refactor Phase: 코드 품질 개선")
    
    print("\n🏗️  구현해야 할 모듈들:")
    modules_to_implement = [
        "yoyaktube/__init__.py",
        "yoyaktube/utils.py (extract_video_id, format_hms, build_llm_summary_context)",
        "yoyaktube/transcript.py (collect_transcript, collect_transcript_entries)",
        "yoyaktube/metadata.py (fetch_video_metadata)",
        "yoyaktube/llm.py (OpenAIClient, get_or_create_llm)",
        "cli/ 패키지 (yyt_transcript, yyt_summarize, yyt_chat, yyt_ai)"
    ]
    
    for i, module in enumerate(modules_to_implement, 1):
        print(f"  {i}. {module}")
    
    print("\n💡 권장 구현 순서:")
    print("  1. yoyaktube/__init__.py (패키지 초기화)")
    print("  2. yoyaktube/utils.py (유틸리티 함수들)")
    print("  3. yoyaktube/transcript.py (자막 추출)")
    print("  4. yoyaktube/metadata.py (메타데이터 추출)")
    print("  5. yoyaktube/llm.py (LLM 클라이언트)")
    print("  6. cli/ 모듈들 (CLI 인터페이스)")

def main():
    """메인 함수"""
    print("🧪 YoYakTube TDD 테스트 러너")
    print("=" * 50)
    
    # 테스트 구조 분석
    analyze_test_structure()
    
    # 테스트 실행
    success = run_pytest_with_summary()
    
    # 다음 단계 안내
    show_next_steps()
    
    print(f"\n🎉 테스트 러너 완료!")
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)