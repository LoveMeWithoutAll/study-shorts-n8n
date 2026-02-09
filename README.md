# study-shorts-n8n

S3 업로드를 트리거로 Whisper STT → 하이라이트 선택 → FFmpeg 쇼츠(자막 번인) → 썸네일 → 메타데이터 기록까지 로컬에서 처리하는 n8n 파이프라인입니다.

## 구성 요약
- S3 ObjectCreated 이벤트 → SQS 큐 → n8n SQS Trigger 폴링
- Whisper STT: 로컬 Docker 컨테이너(`whisper_api`)
- FFmpeg: 로컬 Docker 컨테이너(`media_worker`)에서 처리 (자막 번인 포함)
- MVP 범위: YouTube 업로드 제외

## 사전 준비
- AWS CLI (`aws`) 설정, 프로필 `personal`
- Docker / Docker Compose
- n8n (docker-compose로 실행)

## 1) S3 + SQS 준비
버킷 생성:
```
AWS_REGION=ap-northeast-2 \
/Users/ys-m4pro/dev/study-shorts-n8n/infra/aws/create_bucket.sh
```

S3 → SQS 이벤트 연결:
```
AWS_REGION=ap-northeast-2 \
BUCKET_NAME=study-shorts-<account>-ap-northeast-2 \
/Users/ys-m4pro/dev/study-shorts-n8n/infra/aws/configure_event.sh
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
cd /Users/ys-m4pro/dev/study-shorts-n8n
docker compose up -d --build
```

`docker-compose.yml`에서 다음 환경 변수를 설정하세요:
- `AWS_REGION`
- `SQS_QUEUE_URL`

필요하면 n8n 기본 인증을 활성화하세요:
```
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=strong-password
```

## 3) n8n 워크플로우 가져오기
워크플로우 JSON은 `/Users/ys-m4pro/dev/study-shorts-n8n/workflows/exports/s3_to_shorts.json`에 있습니다.

CLI로 가져오기:
```
node /Users/ys-m4pro/dev/study-shorts-n8n/scripts/n8nctl.mjs import-workflow /Users/ys-m4pro/dev/study-shorts-n8n/workflows/exports/s3_to_shorts.json
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
- 입력/중간/출력: `/Users/ys-m4pro/dev/study-shorts-n8n/data/runs/` (예: `input_<runId>_...`, `full_<runId>.srt`, `highlight_<runId>_1.mp4`, `highlight_<runId>_1.jpg`)
- 실행 로그: `/Users/ys-m4pro/dev/study-shorts-n8n/runs/run-<runId>.json`

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
