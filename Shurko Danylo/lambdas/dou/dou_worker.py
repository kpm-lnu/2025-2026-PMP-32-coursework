import json
import logging
import os
import random
import time

import boto3
import emoji
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "YOUR_BUCKET_NAME")
s3 = boto3.client('s3')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}


def get_vacancy_details(vacancy_url):
    time.sleep(random.uniform(1.0, 2.0))
    try:
        response = requests.get(vacancy_url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception(f"HTTP status {response.status_code}")

        soup = BeautifulSoup(response.content, "html.parser")

        clean_url = vacancy_url.split('?')[0].rstrip('/')
        url_parts = clean_url.split('/')

        job_id = url_parts[-1]
        slug = "/".join(url_parts[-3:])
        dou_link = "/".join(url_parts[:-2])

        h1 = soup.find("h1", class_="g-h2")
        title = h1.text.strip() if h1 else None

        location_span = soup.find("span", class_="place")
        location = location_span.text.strip() if location_span else None

        company_div = soup.find("div", class_="l-n")
        company = company_div.find("a").text.strip() if company_div and company_div.find("a") else None

        description_div = soup.find("div", class_="b-typo vacancy-section")
        description = None
        if description_div:
            text = description_div.get_text(separator=" ", strip=True).replace('\xa0', ' ')
            text = emoji.replace_emoji(text, "")
            description = " ".join(text.split())

        salary_span = soup.find("span", class_="salary")
        salary_min, salary_max = None, None

        if salary_span:
            salary_text = salary_span.text.strip()
            try:
                if '–' in salary_text:
                    parts = salary_text.split('–')
                    salary_min = int(''.join(filter(str.isdigit, parts[0])))
                    salary_max = int(''.join(filter(str.isdigit, parts[1])))
                elif ' від' in salary_text:
                    salary_min = int(''.join(filter(str.isdigit, salary_text)))
                elif ' до' in salary_text:
                    salary_max = int(''.join(filter(str.isdigit, salary_text)))
                else:
                    salary_min = int(''.join(filter(str.isdigit, salary_text)))
                    salary_max = salary_min
            except (ValueError, IndexError):
                pass

        return {
            "id": job_id,
            "title": title,
            "slug": slug,
            "company": company,
            "description": description,
            "category": None,
            "location": location,
            "date": None,
            "dou_link": dou_link,
            "public_salary_min": salary_min,
            "public_salary_max": salary_max,
        }
    except Exception as e:
        logger.error(f"Failed to parse vacancy {vacancy_url}: {e}")
        return None


def save_to_s3(data):
    job_id = data.get('id', 'unknown_id')
    job_date = data.get('date', 'unknown_date')

    s3_key = f"dou/raw/date={job_date}/{job_id}.json"

    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data, ensure_ascii=False),
            ContentType='application/json'
        )
        logger.info(f"Successfully saved to S3: {s3_key}")
    except Exception as e:
        logger.error(f"Failed to save {s3_key} to S3: {e}")
        raise e


def lambda_handler(event, context):
    for record in event.get('Records', []):
        body = json.loads(record['body'])
        url = body.get('url')
        category = body.get('category')
        job_date = body.get('date')

        logger.info(f"Processing vacancy: {url}")

        job_details = get_vacancy_details(url)

        if job_details:
            job_details["category"] = category
            job_details["date"] = job_date
            save_to_s3(job_details)
        else:
            # Raise an exception to fail the SQS message processing.
            # This ensures the message returns to the queue or goes to
            # a DLQ (Dead Letter Queue).
            error_msg = f"Failed to extract details for {url}"
            logger.error(error_msg)
            raise Exception(error_msg)

    return {'statusCode': 200, 'body': 'Batch processed successfully.'}
