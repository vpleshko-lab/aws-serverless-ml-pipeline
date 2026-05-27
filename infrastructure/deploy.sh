#!/bin/bash
# Infrastructure deployment script using AWS SAM

set -e

STACK_NAME="${1:-ml-inference-pipeline-dev}"
AWS_REGION="${2:-us-east-1}"
ENVIRONMENT="${3:-dev}"

echo "📦 AWS SAM Infrastructure Deployment"
echo "======================================"
echo "Stack Name: $STACK_NAME"
echo "Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Step 1: Validate template
echo "🔍 Validating SAM template..."
sam validate --template infrastructure/template.yaml --region "$AWS_REGION"
echo "✓ Template is valid"
echo ""

# Step 2: Build
echo "🔨 Building SAM application..."
sam build --template infrastructure/template.yaml --region "$AWS_REGION" --use-container
echo "✓ Build completed"
echo ""

# Step 3: Deploy
echo "🚀 Deploying infrastructure..."
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    EnvironmentName="$ENVIRONMENT" \
    ModelVersion="v1.0.0" \
    LogsBucket="aws-ml-logs" \
    LabelingQueueBucket="aws-labeling-queue" \
  --no-confirm-changeset

echo "✓ Deployment completed"
echo ""

# Step 4: Show outputs
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

echo ""
echo "✅ Infrastructure deployment complete!"
echo "Visit CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#dashboards:"
