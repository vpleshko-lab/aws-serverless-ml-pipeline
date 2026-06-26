# AWS Serverless Computer Vision Pipeline (MobileNet)

![CI/CD](https://img.shields.io/github/actions/workflow/status/vpleshko-lab/aws-serverless-ml-pipeline/deploy.yml?branch=main&label=CI%2FCD&logo=github-actions)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)
![ONNX](https://img.shields.io/badge/Runtime-ONNX-grey?logo=onnx)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

Production-oriented, serverless end-to-end computer vision pipeline built around MobileNet. This repository demonstrates a pragmatic MLOps implementation with inference served from AWS Lambda, an active-learning feedback loop, MLflow model registry integration, and a lightweight Streamlit UI.

## Key Features

- **Serverless Architecture**: Lightweight, scalable inference via AWS Lambda (ONNX Runtime).
- **Automated CI/CD**: GitHub Actions validate changes and promote infrastructure with CDK/SAM.
- **AWS CDK / IaC**: Fully scripted cloud resources for repeatable environments (`infra-cdk/`).
- **Remote MLflow Model Registry**: Model and run tracking integrated with S3-backed MLflow store and self-hosted MLflow service.
- **Streamlit UI**: Fast local UI for inference and manual review (`app/streamlit_ui.py`).
- **Active Learning Loop**: `ml-data-selector` isolates low-confidence samples to the labeling queue and triggers retraining.
- **Observability**: DynamoDB metadata, S3 artifact store, CloudWatch metrics and dashboards.


## Architecture

![Architecture](<content/screenshot_001.png>)

ASCII fallback:

Streamlit UI -> Lambda Function URL -> {S3 (images), DynamoDB (metadata), MLflow logging} -> ml-data-selector -> S3 labeling queue -> Retraining -> MLflow Registry -> Deploy

## Cloud Infrastructure Breakdown (AWS CDK)

Resources (high-level):

- **AWS Lambda (Inference)** — Serverless ONNX inference runtime exposed via Function URLs or API Gateway.
- **AWS Lambda (Data Selector)** — `ml-serverless-data-selector` identifies low-confidence predictions and moves samples into the labeling queue.
- **DynamoDB** — Metadata table for inference events, status, and active-learning indexing (TTL/GSI supported).
- **S3 Buckets** — Image logs, MLflow backend/artifact stores, and labeling queue buckets.
- **ECS / Fargate (MLflow Server)** — Self-hosted MLflow behind an Application Load Balancer for model registry and UI.
- **EventBridge / Step Functions** — Orchestration for periodic logging, batch processing, and retraining triggers.
- **CloudWatch** — Metrics, logs, dashboards, and alarms for observability.
- **IAM** — Least-privilege roles for Lambdas and CI/CD deploy role for GitHub Actions.

See `infra-cdk/` for the CDK stacks and `cdk.json` for deployment settings.

## Project Layout (quick)

Key folders:

- `app/` — inference runtime, Streamlit UI, data selector and logging utilities.
- `infra-cdk/` — AWS CDK stacks and deployment configuration (`cdk.json`).
- `mlflow-server/` — Dockerized MLflow server for local/self-hosted registry.
- `src/` — model export and preparation scripts (`export_onnx.py`).
- `tests/` — unit and integration tests (`test_app.py`, `cloud_test.py`).

This repository is organized to make the cloud deployment reproducible and the local developer experience immediate.

## Active Learning Workflow (how `ml-data-selector` works)

1. Inference Lambda processes images and writes a metadata record to DynamoDB (including `confidence`, `model_version`, `log_id`).
2. Records with `confidence < threshold` (configurable; default ~0.6) are flagged during write or by a periodic scan.
3. `ml-serverless-data-selector` Lambda consumes flagged records and copies the corresponding images from the inference S3 bucket into the labeling S3 queue.
4. The record state in DynamoDB is updated to `queued_for_labeling` and assigned to a reviewer (optional workflow integration).
5. After manual annotation, labeled samples are pushed to the retraining dataset location and a retraining job is kicked off (CI/CD or Step Functions).
6. Retraining produces a new model artifact registered in MLflow; automated validation gates promote the model and the CD pipeline deploys the updated model to the inference Lambda.

This design minimizes human effort by surfacing only the most informative examples for annotation and automates promotion once validation passes.

## Local Deployment & Testing

Minimum prerequisites:

- Python 3.11+ (3.12 recommended)
- Docker (optional: for MLflow and Lambda container tests)
- AWS CLI configured with deployment IAM permissions

Install dependencies (Poetry):

```bash
git clone <repo-url>
cd aws-serverless-ml-pipeline
poetry install
```

Alternatively with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Export ONNX (if you need to refresh the model artifact):

```bash
python src/export_onnx.py
```

Configure AWS credentials:

```bash
aws configure
# or set environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

If you running local API and you want import production model from Mlflow registry:
```bash
EXPORT MLFLOW_TRACKING_URI="http://DNS_NAME # EC2 -> Load balancers -> your
```
Run the inference API locally (FastAPI + ONNX):
```bash
uvicorn app.app_main:app --reload
```

Run the Streamlit UI locally (connects to local API or a deployed Function URL):

```bash
streamlit run app/streamlit_ui.py
```

Smoke-test the predict endpoint (local):

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/image_001.png"
```

Test a deployed Lambda Function URL or API Gateway endpoint:

```bash
curl -X POST "https://<function-url>/" -F "file=@path/image_001.png"
```

## CI/CD Pipeline

- The repository includes GitHub Actions workflows that run unit and integration tests, validate infrastructure (CDK synth), and build artifacts on feature branches and `dev`.
- Merges to `main` trigger the protected deploy workflow that executes `cdk deploy` (or SAM deploy) using a deploy role configured via GitHub Secrets. The deploy job enforces policy checks, runs automated validation gates (smoke tests), and only promotes the stack when checks pass.

See `.github/workflows/` for the exact pipeline and the `infra-cdk/` stack definitions for deployment behavior.

## Production Checklist & Best Practices

Security, observability, and cost-control checks are provided in the repo's production checklist; apply them before promoting stacks to production. Key items include:

- Enforce S3 encryption (KMS), enable versioning and MFA delete for critical buckets.
- Enable CloudTrail and X-Ray; configure CloudWatch alarms and SNS notifications for incidents.
- Use separate AWS accounts for dev/staging/prod and enforce least-privilege IAM roles for deploy pipelines.
- Validate models with a gated CI job that runs a holdout validation dataset and a smoke-test against the deployed endpoint.

Refer to the `infra-cdk/` stack docs for concrete resource names, outputs, and deploy-time parameters.

GitHub Actions automatically deploys on push to `main`:

```
Push to main
    ↓
Run Tests (pytest)
    ↓
Build Docker Image
    ↓
Push to ECR
    ↓
Update Lambda Functions
    ↓
Run Integration Tests
```

**GitHub Secrets Required:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## API Reference

### POST /predict

Upload an image for classification.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (image file, supports JPEG, PNG, etc.)

**Response:**
```json
{
  "log_id": "uuid-string",
  "class": 243,
  "confidence": 0.9876,
  "status": "logged"
}
```

**Error Responses:**
- `400`: Invalid image format
- `500`: Inference engine offline

---
## Where to look next

- Inference entrypoint: `app/app_main.py`
- Active learning selector: `app/data_selector.py`
- CDK stacks & deploy: `infra-cdk/`
- MLflow local server: `mlflow-server/`

If you'd like, I can run the test suite and validate the CI pipeline locally, or open a PR with minor improvements to the `infra-cdk` deployment scripts (IAM hardening, safer default parameters). What would you like me to do next?
The project uses GitHub Actions for automated deployment to AWS. The workflow (`.github/workflows/deploy.yml`) performs the following steps on push to main branch:

1. **Code Checkout**: Retrieves the latest code
2. **AWS Authentication**: Configures AWS credentials using repository secrets
3. **ECR Login**: Authenticates with Amazon Elastic Container Registry
4. **Docker Build & Push**: Builds the Docker image and pushes to ECR
5. **Update Inference Lambda**: Updates the main inference Lambda function with the new image
6. **Update Selector Lambda**: Updates the data selector Lambda function for active learning

### Required AWS Resources

- **ECR Repository**: `aws-edge-app`
- **Lambda Functions**:
  - `ml-serverless-inference` (main inference)
  - `ml-serverless-data-selector` (active learning)
- **IAM Permissions**: For ECR access, Lambda updates, and CloudWatch logging

### Environment Secrets

Set the following secrets in your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## AWS Infrastructure Setup

For manual deployment or detailed configuration:

### Required Resources

- **S3 Buckets**:
  - `aws-ml-logs` (for inference logs and images)
  - `aws-labeling-queue` (for active learning samples)
  - `serverless-models-artifacts` (Mlflow storage)
- **DynamoDB Table**: `InferenceLogs`
  - Primary Key: `prediction_id` (String), `timestamp` (String)
  - Global Secondary Index: `ActiveLearningIndex` on `is_labeled` (String), `confidence` (String)
  - Attributes: `predicted_class`, `confidence`, `latency_ms`, `s3_path`, `model_version`, `project`, `is_labeled`
- **CloudWatch**: Namespace `ML_Production` for custom metrics
- **Lambda Functions**:
  - `ml-serverless-inference` (API Gateway trigger for inference)
  - `ml-serverless-data-selector` (EventBridge scheduled trigger for active learning)
- **API Gateway**: REST API with `/predict` endpoint
- **EventBridge Rule**: Scheduled rule to trigger data selector Lambda (e.g., rate(1 hour))

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOGS_BUCKET` | S3 bucket for storing inference logs | `aws-ml-logs` |
| `MODEL_VERSION` | Version identifier for the model | `v1.0.0` |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- MobileNetV2 model from PyTorch torchvision
- ONNX Runtime for optimized inference
- AWS Lambda for serverless computing
- FastAPI for modern Python web APIs
- Streamlit for rapid web UI development
- AWS SAM for Infrastructure as Code
