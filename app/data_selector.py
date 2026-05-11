import boto3
from boto3.dynamodb.conditions import Key, Attr
import os

dynamodb = boto3.resource('dynamodb').Table("InferenceLogs")
s3 = boto3.client('s3')

def handler(event, context):
    # логіка вибору
    response = dynamodb.query(
        IndexName="ActiveLearningIndex",
        KeyConditionExpression=Key('is_labeled').eq('False'),
        FilterExpression=Attr('confidence').between('0.0', '0.6'),
        Limit=20
    )

    items = response.get('Items', [])
    for item in items:
        # копіювання в S3
        s3.copy_object(
            CopySource={'Bucket':'aws-ml-logs', 'Key': item['s3_path']},
            Bucket='aws-labeling-queue',
            Key=f"pending/{item['prediction_id']}.jpg"
        )

        # оновлення статусу в DYNAMODB
        dynamodb.update_item(
            Key={'prediction_id': item['prediction_id'], 'timestamp': item['timestamp']},
            UpdateExpression="SET is_labeled = :val",
            ExpressionAttributeValues={':val': 'In_Review'}
        )

    return {'status': "success", "processed": len(items)}
