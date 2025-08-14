# 유튜브 채널 영상 요약 CLI 도구 사용법

## 개요

`channel_cli.py`는 유튜브 채널에서 특정 기간 동안 업로드된 영상들을 자동으로 수집하고 요약하는 독립적인 CLI 도구입니다.

## 기능

- 유튜브 채널 URL로부터 특정 기간 영상 목록 수집
- 다양한 날짜 형식 지원 (YYYYMMDD, today, yesterday, 숫자 등)
- 영상 정보만 출력하는 테스트 모드
- OpenAI API를 통한 자동 영상 요약
- JSON 형태로 결과 저장

## 설치 요구사항

```bash
pip install yt-dlp youtube-transcript-api requests
```

## 기본 사용법

```bash
python channel_cli.py <channel_url> <date_range> [options]
```

### 필수 인자
- `channel_url`: 유튜브 채널 URL
- `date_range`: 날짜 범위 (여러 형식 지원)

### 옵션
- `--info-only`: 영상 정보만 출력 (요약하지 않음)
- `--max-videos N`: 최대 처리할 영상 수 제한
- `--output OUTPUT`: 결과 저장 파일명 (JSON)
- `--api-key API_KEY`: OpenAI API 키 (환경변수 `OPENAI_API_KEY`도 사용 가능)

## 사용 예시

### 1. 영상 정보만 확인 (테스트)

```bash
# 오늘 업로드된 영상 확인
python channel_cli.py "https://www.youtube.com/@kurzgesagt" today --info-only

# 7일 전부터 오늘까지 영상 확인 (최대 5개)
python channel_cli.py "https://www.youtube.com/@veritasium" 7 --info-only --max-videos 5

# 특정 기간 영상 확인
python channel_cli.py "https://www.youtube.com/@channelname" 20250801-20250810 --info-only
```

### 2. 영상 요약 생성

```bash
# API 키를 환경변수로 설정
export OPENAI_API_KEY="your-openai-api-key"

# 최근 7일간 영상 요약
python channel_cli.py "https://www.youtube.com/@kurzgesagt" 7

# API 키를 직접 전달
python channel_cli.py "https://www.youtube.com/@channelname" yesterday --api-key "your-api-key"

# 결과를 특정 파일에 저장
python channel_cli.py "https://www.youtube.com/@channelname" 30 --output my_summary.json
```

## 날짜 형식

다양한 날짜 형식을 지원합니다:

- `today`: 오늘 업로드된 영상
- `yesterday`: 어제 업로드된 영상  
- `7`: 7일 전부터 오늘까지
- `20250810`: 2025년 8월 10일 하루
- `20250801-20250810`: 2025년 8월 1일부터 10일까지

## 출력 예시

### 정보 출력 모드 (--info-only)

```
채널: Kurzgesagt – In a Nutshell
기간: 2025-07-15 ~ 2025-08-15
영상 정보를 가져오는 중...

찾은 영상 수: 2
================================================================================
1. Alcohol is AMAZING
   업로드: 2025-08-12
   재생시간: 15분 1초
   조회수: 2,667,204
   URL: https://www.youtube.com/watch?v=aOwmt39L2IQ
   설명: Discover Odoo 👉 https://www.odoo.com/r/GpxF...

2. Let's Kill You a Billion Times to Make You Immortal
   업로드: 2025-07-29
   재생시간: 12분 34초
   조회수: 2,917,312
   URL: https://www.youtube.com/watch?v=7wK4peez9zE
   설명: Go to https://ground.news/KiN to get 40% off...
```

### 요약 모드

```
채널: Kurzgesagt – In a Nutshell
기간: 2025-07-15 ~ 2025-08-15
영상 정보를 가져오는 중...

찾은 영상 수: 2
OpenAI API를 사용하여 요약을 생성합니다.

[1/2] 요약 중: Alcohol is AMAZING
  요약 완료

[2/2] 요약 중: Let's Kill You a Billion Times to Make You Immortal
  요약 완료

결과가 channel_summary_20250814_123456.json에 저장되었습니다.
```

## 출력 파일 형식

JSON 파일에는 다음 정보가 저장됩니다:

```json
{
  "generated_at": "2025-08-14T12:34:56",
  "total_videos": 2,
  "summarized_videos": 2,
  "videos": [
    {
      "id": "aOwmt39L2IQ",
      "title": "Alcohol is AMAZING",
      "url": "https://www.youtube.com/watch?v=aOwmt39L2IQ",
      "upload_date": "2025-08-12T00:00:00",
      "duration": 901,
      "view_count": 2667204,
      "description": "Discover Odoo..."
    }
  ],
  "summaries": {
    "aOwmt39L2IQ": {
      "title": "Alcohol is AMAZING",
      "url": "https://www.youtube.com/watch?v=aOwmt39L2IQ",
      "upload_date": "2025-08-12T00:00:00",
      "summary": "## 📝 영상 요약\n\n### 🔑 핵심 내용\n..."
    }
  }
}
```

## 지원하는 채널 URL 형식

- `https://www.youtube.com/@channelname`
- `https://www.youtube.com/channel/UCxxxxxxxxxx`
- `https://www.youtube.com/c/channelname`

## 주의사항

1. **API 키**: 요약 기능을 사용하려면 유효한 OpenAI API 키가 필요합니다.

2. **자막**: 요약은 영상의 자막을 기반으로 생성됩니다. 자막이 없는 영상은 요약할 수 없습니다.

3. **속도 제한**: OpenAI API 호출 제한에 따라 많은 영상을 처리할 때 시간이 걸릴 수 있습니다.

4. **언어 우선순위**: 한국어 → 영어 → 일본어 순으로 자막을 찾습니다.

## 문제해결

### 영상을 찾을 수 없는 경우
```bash
해당 기간에 업로드된 영상이 없습니다.
```
→ 날짜 범위를 넓히거나 다른 기간을 시도해보세요.

### API 키 오류
```bash
오류: OpenAI API 키가 필요합니다.
```
→ 환경변수를 설정하거나 `--api-key` 옵션을 사용하세요.

### 자막 수집 실패
```bash
트랜스크립트를 찾을 수 없습니다.
```
→ 해당 영상에 자막이 없거나 접근할 수 없는 상태입니다.