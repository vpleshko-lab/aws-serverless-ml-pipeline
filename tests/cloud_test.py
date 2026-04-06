import os
import requests
from dotenv import load_dotenv
import logging
from app.logger_setup import setup_app_logging

load_dotenv()
setup_app_logging()

logger = logging.getLogger(__name__)

URL = os.getenv("ML_API_URL")
IMAGE_PATH = "tests/data/1QT8RpgN4CwDYU20PSep6Ig.jpeg"


def test_inference():
    try:
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": f}
            logger.info(f"Sending request to: {URL}")
            response = requests.post(URL, files=files)

        if response.status_code == 200:
            logger.info(f"Success! Result: {response.json()}")

        else:
            logger.info(
                f"Server returned: {response.status_code}: {response.text}")

    except FileNotFoundError:
        logger.error(f"File not found at {IMAGE_PATH}")
    except Exception as e:
        logger.exception("Unexpected error during request")


if __name__ == "__main__":
    test_inference()
