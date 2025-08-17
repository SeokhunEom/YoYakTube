# YoYakTube CLI 사용법

YouTube 영상 자막 추출, 요약, Q&A 챗봇 기능을 제공하는 통합 명령줄 도구입니다.

## 📋 목차
- [설치 및 설정](#설치-및-설정)
- [기본 사용법](#기본-사용법)
- [자막 추출](#자막-추출)
- [영상 요약](#영상-요약)
- [대화형 챗봇](#대화형-챗봇)
- [AI 모델 관리](#ai-모델-관리)
- [메타데이터 추출](#메타데이터-추출)
- [설정 관리](#설정-관리)
- [사용 예시](#사용-예시)

---

## 🚀 설치 및 설정

### 필수 요구사항
```bash
pip install -r requirements.txt
```

### 환경 변수 설정
```bash
# OpenAI API 키 설정 (필수)
export OPENAI_API_KEY="your-openai-api-key"

# 선택사항: 설정 파일 경로
export YYT_CONFIG="./config.json"
```

### 지원 AI 모델
- **gpt-5-mini** (기본값) - 빠르고 효율적인 모델
- **gpt-5** - 고성능 모델
- **gpt-5-nano** - 경량 모델

---

## 🎯 기본 사용법

```bash
# 메인 CLI 실행
python -m cli

# 도움말 보기
python -m cli --help

# 특정 명령어 도움말
python -m cli transcript --help
```

---

## 📝 자막 추출

YouTube 영상에서 자막을 추출합니다.

### 기본 명령어
```bash
python -m cli transcript <video_url_or_id>
```

### 옵션
- `--languages`: 선호 언어 순서 (기본값: ko,en,ja)
- `--format`: 출력 형식 (text, json, srt)
- `--output`: 출력 파일명
- `--timestamps/--no-timestamps`: 타임스탬프 포함 여부

### 사용 예시
```bash
# 기본 텍스트 형식으로 자막 추출
python -m cli transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 타임스탬프 포함 텍스트
python -m cli transcript "dQw4w9WgXcQ" --timestamps

# JSON 형식으로 저장
python -m cli transcript "dQw4w9WgXcQ" --format json --output transcript.json

# SRT 자막 파일 생성
python -m cli transcript "dQw4w9WgXcQ" --format srt --output subtitle.srt

# 영어 우선으로 자막 추출
python -m cli transcript "dQw4w9WgXcQ" --languages en,ko,ja
```

---

## 📊 영상 요약

YouTube 영상이나 자막 파일을 AI로 요약합니다.

### 기본 명령어
```bash
python -m cli summarize <video_url_or_id>
```

### 입력 소스
- 영상 URL 또는 비디오 ID
- `--file`: 파일에서 자막 읽기
- `--stdin`: 표준 입력에서 자막 읽기

### 옵션
- `--provider`: AI 제공자 (기본값: openai)
- `--model`: 사용할 모델명 (기본값: gpt-5-mini)
- `--output`: 출력 파일명
- `--languages`: 자막 언어 우선순위

### 사용 예시
```bash
# 기본 요약
python -m cli summarize "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# GPT-5로 요약
python -m cli summarize "dQw4w9WgXcQ" --model gpt-5

# 요약 결과를 파일로 저장
python -m cli summarize "dQw4w9WgXcQ" --output summary.md

# 파일에서 자막 읽어서 요약
python -m cli summarize --file transcript.txt

# 표준 입력에서 요약
cat transcript.txt | python -m cli summarize --stdin
```

---

## 💬 대화형 챗봇

영상 자막을 바탕으로 Q&A 챗봇을 실행합니다.

### 기본 명령어
```bash
python -m cli chat <video_url_or_id>
```

### 모드
- `--interactive`: 대화형 모드 (연속 질문 가능)
- `--question`: 단일 질문

### 옵션
- `--file`: 파일에서 자막 읽기
- `--provider`: AI 제공자 (기본값: openai)
- `--model`: 사용할 모델명 (기본값: gpt-5-mini)

### 사용 예시
```bash
# 대화형 모드
python -m cli chat "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --interactive

# 단일 질문
python -m cli chat "dQw4w9WgXcQ" --question "이 영상의 주요 내용은 무엇인가요?"

# 파일에서 자막을 읽어서 대화
python -m cli chat --file transcript.txt --interactive

# GPT-5로 대화
python -m cli chat "dQw4w9WgXcQ" --model gpt-5 --interactive
```

---

## 🤖 AI 모델 관리

사용 가능한 AI 모델을 관리하고 테스트합니다.

### 모델 목록 보기
```bash
python -m cli ai list

# 특정 제공자만 보기
python -m cli ai list --provider openai
```

### 모델 연결 테스트
```bash
python -m cli ai test openai gpt-5-mini

# 커스텀 프롬프트로 테스트
python -m cli ai test openai gpt-5 --prompt "안녕하세요, 테스트입니다."
```

### 직접 AI와 대화
```bash
python -m cli ai chat --provider openai --model gpt-5-mini
```

### 모델 성능 벤치마크
```bash
# 기본 모델들 벤치마크
python -m cli ai benchmark

# 특정 모델들만 테스트
python -m cli ai benchmark --models "gpt-5-mini,gpt-5"

# 결과를 파일로 저장
python -m cli ai benchmark --output benchmark_results.json
```

---

## 📋 메타데이터 추출

YouTube 영상의 메타데이터를 추출합니다.

```bash
python -m cli meta "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

출력 예시:
```json
{
  "id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "uploader": "Rick Astley",
  "duration": 212,
  "view_count": 1000000000,
  "upload_date": "20091025"
}
```

---

## ⚙️ 설정 관리

### 현재 설정 확인
```bash
python -m cli config show
```

### 파이프라인 명령어
```bash
# 채널 영상 일괄 요약 (미구현)
python -m cli pipeline channel-summary "https://www.youtube.com/@channelname"

# 완전한 영상 분석 (미구현)
python -m cli pipeline full-analysis "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

## 🎯 사용 예시

### 1. 영상 완전 분석 워크플로우
```bash
# 1단계: 메타데이터 확인
python -m cli meta "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 2단계: 자막 추출
python -m cli transcript "dQw4w9WgXcQ" --format json --output transcript.json

# 3단계: 요약 생성
python -m cli summarize "dQw4w9WgXcQ" --output summary.md

# 4단계: 대화형 Q&A
python -m cli chat "dQw4w9WgXcQ" --interactive
```

### 2. 배치 처리 예시
```bash
# 여러 영상의 자막을 SRT로 저장
for video in "dQw4w9WgXcQ" "another_video_id"; do
    python -m cli transcript "$video" --format srt --output "${video}.srt"
done

# 파일들을 일괄 요약
for file in *.txt; do
    python -m cli summarize --file "$file" --output "${file%.txt}_summary.md"
done
```

### 3. 고급 사용법
```bash
# 파이프라인 사용
youtube-dl --write-sub --skip-download "video_url" | \
python -m cli summarize --stdin --model gpt-5 --output advanced_summary.md

# 설정 파일을 통한 모델 관리
echo '{"default_model": "gpt-5", "temperature": 0.1}' > config.json
export YYT_CONFIG="./config.json"
python -m cli summarize "dQw4w9WgXcQ"
```

---

## ❗ 주의사항

1. **API 키 필수**: OpenAI API 키가 환경변수에 설정되어 있어야 합니다.
2. **네트워크 연결**: YouTube API와 OpenAI API 접근이 필요합니다.
3. **자막 가용성**: 모든 YouTube 영상에 자막이 있는 것은 아닙니다.
4. **사용량 제한**: OpenAI API 사용량에 따른 비용이 발생할 수 있습니다.

---

## 🔧 문제 해결

### 자주 발생하는 오류

**"Error: OPENAI_API_KEY environment variable is required"**
```bash
export OPENAI_API_KEY="your-api-key"
```

**"Error: Could not extract transcript"**
- 해당 영상에 자막이 없거나 비공개 영상일 수 있습니다.
- 다른 언어로 시도해보세요: `--languages en,ko,ja`

**"Error: Invalid video URL or ID"**
- YouTube URL 형식을 확인하세요.
- 비디오 ID만 사용해도 됩니다: `dQw4w9WgXcQ`

---

## 📚 추가 정보

- API 문서: `api_doc.md` 참조
- 프로젝트 설정: `CLAUDE.md` 참조
- 테스트: `python run_tests.py`