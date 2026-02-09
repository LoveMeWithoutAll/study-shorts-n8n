# study-shorts-n8n

S3 업로드를 트리거로 Whisper STT → 하이라이트 선택 → FFmpeg 쇼츠(자막 번인) → 썸네일 → 메타데이터 기록까지 로컬에서 처리하는 n8n 파이프라인입니다.

## 구성 요약
- S3 ObjectCreated 이벤트 → SQS 큐 → n8n SQS Trigger 폴링
- Whisper STT: 로컬 Docker 컨테이너(`whisper_api`)
- FFmpeg: 로컬 Docker 컨테이너(`media_worker`)에서 처리 (자막 번인 포함)
- MVP 범위: YouTube 업로드 제외

## 사전 준비
아래 도구/환경이 필요합니다.
- **OS**: macOS 또는 Linux 권장 (Windows는 WSL2 권장)
- **AWS CLI**: `aws` (v2 권장)
- **Docker / Docker Compose**: Docker Desktop 또는 엔진 + compose 플러그인
- **Node.js**: `node` 18 이상 (스크립트 실행용)
- **Python 3**: `python3` (SQS 설정 스크립트에서 사용)
- **FFmpeg**: 로컬 설치 불필요 (컨테이너 내부에서 사용)
- **n8n**: 본 저장소의 `docker compose`로 실행

## 빠른 시작 (로컬 개발 환경)
아래 단계는 macOS/Linux 기준입니다. Windows는 경로와 명령어만 적절히 치환하면 됩니다.

### 1) 저장소 클론 및 환경 변수 준비
```
git clone <YOUR_REPO_URL>
cd study-shorts-n8n
```

`.env.example`을 참고해 `.env`를 만들고 아래 값을 입력합니다.
```
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=<n8n에서 발급된 API 키>
AWS_REGION=ap-northeast-2
SQS_QUEUE_URL=<SQS 큐 URL>
```

AWS CLI 프로필을 사용하려면 `AWS_PROFILE`을 지정하세요.
```
AWS_PROFILE=default
```
지정하지 않으면 `default` 프로필이 사용됩니다.

### 2) 로컬에서 n8n 실행 및 계정 생성
```
docker compose up -d --build
```
브라우저에서 `http://localhost:5678` 접속 후 관리자 계정을 생성합니다.

### 3) AWS IAM 사용자 생성
AWS 콘솔에서 전용 IAM 사용자를 만들고 다음 권한을 부여합니다.
- SQS: `ReceiveMessage`, `DeleteMessage`, `GetQueueAttributes`
- S3: `GetObject`, `ListBucket`

권장 방식:
1. IAM 사용자 생성 (Programmatic access)
2. Access Key / Secret Key 발급
3. 아래 정책을 사용자에게 연결

### 4) S3/SQS 리소스 생성
버킷 생성:
```
AWS_REGION=ap-northeast-2 \
./infra/aws/create_bucket.sh
```

S3 → SQS 이벤트 연결:
```
AWS_REGION=ap-northeast-2 \
BUCKET_NAME=study-shorts-<account>-ap-northeast-2 \
./infra/aws/configure_event.sh
```
출력된 `Queue URL`을 `.env`의 `SQS_QUEUE_URL`에 반영합니다.

참고: `AWS_PROFILE`을 지정하면 해당 프로필을 사용합니다. 지정하지 않으면 `default` 프로필을 사용합니다.

### 5) n8n Credentials 설정 (AWS)
n8n UI에서 다음 경로로 이동합니다.
`Settings → Credentials → New`

`AWS` 자격 증명을 추가하고 다음 값을 입력합니다.
- Access Key
- Secret Key

이 값들은 위에서 생성한 IAM 사용자의 키를 사용합니다.

## 1) S3 + SQS 준비
버킷 생성:
```
AWS_REGION=ap-northeast-2 \
./infra/aws/create_bucket.sh
```

S3 → SQS 이벤트 연결:
```
AWS_REGION=ap-northeast-2 \
BUCKET_NAME=study-shorts-<account>-ap-northeast-2 \
./infra/aws/configure_event.sh
```

출력된 `Queue URL`을 아래 n8n 환경 변수에 넣습니다.

### n8n용 최소 IAM 권한 예시
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:<region>:<account>:<queue-name>"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::<bucket>",
        "arn:aws:s3:::<bucket>/*"
      ]
    }
  ]
}
```

## 2) Docker Compose 실행
```
docker compose up -d --build
```

`.env` 또는 쉘 환경변수로 다음 값을 설정하세요:
- `AWS_REGION`
- `SQS_QUEUE_URL`

필요하면 n8n 기본 인증을 활성화하세요:
```
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=strong-password
```

## 3) n8n 워크플로우 가져오기
워크플로우 JSON은 `workflows/exports/s3_to_shorts.json`에 있습니다.

CLI로 가져오기:
```
node ./scripts/n8nctl.mjs import-workflow ./workflows/exports/s3_to_shorts.json
```

## 4) n8n 자격 증명 설정
### AWS
- n8n UI에서 `AWS` 자격 증명을 추가
- Access Key / Secret Key는 `personal` 프로필과 동일한 값을 입력
참고: 최신 n8n에서 `Credentials` 메뉴는 좌측 사이드바의 `Settings → Credentials`에 있습니다.

## 5) 테스트 업로드
예시 업로드:
```
aws s3 cp /path/to/sample.mp4 s3://<BUCKET_NAME>/incoming/sample.mp4 --profile personal
```

n8n 실행이 끝나면 결과 파일이 생성됩니다:
- 입력/중간/출력: `data/runs/` (예: `input_<runId>_...`, `full_<runId>.srt`, `highlight_<runId>_1.mp4`, `highlight_<runId>_1.jpg`)
- 실행 로그: `runs/run-<runId>.json`

## 6) Whisper 모델 조정 (한국어 품질)
`docker-compose.yml`의 `whisper_api` 환경 변수를 조정하세요:
- `WHISPER_MODEL`: `small`, `medium`, `large-v3`
- `WHISPER_COMPUTE_TYPE`: `int8` (기본), `float16` (정확도↑, 속도↓)

## 파일/폴더
- `infra/aws/`: S3/SQS 생성 스크립트
- `services/whisper_api/`: Whisper STT API (FastAPI)
- `workflows/exports/`: n8n 워크플로우 JSON
- `data/`: 실행 데이터 (영상/자막/썸네일)
- `runs/`: 실행 로그 JSON

## 참고
- SQS 트리거는 폴링 방식이며, 이벤트마다 실행이 종료됩니다.
- n8n을 외부에 공개하지 마세요. 필요 시 기본 인증을 활성화하세요.
