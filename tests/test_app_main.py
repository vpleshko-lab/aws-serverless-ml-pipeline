import io
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np
import pytest

# Mock boto3 clients before importing the app module
with patch('app.app_main.s3'), \
     patch('app.app_main.dynamodb'), \
     patch('app.app_main.cloudwatch'), \
     patch('app.app_main.ort.InferenceSession'):
    from app.app_main import preprocess_image
    from fastapi import HTTPException


def make_jpeg_bytes(size=(100, 100), color=(255, 0, 0)):
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_preprocess_image_returns_correct_shape_and_dtype():
    img_bytes = make_jpeg_bytes()
    arr = preprocess_image(img_bytes)
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (1, 3, 224, 224)
    assert arr.dtype == np.float32


def test_preprocess_image_invalid_bytes_raises_http_exception():
    with pytest.raises(HTTPException):
        preprocess_image(b"not-an-image")
