### YoYakTube — YouTube 영상 요약 & Q&A 챗봇

YoYakTube는 YouTube 영상 링크만 입력하면 자막을 수집하여 한국어로 구조화된 요약을 생성하고, 영상 내용에 대한 질의응답(Q&A)을 할 수 있는 Streamlit 앱입니다.

## 주요 기능

- **영상 링크 입력**: `https://www.youtube.com/watch?v=...` 또는 `youtu.be/...` 지원
- **자막 수집/캐시**: `youtube-transcript-api`로 자막 텍스트와 타임스탬프 엔트리 수집(`st.cache_data`로 1시간 캐시)
- **영상 메타데이터 표시**: `yt-dlp`로 제목/채널/재생시간/업로드일 추출 후 상단 캡션으로 표시
- **LLM 요약 생성**: 고밀도 한국어 요약(타임스탬프 강조 포함) 생성
- **Q&A 챗**: 생성된 요약/자막을 컨텍스트로 사용자 질문에 답변
- **다운로드**: 요약(.md), 자막(.txt), 요약+자막(.md) 저장
- **다국어 자막 우선순위**: 예) `ko,en,ja`와 같이 입력하여 우선 순위 지정

## 기술 스택

- UI: Streamlit
- LLM: OpenAI / Google Gemini / Ollama 중 선택 가능
- 자막: `youtube-transcript-api`
- 메타데이터: `yt-dlp`

## 프로젝트 구조

```
YoYakTube/
  app.py                   # 앱 시작점 (streamlit run app.py)
  requirements.txt         # 의존성 목록
  yoyaktube/
    app_main.py            # 앱 오케스트레이션(UI/흐름/잡 상태)
    ui.py                  # 사이드바/툴바/챗/메타데이터 UI
    state.py               # Streamlit 세션 상태 래퍼
    transcript.py          # 자막/타임스탬프 수집 + 캐시
    metadata.py            # yt-dlp로 영상 메타데이터 수집 + 캐시
    llm.py                 # LLM 클라이언트(OpenAI/Gemini/Ollama)
    config.py              # 사용 가능 Provider 구성 로드(파일/환경변수)
    constants.py           # 상수/프롬프트/세션 키
    i18n.py                # 한국어 UI 텍스트
    utils.py               # 유틸(영상ID 추출, 포맷팅, 마크다운 생성 등)
```

## 설치

1. Python 가상환경 권장

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. 의존성 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
streamlit run app.py
```

브라우저가 열리면 사이드바에서 LLM Provider/모델/API 키(또는 Ollama 호스트)를 설정하고, 상단 입력창에 YouTube 링크를 넣어 시작합니다.

## 구성(Providers)

앱은 다음 3가지 Provider를 지원합니다.

- OpenAI: 모델/키 필요
- Gemini: 모델/키 필요
- Ollama: 모델/호스트 필요(기본 `http://localhost:11434`)

사용 가능 Provider는 아래 우선순위로 결정됩니다.

1. 환경변수 `YYT_CONFIG`가 가리키는 JSON 파일
2. 현재 작업 디렉토리의 `yoyaktube.config.json`
3. 환경변수 `YYT_PROVIDERS` (예: `openai,gemini,ollama`)
4. 기본값: `openai, gemini, ollama`

예시: `yoyaktube.config.json`

```json
{
  "providers": ["openai", "gemini", "ollama"]
}
```

사이드바에서 API 키/호스트/모델을 직접 입력할 수 있으며, 입력값은 세션 범위에서만 사용됩니다.

## 사용 방법

1. 사이드바에서 Provider와 모델, API 키(또는 Ollama 호스트) 입력
2. 상단에 유튜브 영상 URL 입력 → 자동으로 영상 ID 검증/추출
3. 좌측 툴바에서 [요약하기] 클릭 → 자막 수집 → 요약 생성
4. 생성된 요약을 확인하고, 우측 챗 영역에서 Q&A 진행
5. 필요 시 요약/자막/통합 문서를 다운로드

## 자막 언어 우선순위

사이드바의 "자막 언어 우선순위"에서 `ko,en,ja` 처럼 콤마로 구분해 입력하면, 우선순위에 맞춰 자막을 시도합니다. 자동 생성 자막도 가능한 경우 활용합니다.

## Ollama 사용 팁

- 로컬에서 Ollama를 실행하고 모델을 풀/준비하세요.
- Ollama 호스트(포트 포함)를 사이드바에 입력하고, [↻]로 모델 목록을 새로고침할 수 있습니다.

## 문제해결

- 유효하지 않은 링크 경고: `https://www.youtube.com/watch?v=...` 형식을 확인하세요.
- 자막을 가져오지 못함: 멤버십/연령 제한/비공개/지역 차단 영상일 수 있습니다.
- 모델 호출 오류(401/429/5xx/Timeout):
  - API 키/권한 확인(OpenAI/Gemini)
  - 호출이 많은 경우 잠시 후 재시도(429)
  - 서비스 불안정/네트워크 오류 시 재시도 또는 Provider 변경
- 요약 버튼 비활성화: 선택한 Provider에 필요한 설정(모델/키/호스트)을 모두 채워야 활성화됩니다.

## 개발 참고

- 요약 프롬프트: `yoyaktube/constants.py`의 `FULL_SUMMARY_PROMPT`
- 세션 상태 키: `yoyaktube/constants.py` / 접근함수: `yoyaktube/state.py`
- 요약/챗 컨텍스트 구성: `yoyaktube/utils.py`
- LLM 인스턴스 캐싱: `yoyaktube/llm.py`의 `get_or_create_llm`
- 메타데이터/자막 캐시: `st.cache_data` (TTL 3600초)

## 로드맵(예정)

- 요약 내 타임스탬프에 영상 구간 이동 링크 제공
- 챗 기록 초기화 버튼 추가
- URL 입력란에 예시 placeholder 표시

## 라이선스

별도 명시가 없으므로 조직/저작자 정책에 따릅니다. 상용/배포 시 사용 라이선스와 모델 사용약관(OpenAI/Gemini/Ollama)을 반드시 확인하세요.

## 감사의 말

- youtube-transcript-api
- yt-dlp
- Streamlit
