import boto3
import json
import logging

from app.logger_setup import setup_app_logging

setup_app_logging()
logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
LOGS_BUCKET = "aws-ml-logs"
LABELING_BUCKET = "aws-labeling-queue" # окремий бакет для розмітки

def get_uncertain_predictions(confidence_threshold=0.55):
    """Пошук зображень, де модель має низьку confidence"""

    response = s3.list_objects_v2(
        Bucket=LOGS_BUCKET,
        Prefix="metadata/"
    )

    uncertain = []

    for obj in response.get('Contents', []):
        # Read
        meta = json.loads(
            s3.get_object(Bucket=LOGS_BUCKET,
                          Key=obj['Key'])['Body'].read()
        )

        if meta['confidence'] < confidence_threshold:
            uncertain.append(meta)

    return uncertain

def copy_to_labeling_queue(samples):
    """Копіювання зображення в окремий бакет для Label Studio"""
    # перевірка на пустий список
    if not samples:
        logger.info("No uncertain samples found. Nothing to copy.")
        return

    logger.info(f"Starting to copy {len(samples)} samples to {LABELING_BUCKET}...")

    for sample in samples:
        # копіювання зображення
        try:
            s3.copy_object(
                CopySource={
                    'Bucket': LOGS_BUCKET,
                    'Key': sample['image_key']
                },
                Bucket=LABELING_BUCKET,
                Key=sample['image_key']
            )
            logger.info(f"Sent to annotation: {sample['id']} (confidence: {sample['confidence']:.2f})")

        except Exception as e:
            logger.error(f"Failed to copy sample {sample.get('id')}: {e}")

    logger.info("Copying process finished.")

if __name__ == "__main__":
    samples = get_uncertain_predictions()
    # logging
    copy_to_labeling_queue(samples)
