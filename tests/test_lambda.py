import pytest
import requests
import glob
import os

URL = "https://hph4sxhs7mk65c65o4klg6wpo40qdgbv.lambda-url.eu-central-1.on.aws/predict"
IMAGE_TEST_FOLDER = "tests/data/*.jpeg"

# acces to all files
images = glob.glob(IMAGE_TEST_FOLDER)


@pytest.mark.parametrize("image_path", images)
def test_inference(image_path):
    print(f"\nTesting image: {image_path}")

    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(URL, files=files)

    assert response.status_code == 200, f"Error {response.status_code}: {response.text}"

    result = response.json()
    assert "class_id" in result or "confidence" in result or "latency_ms" in result
    print(f"Result for {os.path.basename(image_path)}: {result}")
