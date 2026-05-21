import json
import logging
import os
import random
import time
from datetime import date, timedelta

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME', 'YOUR_TABLE_NAME')
PRODUCER_NAME = os.environ.get('PRODUCER_FUNCTION_NAME', 'YOUR_PRODUCER_NAME')

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

ALL_CATEGORIES = [
    ".NET", "Account Manager", "AI/ML", "Analyst", "Android",
    "Animator", "Architect", "Artist", "Assistant", "Big Data",
    "Blockchain", "C++", "C-level", "Copywriter", "Data Engineer",
    "Data Science", "DBA", "Design", "DevOps", "Embedded",
    "Engineering Manager", "Erlang", "ERP/CRM", "Finance", "Flutter",
    "Front End", "Golang", "Hardware", "HR", "iOS/macOS",
    "Java", "Legal", "Marketing", "No-code", "Node.js",
    "Office Manager", "Other", "PHP", "Product Manager", "Project Manager",
    "Python", "QA", "React Native", "Ruby", "Rust",
    "Sales", "Salesforce", "SAP", "Scala", "Scrum Master",
    "Security", "SEO", "Support", "SysAdmin", "Technical Writer",
    "Unity", "Unreal Engine", "Військова справа"
]


def get_last_date():
    try:
        response = table.get_item(Key={'Name': 'last_dou_date'})
        last_date = response.get('Item', {}).get('Date', None)

        if last_date is None:
            return date(1970, 1, 1)

        return date.fromisoformat(last_date)
    except Exception as e:
        logger.error(f"Failed to read from DynamoDB: {e}")
        raise e


def lambda_handler(event, context):
    start_date = get_last_date()
    end_date = date.today() - timedelta(days=1)

    if start_date > end_date:
        logger.info("No new dates to process. Exiting.")
        return {'statusCode': 200, 'body': 'No new dates to process.'}

    logger.info(f"Starting DOU dispatcher. Date range: {start_date} to {end_date}")

    for category in ALL_CATEGORIES:
        payload = {
            "category": category,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

        try:
            lambda_client.invoke(
                FunctionName=PRODUCER_NAME,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            logger.info(f"Dispatched producer for: {category}")
        except Exception as e:
            logger.error(f"Failed to invoke producer for category '{category}': {e}")
            raise e

        time.sleep(random.uniform(1.5, 3.5))

    try:
        table.put_item(Item={
            'Name': 'last_dou_date',
            'Date': date.today().isoformat()
        })
        logger.info("DynamoDB table updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update DynamoDB: {e}")
        raise e

    return {
        "statusCode": 200,
        "body": f"Successfully dispatched {len(ALL_CATEGORIES)} categories."
    }
