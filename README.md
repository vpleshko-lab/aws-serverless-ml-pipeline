# AWS Serverless ML Pipeline

![CI/CD](https://img.shields.io/github/actions/workflow/status/vpleshko-lab/aws-serverless-ml-pipeline/deploy.yml?branch=main&label=CI%2FCD&logo=github-actions)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)
![ONNX](https://img.shields.io/badge/Runtime-ONNX-grey?logo=onnx)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

End-to-end serverless ML inference pipeline for image classification using MobileNetV2 on AWS Lambda. Includes Infrastructure as Code (SAM), web UI (Streamlit), MLFlow experiment tracking, and active learning capabilities.

## ✨ Features

- 🔧 **Infrastructure as Code** — AWS SAM template for fully automated deployment
- 🌐 **Web UI** — Streamlit interface for interactive inference testing
- 🎯 **Serverless Inference** — AWS Lambda + API Gateway for scalable, cost-effective predictions
- ⚡ **High Performance** — ONNX Runtime optimized for MobileNetV2 inference
- 📊 **Comprehensive Monitoring** — CloudWatch dashboards, DynamoDB metadata, S3 logging
- 🧠 **Active Learning** — Automatic queuing of uncertain predictions for human review
- 📈 **MLFlow Tracking** — Experiment logging via Lambda (no manual UI needed)
- 🐳 **Containerized** — Docker-based Lambda deployment
- ⚙️ **Automated CI/CD** — GitHub Actions workflow

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACES                             │
├──────────────────────┬──────────────────────────────────────────┤
│  Streamlit Web UI    │  Curl / Python / API Client              │
│  (Local or Remote)   │  (AWS API Gateway)                       │
└──────────────┬───────┴──────────────────────┬────────────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
                    ┌──────────────────────┐
                    │  AWS API Gateway     │
                    │  (REST Endpoint)     │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌────────────────────┐      ┌─────────────────────┐
        │  Lambda: Inference │      │  Lambda: MLFlow     │
        │  (FastAPI + ONNX)  │      │  Tracking           │
        │                    │      │  (EventBridge)      │
        └────────┬───────────┘      └─────────────────────┘
                 │                           │
        ┌────────┼─────────────┬─────────────┘
        ▼        ▼             ▼
    ┌───────┐ ┌──────────┐ ┌──────────────┐
    │  S3   │ │DynamoDB  │ │ CloudWatch   │
    │Images │ │Metadata  │ │ Metrics &    │
    │Logs   │ │Inference │ │ Dashboard    │
    └───────┘ └──────────┘ └──────────────┘
        │
        ▼ (Low confidence)
    ┌──────────────────┐
    │ S3 Labeling      │
    │ Queue            │
    │ (Active Learning)│
    └──────────────────┘
        │
        ▼ (Human Review)
    ┌──────────────────┐
    │ Model Retraining │
    │ Pipeline         │
    └──────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **ML Framework** | PyTorch, ONNX Runtime |
| **Model** | MobileNetV2 (ImageNet pre-trained) |
| **API Framework** | FastAPI, Mangum (Lambda adapter) |
| **Web UI** | Streamlit |
| **Infrastructure** | AWS SAM (CloudFormation) |
| **Cloud Services** | Lambda, API Gateway, S3, DynamoDB, CloudWatch, EventBridge |
| **Tracking** | MLFlow (Lambda-based logging) |
| **Container** | Docker |
| **CI/CD** | GitHub Actions |

## Project Structure

```
aws-serverless-ml-pipeline/
├── infrastructure/                      # Infrastructure as Code (IaC)
│   ├── template.yaml                    # AWS SAM template (Lambda, API Gateway, S3, DynamoDB, IAM, CloudWatch)
│   ├── mlflow_lambda.py                 # Lambda handler for experiment tracking via EventBridge
│   ├── parameters.json                  # SAM deployment parameters
│   └── deploy.sh                        # Deployment automation script
├── app/                                 # Application code
│   ├── __init__.py
│   ├── app_main.py                      # FastAPI endpoint with ONNX inference
│   ├── streamlit_ui.py                  # Streamlit web interface for testing
│   ├── data_selector.py                 # Lambda handler for active learning
│   ├── logger_setup.py                  # Centralized logging configuration
│   └── model.onnx                       # Pre-trained MobileNetV2 (ONNX format)
├── src/                                 # Model preparation scripts
│   └── export_onnx.py                   # PyTorch → ONNX export utility
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── cloud_test.py                    # Integration tests
│   └── data/
│       └── dog_001.avif                 # Sample image for testing
├── .github/workflows/
│   └── deploy.yml                       # GitHub Actions CI/CD pipeline
├── Dockerfile                           # Container definition for Lambda
├── pyproject.toml                       # Poetry project configuration
├── requirements.txt                     # Python dependencies (generated from pyproject.toml)
└── README.md                            # This file
```

## Prerequisites

- **Python** 3.11-3.14
- **AWS CLI** configured with appropriate IAM permissions
- **Docker** (for local testing and Lambda deployment)
- **Poetry** (for dependency management)
- **AWS SAM CLI** (for infrastructure deployment)

### Optional Tools
- **AWS Account** with appropriate service limits for Lambda, S3, DynamoDB
- **GitHub Secrets** configured for CI/CD automation

## Installation & Setup

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/vpleshko-lab/aws-serverless-ml-pipeline.git
cd aws-serverless-ml-pipeline
poetry install
```

### 2. Export ONNX Model (if needed)

```bash
python src/export_onnx.py
```

## Local Development

### Option A: Run FastAPI Backend Only

```bash
uvicorn app.app_main:app --reload
```

The API will be available at `http://localhost:8000`

**Test with curl:**
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@tests/data/dog_001.avif"
```

### Option B: Run Streamlit Web UI + FastAPI

**Terminal 1 - Start FastAPI:**
```bash
uvicorn app.app_main:app --reload
```

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run app/streamlit_ui.py
```

The web interface will open at `http://localhost:8501`

## Infrastructure as Code (AWS SAM)

### Prerequisites for Deployment

```bash
# Install AWS SAM CLI
brew install aws-sam-cli

# Configure AWS credentials
aws configure
```

### Deploy Infrastructure

```bash
cd infrastructure
chmod +x deploy.sh

# Deploy to AWS (dev environment)
./deploy.sh ml-inference-pipeline-dev us-east-1 dev

# For staging/production
./deploy.sh ml-inference-pipeline-prod eu-central-1 prod
```

### Manual SAM Deployment

```bash
# Validate template
sam validate --template infrastructure/template.yaml

# Build SAM app
sam build --template infrastructure/template.yaml --use-container

# Deploy with interactive prompts
sam deploy --guided

# Or deploy with parameters
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name ml-inference-pipeline-dev \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    EnvironmentName=dev \
    ModelVersion=v1.0.0
```

### What Gets Created

The SAM template (`infrastructure/template.yaml`) creates:

| Resource | Description |
|----------|-------------|
| **Lambda Functions** | 3x (Inference, Data Selector, MLFlow Tracking) |
| **API Gateway** | REST API with `/predict` endpoint |
| **S3 Buckets** | Image logs + active learning queue |
| **DynamoDB Table** | Inference metadata + GSI for active learning |
| **CloudWatch Dashboard** | Real-time metrics and monitoring |
| **IAM Roles** | Least-privilege execution roles per function |
| **EventBridge Rule** | Triggers MLFlow logging Lambda hourly |

### Infrastructure Outputs

After deployment, you'll receive:

```
InferenceApiEndpoint: https://xxxxx.execute-api.region.amazonaws.com/dev/predict
LogsBucketName: aws-ml-logs-123456789
LabelingQueueBucketName: aws-labeling-queue-123456789
CloudWatchDashboardUrl: https://console.aws.amazon.com/cloudwatch/...
```

## Production Deployment Checklist

Before deploying to production, ensure:

### 🔒 Security
- [ ] Enable S3 bucket encryption (KMS or SSE-S3)
- [ ] Enable S3 versioning and MFA delete
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Use VPC endpoints for private S3/DynamoDB access
- [ ] Rotate AWS credentials regularly
- [ ] Enable AWS CloudTrail for audit logging
- [ ] Enable VPC Flow Logs for network monitoring
- [ ] Review and restrict IAM policy permissions

### 📊 Monitoring & Observability
- [ ] Configure CloudWatch alarms for Lambda errors
- [ ] Set up SNS notifications for high error rates
- [ ] Enable X-Ray tracing for distributed requests
- [ ] Configure log retention (e.g., 30 days)
- [ ] Create custom CloudWatch metrics for business KPIs
- [ ] Set up dashboard for model performance

### ⚡ Performance & Scaling
- [ ] Set Lambda memory to 1024 MB or higher for inference
- [ ] Configure Lambda reserved concurrency to prevent throttling
- [ ] Use Lambda layers for common dependencies
- [ ] Consider API Gateway caching for repeated requests
- [ ] Enable DynamoDB auto-scaling for writes
- [ ] Test with production-like data volumes

### 🧠 ML Model Management
- [ ] Version all models (e.g., v1.0.0, v1.0.1)
- [ ] Store model artifacts in S3 with versioning
- [ ] Implement model validation pipeline before deployment
- [ ] Set up MLFlow experiment tracking for all training runs
- [ ] Document model performance baselines
- [ ] Create rollback procedure for bad models

### 📝 Data & Compliance
- [ ] Implement data retention policies (DynamoDB TTL)
- [ ] Set up encryption at rest and in transit
- [ ] Create data backup strategy (S3 cross-region replication)
- [ ] Document data processing for compliance (GDPR, etc.)
- [ ] Implement audit logging for data access
- [ ] Set up data anonymization for sensitive info

### 🚀 Deployment
- [ ] Use separate AWS accounts for dev/staging/prod
- [ ] Implement blue-green deployment strategy
- [ ] Test infrastructure with CloudFormation drift detection
- [ ] Set up automated infrastructure validation
- [ ] Document runbook for incidents
- [ ] Create disaster recovery plan

### 💰 Cost Optimization
- [ ] Monitor AWS Lambda costs (use CloudWatch metrics)
- [ ] Review S3 storage costs (lifecycle policies)
- [ ] Set up AWS Budgets alerts
- [ ] Consider Lambda@Edge for global distribution
- [ ] Implement request batching to reduce invocations
- [ ] Use Lambda reserved concurrency wisely

## API Reference

### POST /predict

Upload an image for classification.

**Request:**
```bash
curl -X POST "https://<api-endpoint>/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg"
```

**Request Body:**
- `file` (multipart) — Image file (JPEG, PNG, AVIF, WebP)

**Response (Success - 200):**
```json
{
  "log_id": "550e8400-e29b-41d4-a716-446655440000",
  "class": 243,
  "confidence": 0.9876,
  "latency_ms": 45.2,
  "status": "logged"
}
```

**Response (Error - 400):**
```json
{
  "detail": "Invalid image format"
}
```

**Response (Error - 500):**
```json
{
  "detail": "Inference engine offline"
}
```

## Streamlit Web UI

Launch the interactive web interface:

```bash
streamlit run app/streamlit_ui.py
```

**Features:**
- 🖼️ Image upload with preview
- 🎯 Real-time inference
- 📊 Confidence visualization
- ⚠️ Active learning alerts for low-confidence predictions
- 🔄 Support for both local and AWS API backends
- 📋 Detailed response inspection

**Configuration:**
- Select API mode (Local FastAPI or AWS API Gateway)
- Adjust confidence threshold for active learning
- View system architecture and help docs

## Active Learning Pipeline

The system automatically identifies uncertain predictions and queues them for review:

1. **Inference** — Predictions with confidence < threshold are flagged
2. **Queuing** — Flagged samples copied to `aws-labeling-queue` S3 bucket
3. **Review** — Records marked as "In_Review" in DynamoDB
4. **Labeling** — Human annotators label images (use Label Studio, etc.)
5. **Retraining** — Labeled data incorporated into model retraining
6. **Update** — New model version deployed via CI/CD

**Confidence Threshold:** Default 0.6 (configurable in app or Streamlit UI)

## MLFlow Experiment Tracking

MLFlow tracking is implemented via Lambda to log all inference metrics:

- **Backend Store:** S3 (`s3://aws-ml-logs/mlflow`)
- **Artifact Store:** S3 (`s3://aws-ml-logs/mlflow-artifacts`)
- **Trigger:** EventBridge rule (runs hourly)
- **Metrics Logged:** Confidence, latency, model version, predicted class

To access MLFlow runs:
```bash
# Start MLFlow UI (requires local installation)
mlflow ui --backend-store-uri s3://aws-ml-logs/mlflow
```

## CI/CD Pipeline

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
        -H "Content-Type: multipart/form-data" \
        -F "file=@tests/data/dog_001.avif"
   ```

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

## CI/CD Pipeline

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
  - `ml-edge-inference` (main inference)
  - `ml-data-selector` (active learning)
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
- **DynamoDB Table**: `InferenceLogs`
  - Primary Key: `prediction_id` (String), `timestamp` (String)
  - Global Secondary Index: `ActiveLearningIndex` on `is_labeled` (String), `confidence` (String)
  - Attributes: `predicted_class`, `confidence`, `latency_ms`, `s3_path`, `model_version`, `project`, `is_labeled`
- **CloudWatch**: Namespace `ML_Production` for custom metrics
- **Lambda Functions**:
  - `ml-edge-inference` (API Gateway trigger for inference)
  - `ml-data-selector` (EventBridge scheduled trigger for active learning)
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
