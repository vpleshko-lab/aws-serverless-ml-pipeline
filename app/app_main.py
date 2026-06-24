import os
import io
import time
import uuid
import boto3
import numpy as np
import mlflow
from mlflow.tracking import MlflowClient  # noqa: F401
import onnxruntime as ort
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from PIL import Image
from mangum import Mangum
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from .logger_setup import setup_app_logging

# Logger
setup_app_logging()
logger = logging.getLogger(__name__)

# S3 Client
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb').Table("InferenceLogs")
cloudwatch = boto3.client('cloudwatch')

# Configuration
LOGS_BUCKET = "aws-ml-logs"
MODEL_VERSION = "v1.0.0"
DIMENSIONS = [
    {'Name': 'Model', 'Value': MODEL_VERSION},
    {'Name': 'Project', 'Value': 'CloudPipeline'}
]

# Динамічне завантаження моделі з MLflow


def load_model_from_registry():
    """Завантажує ONNX модель з віддаленого або локального реєстру Mlflow"""
    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)

    model_name = "Classification-MobileNet"
    model_stage = "Production"  # тег моделі, яку імпортуєш

    logger.info(
        f"Connecting to Mlflow at {tracking_uri} to fetch model '{model_name}'...")

    model_uri = f"models://{model_name}/{model_stage}"

    local_model_dir = mlflow.artifacts.download_artifacts(
        artifact_uri=model_uri)
    onnx_path = os.path.join(local_model_dir, "model.onnx")

    return onnx_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    ort_session = None
    input_name = None
    # Ініціалізація сесії один раз при старті контейнера
    try:
        onnx_model_path = load_model_from_registry()

        ort_session = ort.InferenceSession(onnx_model_path)
        input_name = ort_session.get_inputs()[0].name
        logger.info("Model ONNX is succesfull load")
    except Exception as e:
        logger.error(f"Error while loading model from Mlflow: {e}")
        # fallback на локальну модель
        try:
            ort_session = ort.InferenceSession("app/model.onnx")
            input_name = ort_session.get_inputs()[0].name
            logger.warning(
                "Fallback: Loaded local model.onnx instead of MLflow")
        except Exception as local_err:
            logger.critical(
                f"Critical: All model sources failed. Inference offline: {local_err}")
            ort_session = None
    yield {"ort_session": ort_session, "input_name": input_name}

    logger.info("Shutting down application")

app = FastAPI(lifespan=lifespan)
handler = Mangum(app)


def preprocess_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img = img.resize((224, 224))

        img_data = np.array(img).transpose(2, 0, 1).astype('float32') / 255.0

        mean = np.array([0.485, 0.456, 0.406],
                        dtype=np.float32).reshape(3, 1, 1)
        std = np.array([0.229, 0.224, 0.225],
                       dtype=np.float32).reshape(3, 1, 1)
        img_data = (img_data - mean) / std

        return np.expand_dims(img_data, axis=0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")


@app.post("/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    # діставання моделі зі стану додатка
    ort_session = request.state.ort_session
    input_name = request.state.input_name

    if ort_session is None:
        raise HTTPException(status_code=500, detail="Inference engine offline")

    start_time = time.time()
    image_bytes = await file.read()

    # 1. Inference
    input_tensor = preprocess_image(image_bytes)
    outputs = ort_session.run(None, {input_name: input_tensor})

    # 1.1 Soft max для отримання ймовірностей
    logits = outputs[0][0]
    exp_logits = np.exp(logits - np.max(logits))
    probabilities = exp_logits / exp_logits.sum()
    # 1.2 Метадані предікту
    predicted_class = int(np.argmax(probabilities))
    confidence = float(np.max(probabilities))
    latency_ms = (time.time() - start_time) * 1000

    # 2. Логування
    log_id = str(uuid.uuid4())
    now = datetime.utcnow()
    timestamp = now.isoformat() + "Z"
    s3_key = f"inferences/{now.strftime('%Y/%m/%d')}/{log_id}.jpg"
    log_status = "logged"
    logging_error = None

    try:
        # Збереження image to S3
        s3.put_object(Bucket=LOGS_BUCKET, Key=s3_key,
                      Body=image_bytes, ContentType="image/jpeg")

        # Write metadata to DynamoDB
        dynamodb.put_item(
            Item={
                'prediction_id': log_id,
                'timestamp': timestamp,
                'predicted_class': predicted_class,
                'confidence': str(round(confidence, 4)),
                'latency_ms': str(round(latency_ms, 2)),
                's3_path': s3_key,
                'model_version': MODEL_VERSION,
                'is_labeled': str(False),
                'project': 'Cloud_Pipeline'
            }
        )

        # Відправка метрики в CloudWatch
        cloudwatch.put_metric_data(
            Namespace="ML_Production",
            MetricData=[
                {
                    "MetricName": "InferenceConfidence",
                    "Value": confidence,
                    "Unit": 'None',
                    "Dimensions": DIMENSIONS
                },
                {
                    "MetricName": "Latency",
                    "Value": latency_ms,
                    "Unit": "Milliseconds",
                    "Dimensions": DIMENSIONS
                }
            ]
        )
    except Exception as e:
        logger.error(f"Logging failed: {e}")
        log_status = "logging_failed"
        logging_error = str(e)

    response = {
        "log_id": log_id,
        "class": predicted_class,
        "confidence": round(confidence, 4),
        "status": log_status,
        "latency_ms": round(latency_ms, 3)
    }
    if logging_error:
        response["error"] = logging_error

    return response
