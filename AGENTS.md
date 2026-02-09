# AI 에이전트 운영 가이드

## 목적
이 저장소는 로컬 n8n 워크플로우와 실행 데이터를 관리합니다. 에이전트는 워크플로우 JSON의 가져오기/내보내기, 실행 내역 점검, 자동화 자산 정리에 집중합니다.

## 기본 규칙
- 비밀 값은 커밋하거나 출력하지 않습니다. `N8N_API_KEY`는 `.env`에만 둡니다.
- 내보낸 워크플로우는 `/Users/ys-m4pro/dev/study-shorts-n8n/workflows`에 저장합니다.
- 실행 페이로드/테스트 입력은 `/Users/ys-m4pro/dev/study-shorts-n8n/data`에 둡니다.
- API 연동은 `/Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs`를 사용합니다.

## Secrets
- `.env`는 커밋 금지
- 예시가 필요하면 `.env.example` 파일을 만든다

## 자주 하는 작업
- 워크플로우 JSON을 `workflows/`로 내보내기
- `workflows/`의 JSON을 n8n으로 가져오기
- 워크플로우 활성화/비활성화
- 실행 내역 목록/상세 조회

## 로컬 n8n 실행
```
cd /Users/ys-m4pro/dev/study-shorts-n8n
docker compose up -d
```

## 동작 프로토콜
- API 호출 실패 시 `.env`와 n8n 호스트/포트를 확인합니다.
- 반복 작업은 스크립트로 남깁니다.
- 로그/출력은 간결하게 하고, 필요 시 `data/`에 아티팩트를 저장합니다.

## 예시 흐름
1. 워크플로우 내보내기
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs export-workflow 1 --out /Users/ys-m4pro/dev/study-shorts-n8n/workflows/workflow-1.json
```
2. JSON 수정
3. 워크플로우 가져오기
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs import-workflow /Users/ys-m4pro/dev/study-shorts-n8n/workflows/workflow-1.json
```
