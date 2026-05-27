# Infrastructure as Code (AWS SAM)

AWS Serverless Application Model (SAM) templates for automated infrastructure deployment.

## Files

- **template.yaml** — CloudFormation SAM template defining all AWS resources
- **mlflow_lambda.py** — Lambda function for MLFlow experiment tracking
- **parameters.json** — Default parameter values for SAM deployment
- **deploy.sh** — Automated deployment script

## Quick Deployment

```bash
chmod +x deploy.sh
./deploy.sh ml-inference-pipeline-dev us-east-1 dev
```

## What Gets Created

### Compute
- **Lambda: Inference** — FastAPI-based inference endpoint (1024 MB memory)
- **Lambda: Data Selector** — Active learning (scheduled hourly)
- **Lambda: MLFlow Tracking** — Experiment logging (EventBridge triggered)

### API & Networking
- **API Gateway** — REST endpoint at `https://{api-id}.execute-api.{region}.amazonaws.com/dev/predict`
- **EventBridge Rule** — Schedules data selector and MLFlow logging

### Storage
- **S3: Logs Bucket** — Inference images and metadata
- **S3: Labeling Queue** — Active learning sample queue
- **DynamoDB Table** — Inference logs with GSI for active learning

### Monitoring
- **CloudWatch Dashboard** — Real-time metrics visualization
- **CloudWatch Logs** — Centralized logging for all Lambda functions

### Security
- **IAM Roles** — Least-privilege execution roles per Lambda function

## Manual Deployment (without script)

### 1. Validate Template

```bash
sam validate --template template.yaml
```

### 2. Build

```bash
sam build --template template.yaml --use-container
```

### 3. Deploy Interactively

```bash
sam deploy --guided
```

### 4. Deploy with Parameters

```bash
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name ml-inference-pipeline-dev \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    EnvironmentName=dev \
    ModelVersion=v1.0.0 \
    LogsBucket=aws-ml-logs \
    LabelingQueueBucket=aws-labeling-queue
```

## Environment Parameters

Edit `parameters.json` to customize:

```json
{
  "ParameterOverrides": {
    "EnvironmentName": "dev",        // dev, staging, prod
    "ModelVersion": "v1.0.0",        // Your model version
    "LogsBucket": "aws-ml-logs",     // S3 bucket name (will have account ID appended)
    "LabelingQueueBucket": "aws-labeling-queue"
  }
}
```

## IAM Permissions Required

The AWS user running deployment needs permissions for:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "apigateway:*",
        "s3:*",
        "dynamodb:*",
        "iam:*",
        "logs:*",
        "events:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Deployment Outputs

After deployment, CloudFormation provides:

| Output | Description |
|--------|-------------|
| `InferenceApiEndpoint` | URL to call /predict endpoint |
| `LogsBucketName` | S3 bucket for image logs |
| `LabelingQueueBucketName` | S3 bucket for active learning |
| `CloudWatchDashboardUrl` | Link to monitoring dashboard |

## Troubleshooting

### "Resource already exists"
- S3 bucket names are globally unique. Add suffix to bucket name in `parameters.json`

### "Failed to assume IAM role"
- Ensure AWS credentials are configured: `aws configure`

### "Quota exceeded"
- Request Lambda concurrency limit increase in AWS console

### CloudFormation stack failed
- Check CloudFormation events for detailed error messages
- Delete failed stack: `aws cloudformation delete-stack --stack-name ml-inference-pipeline-dev`

## Cleanup

```bash
# Delete stack and all resources
aws cloudformation delete-stack --stack-name ml-inference-pipeline-dev

# Manually empty and delete S3 buckets (required before deleting stack)
aws s3 rm s3://aws-ml-logs-YOUR-ACCOUNT-ID --recursive
```

## Updates & Maintenance

### Update Lambda Code

1. Edit function code (e.g., `app/app_main.py`)
2. Re-deploy:
   ```bash
   sam build --template template.yaml --use-container
   sam deploy --template-file .aws-sam/build/template.yaml
   ```

### Update Infrastructure

1. Edit `template.yaml`
2. Deploy changes:
   ```bash
   sam deploy --template-file .aws-sam/build/template.yaml
   ```
   CloudFormation will show what will change before applying.

### Monitor Deployments

```bash
# Watch stack creation/update
aws cloudformation describe-stacks --stack-name ml-inference-pipeline-dev

# View Lambda logs
aws logs tail /aws/lambda/ml-edge-inference-dev --follow
```

## Cost Estimation

Monthly cost for typical usage (1M requests):

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 1M × 0.05s | ~$0.83 |
| DynamoDB | On-demand write | ~$1.25 |
| S3 | 1GB storage + requests | ~$0.30 |
| CloudWatch | Logs + metrics | ~$0.50 |
| **Total** | | **~$2-3/month** |

*Costs scale linearly with request volume*

## Production Checklist

Before deploying to production:

- [ ] Enable S3 encryption (KMS)
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Configure Lambda reserved concurrency
- [ ] Set up CloudWatch alarms
- [ ] Enable CloudTrail for audit logging
- [ ] Test disaster recovery procedure
- [ ] Document runbook and escalation process
- [ ] Set up cross-region replication (optional)

## References

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
