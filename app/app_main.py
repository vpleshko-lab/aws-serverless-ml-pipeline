import io
import time
import numpy as np
import onnxruntime as ort
import wandb
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from mangum import Mangum
from contextlib import asynccontextmanager

app = FastAPI()
handler = Mangum(app)

# завантаження моделі один раз
try:
    ort_session = ort.InferenceSession("app/model.onnx")
    input_name = ort_session.get_inputs()[0].name
except Exception as e:
    print(f"Erorr loading ONNX model: {e}")
    ort_session = None

_wandb_initialized = False


def ensure_wandb_initialized():
    """Ледача ініціалізація - викликається лише при першому запиті"""
    global _wandb_initialized
    if not _wandb_initialized:
        wandb.init(
            project="aws-edge-ml",
            entity="vpleshko-none",
            job_type="inference",
            # режима offline усуваєм таймаут під час ініту, дані синхраться у фоні
            settings=wandb.Settings(mode="online"),
            reinit=True
        )
        _wandb_initialized = True


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
async def predict(file: UploadFile = File(...)):
    if ort_session is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    # 1. Init wandb
    ensure_wandb_initialized()

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

    # 3. Логування в W&B
    wandb.log({
        "prediction": predictes_class,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "image": wandb.Image(Image.open(io.BytesIO(image_bytes)))
    })
    wandb.finish()
    global _wandb_initialized
    _wandb_initialized = False

    return {
        "class_id": predictes_class,
        "confidence": round(confidence, 4),
        "latency_ms": round(latency_ms, 2)
    }
