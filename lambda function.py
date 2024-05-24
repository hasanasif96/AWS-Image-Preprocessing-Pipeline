import boto3
import json
import os
from PIL import Image
import io

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def handler(event, context):
    queue_url = os.environ['QUEUE_URL']
    messages = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    ).get('Messages', [])
    
    if not messages:
        return

    for message in messages:
        receipt_handle = message['ReceiptHandle']
        body = message['Body']

        # Assuming body contains S3 object details
        s3_info = json.loads(body)
        bucket = s3_info['Records'][0]['s3']['bucket']['name']
        key = s3_info['Records'][0]['s3']['object']['key']

        # Download image from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        img_data = response['Body'].read()

        # Process the image
        img = Image.open(io.BytesIO(img_data))
        img = img.convert('L')  # Example transformation

        buffer = io.BytesIO()
        img.save(buffer, 'JPEG')
        buffer.seek(0)

        # Upload processed image to another S3 bucket
        s3.put_object(Bucket='processed-images-bucket', Key=key, Body=buffer)

        # Delete the message from the queue
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
