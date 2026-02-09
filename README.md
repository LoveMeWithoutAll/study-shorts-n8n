# study-shorts-n8n

로컬 n8n 관리 프로젝트입니다. 워크플로우 JSON의 가져오기/내보내기, 실행 내역 점검, 기본 자동화 제어를 지원합니다.

## 제공 항목
- 로컬 n8n 실행용 `docker-compose.yml`(선택)
- API 설정용 `.env`와 `.env.example`
- n8n API 제어용 CLI: `scripts/n8nctl.mjs`
- 내보낸 워크플로우 보관용 `workflows/`
- 실행 페이로드/입력 데이터용 `data/`
- 에이전트 운영 가이드 `AGENTS.md`

## 빠른 시작
1. (선택) Docker로 로컬 n8n 실행
```
cd /Users/ys-m4pro/dev/study-shorts-n8n
docker compose up -d
```

2. `.env`에 API 키 설정
```
N8N_API_KEY=your_api_key_here
```

3. pnpm 의존성 설치
```
cd /Users/ys-m4pro/dev/study-shorts-n8n
pnpm install
```

4. n8n 상태 확인
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs ping
```

## 자주 쓰는 명령
워크플로우 목록
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs list-workflows
```

워크플로우 JSON 내보내기
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs export-workflow 1 --out /Users/ys-m4pro/dev/study-shorts-n8n/workflows/workflow-1.json
```

워크플로우 JSON 가져오기
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs import-workflow /Users/ys-m4pro/dev/study-shorts-n8n/workflows/workflow-1.json
```

활성화 / 비활성화
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs activate 1
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs deactivate 1
```

실행 내역 목록
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs list-executions
```

임의 API 호출
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs request GET /workflows
```

## 참고
- 기본 n8n URL은 `http://localhost:5678`입니다.
- n8n API 베이스/버전이 다르면 `.env`의 `N8N_API_BASE`, `N8N_API_VERSION`을 수정하세요.
- CLI는 `X-N8N-API-KEY` 헤더로 API 키를 전송합니다.
