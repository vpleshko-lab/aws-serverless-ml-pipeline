# Serverless Edge-to-Cloud ML Pipeline (Computer Vision)

![CI/CD](https://img.shields.io/github/actions/workflow/status/vpleshko-lab/aws-edge-ml/deploy.yml?branch=main&label=CI%2FCD&logo=github-actions)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws)
![ONNX](https://img.shields.io/badge/Runtime-ONNX-grey?logo=onnx)
![License](https://img.shields.io/badge/License-MIT-green)

End-to-end inference pipeline for MobileNetV2, deployed on AWS Lambda via Docker with automated CI/CD. Designed for scalability, low cold-start latency, and full observability through Weights & Biases.

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Monitoring & Observability](#monitoring--observability)
- [API Reference](#api-reference)
- [Local Development](#local-development)
- [Cloud Deployment](#cloud-deployment--replication-guide)
- [Environment Variables](#environment-variables)

---

## Architecture

```
Edge Client (Python)
      │
      ▼  HTTP POST /predict
AWS API Gateway
      │
      ▼
AWS Lambda (Docker Container)
  ├── FastAPI + Mangum
  ├── ONNX Runtime (MobileNetV2)
  └── W&B Logging
      │
      ▼
W&B Dashboard (Latency · Confidence · Images)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **ML** | PyTorch (export), ONNX Runtime, MobileNetV2 |
| **API** | FastAPI, Mangum |
| **Cloud** | AWS Lambda, ECR, API Gateway |
| **DevOps** | Docker, GitHub Actions |
| **Monitoring** | Weights & Biases (W&B) |
| **Dependencies** | Poetry |

---

## Project Structure

```
.
├── app/
│   ├── app_main.py          # FastAPI app + Mangum handler
│   ├── model.onnx           # ONNX model
├── scripts/
│   ├── export_onnx.py       # Export PyTorch → ONNX
├── tests/
│   ├── cloud_test.py        # Test request to AWS
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD pipeline
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Monitoring & Observability

Every inference request is logged to W&B, enabling:

| Signal | What it detects |
|---|---|
| **Confidence distribution** | Model drift over time |
| **Inference latency** | Performance regressions after deploys |
| **Input images** | Data quality issues; feeds Active Learning loop |

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

### 1. Clone & install dependencies

```bash
git clone <your-repo-url>
cd <your-repo>
poetry install
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and fill in your keys (see Environment Variables section)
```

### 3. Export the model

```bash
poetry run python scripts/export_onnx.py
# Generates model.onnx in the project root
```

### 4a. Run with Uvicorn (fast iteration)

```bash
poetry run uvicorn app.main:app --reload --port 8000
# API available at http://localhost:8000
# Docs available at http://localhost:8000/docs
```

### 4b. Run with Docker (production-like)

```bash
docker build -t ml-pipeline .
docker run -p 8000:8000 --env-file .env ml-pipeline
```

### 5. Test locally

```bash
poetry run python scripts/test_endpoint.py --url http://localhost:8000 --image ./your_image.jpg
```

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
| `WANDB_API_KEY` | API key from Weights & Biases |

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
# Weights & Biases
WANDB_API_KEY=your_wandb_api_key

# AWS (needed only for local testing against cloud)
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=eu-central-1

```

> **Note:** In the Lambda environment, `AWS_*` credentials are injected automatically via the execution role. Only `WANDB_API_KEY` need to be set as Lambda environment variables.
