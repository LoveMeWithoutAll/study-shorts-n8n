#!/usr/bin/env bash
set -euo pipefail

PROFILE="${AWS_PROFILE:-default}"
REGION="${AWS_REGION:-ap-northeast-2}"
BUCKET_NAME="${BUCKET_NAME:-}"
QUEUE_NAME="${QUEUE_NAME:-}"
ENABLE_DLQ="${ENABLE_DLQ:-true}"

if [[ -z "$BUCKET_NAME" ]]; then
  echo "BUCKET_NAME is required" >&2
  exit 1
fi

if [[ -z "$QUEUE_NAME" ]]; then
  QUEUE_NAME="${BUCKET_NAME}-events"
fi

DLQ_NAME="${QUEUE_NAME}-dlq"

create_queue() {
  local name="$1"
  aws sqs create-queue --profile "$PROFILE" --region "$REGION" \
    --queue-name "$name" \
    --attributes VisibilityTimeout=300 >/dev/null
}

get_queue_url() {
  aws sqs get-queue-url --profile "$PROFILE" --region "$REGION" --queue-name "$1" --query QueueUrl --output text
}

if ! aws sqs get-queue-url --profile "$PROFILE" --region "$REGION" --queue-name "$QUEUE_NAME" >/dev/null 2>&1; then
  create_queue "$QUEUE_NAME"
fi

if [[ "$ENABLE_DLQ" == "true" ]]; then
  if ! aws sqs get-queue-url --profile "$PROFILE" --region "$REGION" --queue-name "$DLQ_NAME" >/dev/null 2>&1; then
    create_queue "$DLQ_NAME"
  fi

  DLQ_URL=$(get_queue_url "$DLQ_NAME")
  DLQ_ARN=$(aws sqs get-queue-attributes --profile "$PROFILE" --region "$REGION" --queue-url "$DLQ_URL" \
    --attribute-names QueueArn --query Attributes.QueueArn --output text)

  QUEUE_URL=$(get_queue_url "$QUEUE_NAME")
  REDRIVE_INNER=$(printf '{"deadLetterTargetArn":"%s","maxReceiveCount":5}' "$DLQ_ARN")
  export REDRIVE_INNER
  ATTR_JSON=$(python3 - <<'PY'
import json, os
print(json.dumps({"RedrivePolicy": os.environ["REDRIVE_INNER"]}))
PY
)
  aws sqs set-queue-attributes --profile "$PROFILE" --region "$REGION" --queue-url "$QUEUE_URL" \
    --attributes "$ATTR_JSON"
fi

QUEUE_URL=$(get_queue_url "$QUEUE_NAME")
QUEUE_ARN=$(aws sqs get-queue-attributes --profile "$PROFILE" --region "$REGION" --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text)

POLICY=$(cat <<POLICY_JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3SendMessage",
      "Effect": "Allow",
      "Principal": {"Service": "s3.amazonaws.com"},
      "Action": "sqs:SendMessage",
      "Resource": "$QUEUE_ARN",
      "Condition": {
        "ArnEquals": {"aws:SourceArn": "arn:aws:s3:::$BUCKET_NAME"}
      }
    }
  ]
}
POLICY_JSON
)

export POLICY
POLICY_ATTR=$(python3 - <<'PY'
import json, os
print(json.dumps({"Policy": os.environ["POLICY"]}))
PY
)

aws sqs set-queue-attributes --profile "$PROFILE" --region "$REGION" --queue-url "$QUEUE_URL" \
  --attributes "$POLICY_ATTR"

aws s3api put-bucket-notification-configuration --profile "$PROFILE" --region "$REGION" \
  --bucket "$BUCKET_NAME" \
  --notification-configuration "{\"QueueConfigurations\":[{\"QueueArn\":\"$QUEUE_ARN\",\"Events\":[\"s3:ObjectCreated:*\"]}]}"

cat <<EOF_OUT
Configured S3 -> SQS
Bucket: $BUCKET_NAME
Queue URL: $QUEUE_URL
Queue ARN: $QUEUE_ARN
DLQ: ${ENABLE_DLQ}
EOF_OUT
