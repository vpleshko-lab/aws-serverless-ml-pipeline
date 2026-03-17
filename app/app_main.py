import io
import time
import numpy as np
import onnxruntime as ort
import wandb
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from mangum import Mangum
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    wandb.init(
        project="aws-edge-ml",
        entity="vpleshko-none",
        job_type="inference")
    yield
    wandb.finish()

app = FastAPI(lifespan=lifespan)
handler = Mangum(app, lifespan="off")

# завантаження моделі один раз
try:
    ort_session = ort.InferenceSession("app/model.onnx")
    input_name = ort_session.get_inputs()[0].name
except Exception as e:
    print(f"Erorr loading ONNX model: {e}")
    ort_session = None


def preprocess_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img = img.resize((224, 224))
        img_data = np.array(img).transpose(2, 0, 1).astype('float32') / 255.0
        return np.expand_dims(img_data, axis=0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if ort_session is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    start_time = time.time()
    image_bytes = await file.read()
    input_tensor = preprocess_image(image_bytes)

    # 2. інференс та метадані
    outputs = ort_session.run(None, {input_name: input_tensor})
    predictes_class = int(np.argmax(outputs[0]))
    confidence = float(np.max(outputs[0]))

    latency_ms = (time.time() - start_time) * 1000

    # 3. Логування в W&B
    wandb.log({
        "prediction": predictes_class,
        "confidence": confidence,
        "latence_ms": latency_ms,
        "image": wandb.Image(Image.open(io.BytesIO(image_bytes)))
    })

    return {
        "class_id": predictes_class,
        "confidence": round(confidence, 4),
        "latency_ms": round(latency_ms, 2)
    }
