# Decisions

## Trigger Mechanism: S3 → SQS → n8n Polling
선택 이유:
- n8n이 외부 공개 없이도 안정적으로 이벤트를 받을 수 있음
- SQS는 at-least-once 전달 보장 + DLQ 지원으로 장애 대응이 쉬움
- Webhook(SNS+HTTPS) 대비 인증/공개 인프라 필요가 없음

## Whisper 모델 (한국어) 선택
- 기본값: `medium` + `int8`
- 이유: 한국어 정확도와 Apple Silicon CPU 성능 간 균형
- 필요 시 정확도 우선으로 `large-v3` + `float16`로 상향 가능 (속도/자원 증가)

## MVP 범위
- YouTube 업로드는 제외 (로컬 처리 + 결과 아티팩트/메타데이터 저장까지)
