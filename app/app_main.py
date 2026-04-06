import io
import time
import json
import uuid
import boto3
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from mangum import Mangum
from datetime import datetime
import logging
from logger_setup import setup_app_logging

# Logger
setup_app_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
handler = Mangum(app)

# S3 Client - ініт один раз при старті контейнера
s3 = boto3.client('s3')
LOGS_BUCKET = "aws-ml-logs"

# завантаження моделі один раз
try:
    ort_session = ort.InferenceSession("app/model.onnx")
    input_name = ort_session.get_inputs()[0].name
    logger.info("Model ONNX is succesfull load")
except Exception as e:
    logger.error(f"Error while loading model: {e}")
    ort_session = None


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


def log_to_s3(image_bytes: bytes, predicted_class: int, confidence: float, latency_ms: float):
    """Збереження зображень + метаданів в S3 для Data flywheel"""
    log_id = str(uuid.uuid4())

    # зображення
    s3.put_object(
        Bucket=LOGS_BUCKET,
        Key=f"images/{log_id}.jpg",
        Body=image_bytes,
        ContentType="image/jpeg"
    )

    # метадані окремо задля легкого читання без завантаження зобрж
    s3.put_object(
        Bucket=LOGS_BUCKET,
        Key=f"metadata/{log_id}.json",
        Body=json.dumps({
            "id": log_id,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "image_key": f"images/{log_id}.jpg"
        }),
        ContentType="application/json"
    )

    return log_id


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if ort_session is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    start_time = time.time()
    image_bytes = await file.read()
    input_tensor = preprocess_image(image_bytes)

    # 2. інференс та метадані
    outputs = ort_session.run(None, {input_name: input_tensor})
    # soft max
    logits = outputs[0][0]
    exp_logits = np.exp(logits - np.max(logits))
    probabilities = exp_logits / exp_logits.sum()

    predictes_class = int(np.argmax(probabilities))
    confidence = float(np.max(probabilities))
    latency_ms = (time.time() - start_time) * 1000

    # 3. Логування в S3
    log_id = log_to_s3(image_bytes, predictes_class, confidence, latency_ms)

    return {
        "class_id": predictes_class,
        "confidence": round(confidence, 4),
        "latency_ms": round(latency_ms, 2),
        "log_id": log_id
    }
