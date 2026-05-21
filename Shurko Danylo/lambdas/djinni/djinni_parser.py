import logging
import os
import random
import time
from datetime import date, datetime, timedelta

import boto3
import emoji
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
import s3fs
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'YOUR_BUCKET_NAME')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME', 'YOUR_TABLE_NAME')

BASE_URL = "https://djinni.co/api/jobs/"
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
}

ALL_CATEGORIES = [
    "JavaScript", "Fullstack",
    "Java", ".NET", "Python", "PHP",
    "Node.js", "iOS", "Android", "React Native",
    "C++", "Flutter", "Golang",
    "Ruby", "Scala", "Salesforce", "Rust", "Elixir",
    "Kotlin", "ERP", "No Code",
    "QA Manual", "QA Automation", "Design",
    "Artist", "Unity",
    "Project Manager", "Product Manager",
    "Product Owner", "Delivery Manager",
    "Scrum Master",
    "Lead", "DevOps",
    "Security", "Sysadmin", "Business Analyst",
    "Data Science", "Web Analyst",
    "Data Analyst", "Data Engineer", "SQL",
    "Technical Writing",
    "Marketing", "Sales", "Lead Generation",
    "SEO", "HR", "Recruiter",
    "Support",
    "Head Chief", "Finances", "Other"
]


def fetch_all_jobs(categories, start_date, end_date):
    all_jobs = []
    for category in categories:
        all_jobs.extend(fetch_jobs_by_category(category, start_date, end_date))
    return all_jobs


def fetch_jobs_by_category(category, start_date, end_date):
    all_jobs = []
    parameters = {"offset": 0, "category": category}

    while True:
        time.sleep(random.uniform(0.5, 1.5))

        response = requests.get(BASE_URL, params=parameters, headers=HEADERS)
        if response.status_code != 200:
            break

        data = response.json()
        limit = data.get("limit", 10)
        parameters["offset"] += limit
        jobs = data.get("results", [])

        if not jobs:
            break

        for job in jobs:
            published_date = datetime.fromisoformat(job["published"]).date()
            if published_date < start_date:
                return all_jobs
            elif published_date <= end_date:
                result = {
                    "id": job["id"],
                    "title": job["title"],
                    "slug": job["slug"],
                    "company": job["company_name"],
                    "description": clean_text(job["long_description"]),
                    "category": category,
                    "location": job["location"],
                    "experience": job["experience"],
                    "english": job["english"]["name"],
                    "domain": job["domain"],
                    "date": published_date,
                    "dou_link": job["dou_link"],
                    "public_salary_min": job["public_salary_min"],
                    "public_salary_max": job["public_salary_max"],
                    "is_parttime": job["is_parttime"],
                    "has_test": job["has_test"],
                    "is_ukraine_only": job["is_ukraine_only"]
                }
                all_jobs.append(result)

    return all_jobs


def clean_text(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ").strip()
    clean_text = emoji.replace_emoji(text, "")
    return " ".join(clean_text.split())


def save_jobs_to_s3(df, bucket_name, prefix='djinni/processed'):
    table_pa = pa.Table.from_pandas(df)
    s3 = s3fs.S3FileSystem()

    pq.write_to_dataset(
        table_pa,
        root_path=f"s3://{bucket_name}/{prefix}/",
        partition_cols=["date"],
        filesystem=s3
    )


def get_last_date():
    response = table.get_item(Key={'Name': 'last_djinni_date'})
    last_date = response.get('Item', {}).get('Date', None)

    if last_date is None:
        # Note: For the initial backfill, it's highly recommended to run this
        # script locally to fetch all currently available active jobs
        # (usually the last 1-2 months) without hitting the 15-min Lambda
        # timeout.
        # If running in Lambda, change '1970-01-01' to a recent date
        # (e.g., last few weeks).
        return date(1970, 1, 1)

    return date.fromisoformat(last_date)


def lambda_handler(event, context):
    start = get_last_date()
    end = date.today() - timedelta(days=1)

    if start > end:
        logger.info("No new dates to process. Exiting.")
        return {'statusCode': 200, 'body': 'No new dates to process.'}

    logger.info(f"Starting Djinni parser. Date range: {start} to {end}")

    all_jobs = fetch_all_jobs(ALL_CATEGORIES, start, end)

    if all_jobs:
        try:
            df = pd.DataFrame(all_jobs)
            save_jobs_to_s3(df, S3_BUCKET_NAME)
            logger.info(f"Successfully saved {len(all_jobs)} jobs to S3.")
        except Exception as e:
            logger.error(f"Failed to save to S3: {e}")
            raise e

    table.put_item(Item={
        'Name': 'last_djinni_date',
        'Date': date.today().isoformat()
    })
    logger.info("DynamoDB table updated successfully.")

    return {'statusCode': 200, 'body': f'Processed {len(all_jobs)} jobs.'}


if __name__ == "__main__":
    # Fake event and context to simulate AWS Lambda execution locally
    fake_event = {}
    fake_context = None

    logger.info("Starting Lambda execution in local mode...")
    result = lambda_handler(fake_event, fake_context)
    logger.info(f"Local execution completed. Result: {result}")
