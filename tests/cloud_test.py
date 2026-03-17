import requests

URL = "https://hph4sxhs7mk65c65o4klg6wpo40qdgbv.lambda-url.eu-central-1.on.aws/predict"

IMAGE_PATH = "tests/1QT8RpgN4CwDYU20PSep6Ig.jpeg"


def test_inference():
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": f}
        print(f"Send request to AWS Lambda")
        response = requests.post(URL, files=files)

    if response.status_code == 200:
        print("Done!")
        print(f"Result: {response.json()}")

    else:
        print(f"Error {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    test_inference()
