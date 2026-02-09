#!/usr/bin/env bash
set -euo pipefail

PROFILE="personal"
REGION="${AWS_REGION:-ap-northeast-2}"
BUCKET_NAME="${BUCKET_NAME:-}"
ENABLE_VERSIONING="${ENABLE_VERSIONING:-false}"

if [[ -z "$BUCKET_NAME" ]]; then
  ACCOUNT_ID=$(aws sts get-caller-identity --profile "$PROFILE" --query Account --output text)
  BUCKET_NAME="study-shorts-${ACCOUNT_ID}-${REGION}"
fi

if aws s3api head-bucket --bucket "$BUCKET_NAME" --profile "$PROFILE" >/dev/null 2>&1; then
  echo "Bucket exists: $BUCKET_NAME"
else
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET_NAME" --profile "$PROFILE"
  else
    aws s3api create-bucket --bucket "$BUCKET_NAME" --profile "$PROFILE" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
  echo "Created bucket: $BUCKET_NAME"
fi

if [[ "$ENABLE_VERSIONING" == "true" ]]; then
  aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" --profile "$PROFILE" \
    --versioning-configuration Status=Enabled
  echo "Enabled versioning: $BUCKET_NAME"
fi

echo "$BUCKET_NAME"
