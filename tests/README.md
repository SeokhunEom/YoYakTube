# YoYakTube CLI 테스트 가이드

이 디렉토리는 YoYakTube CLI 도구들의 테스트 코드를 포함합니다.

## 테스트 구조

```
tests/
├── __init__.py                 # 테스트 패키지 초기화
├── conftest.py                 # 공통 테스트 설정 및 유틸리티
├── run_tests.py               # 테스트 실행기
├── README.md                  # 이 파일
├── test_yyt.py               # 메인 CLI 인터페이스 테스트
├── test_yyt_ai.py            # AI 모델 관리 테스트
├── test_yyt_channel.py       # 채널 영상 리스트 추출 테스트
├── test_yyt_chat.py          # Q&A 챗봇 테스트
├── test_yyt_config.py        # 설정 관리 테스트
├── test_yyt_meta.py          # 메타데이터 추출 테스트
├── test_yyt_summarize.py     # 자막 요약 테스트
└── test_yyt_transcript.py    # 자막 추출 테스트
```

## 테스트 실행

### 모든 테스트 실행
```bash
python tests/run_tests.py
```

### 특정 테스트 모듈 실행
```bash
python tests/run_tests.py test_yyt_transcript
```

### 사용 가능한 테스트 모듈 확인
```bash
python tests/run_tests.py --list
```

### pytest 사용 (설치된 경우)
```bash
pytest tests/
pytest tests/test_yyt_transcript.py
pytest tests/ -v  # 자세한 출력
```

## 테스트 특징

### Mock 사용
- **API 호출**: 모든 외부 API 호출(OpenAI, Gemini, Ollama)은 mock으로 처리
- **네트워크 요청**: YouTube API, yt-dlp 등의 네트워크 호출도 mock
- **파일 시스템**: 파일 읽기/쓰기 작업은 필요에 따라 mock

### 테스트 범위
각 CLI 도구의 핵심 기능들을 테스트:

1. **yyt_transcript.py**
   - 자막 추출 및 포맷 변환
   - SRT, VTT, JSON, 텍스트 형식 지원
   - 타임스탬프 처리

2. **yyt_meta.py**
   - YouTube 영상 메타데이터 추출
   - JSON 및 테이블 형식 출력
   - 필드 필터링

3. **yyt_channel.py**
   - 채널 영상 리스트 추출
   - 날짜 범위 필터링
   - 최대 영상 수 제한

4. **yyt_summarize.py**
   - LLM을 이용한 자막 요약
   - 다양한 입력 소스 지원
   - 메타데이터 기반 컨텍스트 강화

5. **yyt_chat.py**
   - 자막 기반 Q&A 챗봇
   - 대화형 인터페이스
   - 채팅 히스토리 관리

6. **yyt_ai.py**
   - 사용 가능한 AI 모델 목록
   - 모델 연결 테스트
   - 대화형 채팅 및 벤치마크

7. **yyt_config.py**
   - 설정 파일 관리
   - 환경변수 처리
   - 설정 유효성 검사

8. **yyt.py**
   - 메인 CLI 인터페이스
   - 서브명령 라우팅
   - 파이프라인 실행

## 테스트 데이터

`conftest.py`에서 공통 테스트 데이터 제공:

- **sample_video_id**: "dQw4w9WgXcQ"
- **sample_transcript_text**: 샘플 자막 텍스트
- **sample_transcript_entries**: 타임스탬프가 포함된 자막 엔트리
- **sample_metadata**: 영상 메타데이터
- **sample_config**: 설정 데이터

## 환경 설정

테스트 실행 시 실제 API 키나 외부 서비스가 필요하지 않습니다. 모든 외부 의존성은 mock으로 처리됩니다.

### 필요한 패키지
테스트 실행에 필요한 기본 패키지들:
```
unittest (Python 내장)
unittest.mock (Python 내장)
pathlib (Python 내장)
```

### 선택적 패키지
더 나은 테스트 경험을 위한 선택적 패키지:
```bash
pip install pytest pytest-cov  # pytest 및 커버리지
```

## 주의사항

1. **실제 API 호출 금지**: 테스트는 실제 YouTube API나 LLM API를 호출하지 않습니다
2. **격리된 환경**: 각 테스트는 독립적으로 실행되며 서로 영향을 주지 않습니다
3. **빠른 실행**: mock 사용으로 모든 테스트가 빠르게 실행됩니다

## 새 테스트 추가

새로운 CLI 도구나 기능을 추가할 때:

1. `test_새기능.py` 파일 생성
2. `unittest.TestCase`를 상속하는 테스트 클래스 작성
3. 필요한 mock 설정
4. 핵심 기능 및 에러 케이스 테스트
5. `conftest.py`의 BaseTestCase 활용 권장