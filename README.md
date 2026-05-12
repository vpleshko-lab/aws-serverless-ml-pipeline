# AWS Serverless ML Pipeline

![CI/CD](https://img.shields.io/github/actions/workflow/status/vpleshko-lab/aws-serverless-ml-pipeline/deploy.yml?branch=main&label=CI%2FCD&logo=github-actions)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)
![ONNX](https://img.shields.io/badge/Runtime-ONNX-grey?logo=onnx)
![License](https://img.shields.io/badge/License-MIT-green)

An end-to-end serverless machine learning inference pipeline for image classification using MobileNetV2, deployed on AWS Lambda with Docker containers. Features automated CI/CD, comprehensive logging, and active learning capabilities for continuous model improvement.

## Features

- **Serverless Architecture**: Deployed on AWS Lambda with API Gateway for scalable, cost-effective inference
- **High Performance**: ONNX Runtime optimized for low-latency predictions
- **Comprehensive Monitoring**: Integrated logging to CloudWatch, DynamoDB, and S3
- **Active Learning**: Automatic identification and queuing of uncertain predictions for human labeling
- **Containerized Deployment**: Docker-based deployment ensuring consistent environments
- **Automated CI/CD**: GitHub Actions workflow for continuous deployment

## Architecture

```
Client Application
      │
      ▼ HTTP POST /predict
AWS API Gateway
      │
      ▼
AWS Lambda (Inference Container)
  ├── FastAPI + Mangum
  ├── ONNX Runtime (MobileNetV2)
  ├── Image Preprocessing
  └── Comprehensive Logging
      │
      ├─► S3 (Input Images)
      ├─► DynamoDB (Inference Metadata)
      ├─► CloudWatch (Metrics)
      │
      ▼ Scheduled/Event Trigger
AWS Lambda (Data Selector)
  └── Active Learning Pipeline
      │
      └─► S3 Labeling Queue
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **ML Framework** | PyTorch, ONNX Runtime |
| **Model** | MobileNetV2 (ImageNet pre-trained) |
| **API Framework** | FastAPI, Mangum (Lambda adapter) |
| **Cloud Services** | AWS Lambda, API Gateway, S3, DynamoDB, CloudWatch |
| **Tracking Experiments** | MlFlow (*not released*) |
| **Container** | Docker |
| **CI/CD** | GitHub Actions |

## Project Structure

```
aws-serverless-ml-pipeline/
├── app/                         # Main application code
│   ├── __init__.py              # Package initialization
│   ├── app_main.py              # FastAPI application with /predict endpoint, ONNX inference, and logging
│   ├── data_selector.py         # Lambda handler for active learning: queries DynamoDB for low-confidence predictions and queues them for labeling
│   ├── logger_setup.py          # Centralized logging configuration with structured formatting
│   └── model.onnx               # Pre-trained MobileNetV2 model in ONNX format for optimized inference
├── src/                         # Source code for model preparation
│   └── export_onnx.py           # Script to export PyTorch model to ONNX
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── cloud_test.py            # Integration tests for cloud deployment
│   └── data/                    # Test data
│       └── dog_001.avif         # Sample image for testing
├── .github/workflows/           # CI/CD configuration
│   └── deploy.yml               # GitHub Actions workflow for AWS deployment
├── Dockerfile                   # Container definition for AWS Lambda
├── pyproject.toml               # Project configuration and dependencies
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Prerequisites

- Python 3.11-3.14
- AWS CLI configured with appropriate permissions
- Docker (for local testing)
- Poetry (for dependency management)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vpleshko-lab/aws-serverless-ml-pipeline.git
   cd aws-edge-ml
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Export the model (if needed):**
   ```bash
   python src/export_onnx.py
   ```

## Local Development

1. **Run the application locally:**
   ```bash
   uvicorn app.app_main:app --reload
   ```

2. **Test the API:**
   ```bash
   curl -X POST "http://localhost:8000/predict" \
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

## Active Learning Pipeline

The system includes active learning capabilities to improve model performance over time:

1. **Uncertainty Detection**: Predictions with confidence below threshold (0.6) are flagged in DynamoDB
2. **Automated Data Selection**: Scheduled Lambda function (`data_selector.py`) queries DynamoDB for uncertain predictions
3. **Data Queuing**: Uncertain samples are automatically copied to a dedicated S3 bucket (`aws-labeling-queue`) for labeling
4. **Status Updates**: Records are marked as "In_Review" to prevent duplicate processing
5. **Human Labeling**: Use tools like Label Studio to annotate queued images
6. **Model Retraining**: Incorporate labeled data to update the model

The data selector Lambda runs on a schedule or event trigger to continuously identify samples for improvement.

## Monitoring and Observability

- **CloudWatch Metrics**: Inference latency and confidence scores
- **DynamoDB Logs**: Detailed inference metadata
- **S3 Storage**: Input images and inference artifacts
- ~~**ML FLow**: Experiment tracking and visualization~~ (*not released now*)

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

| Field | Instrument |
|---|---|
| **Cloud** | AWS Lambda, ECR, API Gateway |
| **DevOps** | Docker, GitHub Actions |
| **Logging & tracking metrics** | AWS CloudWatch |
| **Dependencies** | Poetry |


---

## API Reference

**Endpoint:** `POST /predict`

**Request** — `multipart/form-data`:

| Field | Type | Description |
|---|---|---|
| `file` | image (jpg/png) | Image to classify |

**Response** — `application/json`:

```json
{
  "class_id": "75",
  "confidence": 0.94,
  "latency_ms": 112.4
}
```

**Example with `curl`:**

```bash
curl -X POST "https://<api-id>.execute-api.<region>.amazonaws.com/predict" \
  -F "file=@./your_image.jpg"
```

**Example with Python (edge client):**

```python
import requests

url = "https://<api-id>.execute-api.<region>.amazonaws.com/predict"

with open("your_image.jpg", "rb") as f:
    response = requests.post(url, files={"file": f})

print(response.json())
# {"class_id": "75", "confidence": 0.94, "latency_ms": 112.4}
```

---

## Local Development

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.12+ |
| Poetry | 1.8+ |
| Docker | 24+ |
| AWS CLI | 2.x (for deployment only) |

---

## Cloud Deployment & Replication Guide

Deployment to AWS Lambda is fully automated via CI/CD. To replicate this pipeline in your own account:

### 1. AWS Infrastructure (one-time setup)

1. **ECR** — Create a private repository in Amazon ECR.
2. **Lambda** — Create a Lambda function, choosing **"Container image"** as the source.
   - Recommended memory: **1024 MB**; timeout: **30s**.
3. **API Gateway** — Create an HTTP API and attach it as a trigger to your Lambda.

### 2. GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM key with ECR & Lambda permissions |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret key |
| `AWS_REGION` | e.g. `eu-central-1` |

### 3. CI/CD Flow

Every `git push` to `main` triggers the GitHub Actions workflow:

```
Push to main
    │
    ├── 1. Run tests
    ├── 2. Build Docker image
    ├── 3. Push image to ECR
    └── 4. Update Lambda function → new image
```

---

## Environment Variables

Full list of variables required in `.env`:

```bash
# AWS (needed only for local testing against cloud)
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=eu-central-1

```

> **Note:** In the Lambda environment, `AWS_*` credentials are injected automatically via the execution role.
