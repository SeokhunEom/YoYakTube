# YoYakTube CLI 도구들

YoYakTube의 각 기능을 모듈별로 분리한 CLI 도구 모음입니다.

## 📋 CLI 도구 목록

### 1. `yyt_channel.py` - 채널 영상 리스트 추출
YouTube 채널의 영상 목록을 날짜별로 필터링하여 추출합니다.

```bash
# 채널의 최근 7일 영상
python -m cli.yyt_channel "@channelname" --days 7

# 특정 기간 영상
python -m cli.yyt_channel "https://www.youtube.com/channel/UCxxxx" --date-range 20250810-20250812

# JSON 형식으로 저장
python -m cli.yyt_channel "@channelname" --days 7 --format json --output videos.json
```

### 2. `yyt_transcript.py` - 영상 자막 추출
YouTube 영상의 자막을 다양한 형식으로 추출합니다.

```bash
# 기본 텍스트 형식
python -m cli.yyt_transcript "https://www.youtube.com/watch?v=VIDEO_ID"

# SRT 형식
python -m cli.yyt_transcript VIDEO_ID --format srt --output subtitle.srt

# 타임스탬프 포함 텍스트
python -m cli.yyt_transcript VIDEO_ID --timestamps --output transcript.txt

# JSON 형식 (메타데이터 포함)
python -m cli.yyt_transcript VIDEO_ID --format json
```

### 3. `yyt_meta.py` - 영상 메타데이터 추출
YouTube 영상의 상세 메타데이터를 추출합니다.

```bash
# 테이블 형식 출력
python -m cli.yyt_meta "https://www.youtube.com/watch?v=VIDEO_ID"

# JSON 형식
python -m cli.yyt_meta VIDEO_ID --json --output metadata.json

# 특정 필드만 추출
python -m cli.yyt_meta VIDEO_ID --fields title,uploader,duration,view_count

# 사용 가능한 필드 목록
python -m cli.yyt_meta --list-fields
```

### 4. `yyt_summarize.py` - 자막 요약
자막을 AI로 요약합니다.

```bash
# 영상 URL로 요약
python -m cli.yyt_summarize "https://www.youtube.com/watch?v=VIDEO_ID"

# 파일에서 자막 읽어서 요약
python -m cli.yyt_summarize --file transcript.txt

# 표준 입력에서 자막 읽기
cat transcript.txt | python -m cli.yyt_summarize --stdin

# AI 모델 지정
python -m cli.yyt_summarize VIDEO_URL --provider openai --model gpt-5

# 결과를 파일로 저장
python -m cli.yyt_summarize VIDEO_URL --output summary.md
```

### 5. `yyt_chat.py` - 자막 기반 Q&A 챗봇
자막을 기반으로 질의응답을 진행합니다.

```bash
# 대화형 채팅
python -m cli.yyt_chat "https://www.youtube.com/watch?v=VIDEO_ID" --interactive

# 단일 질문
python -m cli.yyt_chat VIDEO_URL --question "이 영상의 주요 내용은 무엇인가요?"

# 파일 기반 채팅
python -m cli.yyt_chat --file transcript.txt --interactive

# AI 모델 지정
python -m cli.yyt_chat VIDEO_URL --provider gemini --model gemini-2.5-flash
```

### 6. `yyt_ai.py` - AI 모델 라우터 및 관리
AI 모델을 관리하고 테스트합니다.

```bash
# 사용 가능한 모델 목록
python -m cli.yyt_ai list

# 특정 제공자 모델만 나열
python -m cli.yyt_ai list --provider openai

# 모델 연결 테스트
python -m cli.yyt_ai test openai gpt-5-mini

# 모델과 직접 채팅
python -m cli.yyt_ai chat --provider gemini --model gemini-2.5-flash

# 모델 성능 벤치마크
python -m cli.yyt_ai benchmark --models "openai:gpt-5-mini,gemini:gemini-2.5-flash"
```

### 7. `yyt_config.py` - 설정 관리
YoYakTube 설정을 관리합니다.

```bash
# 현재 설정 보기
python -m cli.yyt_config show

# 기본 설정 파일 생성
python -m cli.yyt_config init

# 설정 값 변경
python -m cli.yyt_config set providers "openai,gemini"
python -m cli.yyt_config set models.openai "gpt-5"

# 특정 설정 값 조회
python -m cli.yyt_config get providers

# 설정 유효성 검사
python -m cli.yyt_config validate
```

### 8. `yyt.py` - 통합 CLI 인터페이스
모든 CLI 도구를 통합한 인터페이스입니다.

```bash
# 기본 워크플로우: 영상 URL -> 요약
python -m cli.yyt summarize "https://www.youtube.com/watch?v=VIDEO_ID"

# 완전한 분석 파이프라인
python -m cli.yyt pipeline full-analysis VIDEO_URL --output-dir ./results

# 개별 도구 실행
python -m cli.yyt transcript VIDEO_URL --format srt
python -m cli.yyt meta VIDEO_URL --json
python -m cli.yyt ai list
python -m cli.yyt config show
```

## 🔧 설정

### 환경변수 설정
CLI 도구들을 사용하기 전에 필요한 API 키를 환경변수로 설정하세요:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export OLLAMA_HOST="http://localhost:11434"  # Ollama 사용시
```

### 설정 파일 생성
기본 설정 파일을 생성하려면:

```bash
python -m cli.yyt_config init
```

이 명령은 `yoyaktube.config.json` 파일을 현재 디렉토리에 생성합니다.

## 🚀 워크플로우 예시

### 1. 기본 영상 분석 워크플로우
```bash
# 1. 영상 메타데이터 확인
python -m cli.yyt_meta "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. 자막 추출
python -m cli.yyt_transcript VIDEO_ID --output transcript.txt

# 3. 요약 생성
python -m cli.yyt_summarize VIDEO_ID --output summary.md

# 4. 질의응답
python -m cli.yyt_chat VIDEO_ID --interactive
```

### 2. 채널 일괄 분석 워크플로우
```bash
# 1. 채널 영상 리스트 추출
python -m cli.yyt_channel "@channelname" --days 7 --format json --output videos.json

# 2. 각 영상별로 분석 (스크립트 작성 필요)
# videos.json을 파싱하여 각 영상에 대해 요약 실행
```

### 3. 완전 자동화 워크플로우
```bash
# 통합 파이프라인으로 모든 단계 실행
python -m cli.yyt pipeline full-analysis "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir ./analysis_results
```

## 📁 파일 구조

```
cli/
├── __init__.py
├── README.md
├── yyt.py              # 통합 CLI 인터페이스
├── yyt_channel.py      # 채널 영상 리스트 추출
├── yyt_transcript.py   # 영상 자막 추출
├── yyt_meta.py         # 영상 메타데이터 추출
├── yyt_summarize.py    # 자막 요약
├── yyt_chat.py         # 자막 기반 Q&A 챗봇
├── yyt_ai.py           # AI 모델 관리
└── yyt_config.py       # 설정 관리
```

## 🔍 문제해결

### 일반적인 문제들

1. **모듈을 찾을 수 없음 오류**
   ```bash
   # 프로젝트 루트 디렉토리에서 실행하세요
   cd /path/to/YoYakTube
   python -m cli.yyt_transcript VIDEO_ID
   ```

2. **API 키 오류**
   ```bash
   # 환경변수가 올바르게 설정되었는지 확인
   python -m cli.yyt_config validate
   ```

3. **자막을 찾을 수 없음**
   ```bash
   # 다른 언어로 시도
   python -m cli.yyt_transcript VIDEO_ID --languages en,ja,ko
   ```

## 💡 팁

- 모든 CLI 도구는 `--verbose` 옵션으로 상세 정보를 출력할 수 있습니다.
- JSON 형식 출력은 다른 도구와 파이프라인으로 연결하기 좋습니다.
- 대용량 채널 분석시에는 `--max-videos` 옵션으로 제한하세요.
- 정기적으로 `python -m cli.yyt_config validate`로 설정을 검증하세요.