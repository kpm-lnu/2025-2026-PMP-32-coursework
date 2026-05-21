import json
import logging
import os
from datetime import date, timedelta
from io import BytesIO

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "YOUR_BUCKET_NAME")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE_NAME", "YOUR_TABLE_NAME")
MAX_RECURSION_DEPTH = int(os.environ.get("MAX_RECURSION_DEPTH", 3))

s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def get_earliest_date_from_s3():
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix='dou/raw/date=',
            Delimiter='/',
            MaxKeys=1
        )

        if 'CommonPrefixes' in response and response['CommonPrefixes']:
            first_folder = response['CommonPrefixes'][0]['Prefix']
            date_str = first_folder.split('=')[1].strip('/')
            logger.info(f"Found earliest date in S3: {date_str}")
            return date.fromisoformat(date_str)

        return None
    except Exception as e:
        logger.error(f"Failed to find earliest date in S3: {e}")
        return None


def get_last_aggregated_date():
    try:
        response = table.get_item(Key={'Name': 'last_dou_aggregated_date'})
        last_date = response.get('Item', {}).get('Date')

        if last_date:
            return date.fromisoformat(last_date)

        logger.info("No date in DynamoDB. Searching for the earliest date in S3...")
        earliest_date = get_earliest_date_from_s3()

        if earliest_date:
            return earliest_date
        else:
            logger.error("No data found in S3 either. Exiting.")
            raise RuntimeError("No data available to aggregate.")

    except Exception as e:
        logger.error(f"Failed to read from DynamoDB: {e}")
        raise e


def update_last_aggregated_date(new_date):
    try:
        table.put_item(Item={
            'Name': 'last_dou_aggregated_date',
            'Date': new_date.isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to update DynamoDB: {e}")
        raise e


def lambda_handler(event, context):
    start_date = get_last_aggregated_date()
    current_date = start_date
    end_date = date.today() - timedelta(days=1)

    if start_date > end_date:
        logger.info("No new dates to process. Exiting.")
        return {'statusCode': 200, 'body': 'No new dates to process.'}

    days_processed = 0
    total_vacancies_processed = 0

    invocation_count = event.get('invocation_count', 1)

    while current_date <= end_date:
        # SMART STOP & RECURSION: Save state and self-invoke if time is running out
        if hasattr(context, 'get_remaining_time_in_millis'):
            if context.get_remaining_time_in_millis() < 60000:
                logger.warning(f"Lambda time is running out! Stopping at {current_date}.")

                if invocation_count < MAX_RECURSION_DEPTH:
                    logger.info(f"Triggering self-invocation (Attempt"
                                f" {invocation_count + 1}/{MAX_RECURSION_DEPTH})...")
                    try:
                        lambda_client.invoke(
                            FunctionName=context.function_name,
                            InvocationType='Event',
                            Payload=json.dumps({'invocation_count': invocation_count + 1})
                        )
                    except Exception as e:
                        logger.error(f"Failed to self-invoke: {e}")
                else:
                    logger.error(f"Max recursion depth reached ({MAX_RECURSION_DEPTH}). Stopping entirely.")
                break

        logger.info(f"Aggregating date: {current_date}...")
        prefix = f"dou/raw/date={current_date.isoformat()}/"

        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=prefix)

        json_keys = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.json'):
                        json_keys.append(obj['Key'])

        if not json_keys:
            logger.info(f"No data found for {current_date}. Moving to next day.")
            current_date += timedelta(days=1)
            continue

        day_data = []
        for key in json_keys:
            try:
                response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
                file_content = response['Body'].read().decode('utf-8')
                day_data.append(json.loads(file_content))
            except Exception as e:
                logger.error(f"Failed to read file {key}: {e}")

        if day_data:
            df = pd.DataFrame(day_data)

            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if 'public_salary_min' in df.columns:
                df['public_salary_min'] = pd.to_numeric(df['public_salary_min'], errors='coerce')
            if 'public_salary_max' in df.columns:
                df['public_salary_max'] = pd.to_numeric(df['public_salary_max'], errors='coerce')
            if 'id' in df.columns:
                df['id'] = pd.to_numeric(df['id'], errors='coerce')

            parquet_key = f"dou/processed/date={current_date.isoformat()}/dou_{current_date.isoformat()}.parquet"

            try:
                table_pa = pa.Table.from_pandas(df)
                out_buffer = BytesIO()
                pq.write_table(table_pa, out_buffer)

                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=parquet_key,
                    Body=out_buffer.getvalue()
                )

                total_vacancies_processed += len(df)
                logger.info(f"Successfully saved {len(df)} vacancies to {parquet_key}")
            except Exception as e:
                logger.error(f"Failed to save parquet file {parquet_key}: {e}")
                raise e

        days_processed += 1
        current_date += timedelta(days=1)

    if current_date > start_date:
        update_last_aggregated_date(current_date)
        logger.info(f"DynamoDB successfully updated with next start date: {current_date}")

    return {
        'statusCode': 200,
        'body': (
            f"Processed {days_processed} days ({total_vacancies_processed}"
            f" vacancies). NEXT START DATE: {current_date}"
        )
    }
