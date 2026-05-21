import json
import logging
import os
import random
import time
from datetime import date
from urllib.parse import quote

import boto3
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "YOUR_SQS_QUEUE_URL")
sqs = boto3.client('sqs')

UA_MONTHS = {
    'січня': 1, 'лютого': 2, 'березня': 3, 'квітня': 4, 'травня': 5,
    'червня': 6, 'липня': 7, 'серпня': 8, 'вересня': 9, 'жовтня': 10,
    'листопада': 11, 'грудня': 12
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}


def parse_dou_date(date_text):
    parts = date_text.strip().split()
    if len(parts) < 2:
        return None
    try:
        day = int(parts[0])
        month_str = parts[1].lower()
        month = UA_MONTHS.get(month_str)
        if not month:
            return None
        year = int(parts[2]) if len(parts) == 3 else date.today().year
        return date(year, month, day)
    except ValueError:
        return None


def get_real_date_from_page(job_url):
    time.sleep(random.uniform(0.5, 1.5))
    try:
        response = requests.get(job_url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        date_div = soup.find("div", class_="date")
        if not date_div:
            return None
        return parse_dou_date(date_div.text.strip())
    except Exception as e:
        logger.error(f"Failed to extract date from {job_url}: {e}")
        return None


def fetch_dou_jobs_ajax(category):
    # Encode for query params (e.g., 'C++' -> 'C%2B%2B')
    encoded_category = quote(category)

    # Prevent UnicodeEncodeError for Cyrillic headers
    header_category = encoded_category if not category.isascii() else category

    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers.update({
        "Referer": f"https://jobs.dou.ua/vacancies/?category={header_category}",
        "x-requested-with": "XMLHttpRequest"
    })
    base_url = f"https://jobs.dou.ua/vacancies/?category={encoded_category}"
    xhr_url = f"https://jobs.dou.ua/vacancies/xhr-load/?category={encoded_category}"

    all_vacancies_html = []
    response = session.get(base_url)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]
    except TypeError:
        return []

    first_batch = soup.find_all("li", class_="l-vacancy")
    all_vacancies_html.extend(first_batch)

    if len(first_batch) < 20:
        return all_vacancies_html

    count = 20

    while True:
        try:
            time.sleep(random.uniform(1.0, 2.5))
            payload = {"csrfmiddlewaretoken": csrf_token, "count": count}
            response = session.post(xhr_url, data=payload)
            data = response.json()
            is_last = data.get("last", False)
            new_html = data.get("html", "")

            if not new_html:
                break

            soup_chunk = BeautifulSoup(new_html, "html.parser")
            new_items = soup_chunk.find_all("li", class_="l-vacancy")
            if not new_items:
                break

            all_vacancies_html.extend(new_items)
            if is_last:
                break
            count += 40
        except Exception as e:
            logger.warning(f"Error during AJAX pagination for {category}: {e}")
            break

    return all_vacancies_html


def send_to_sqs_in_batches(messages):
    success_count = 0
    for i in range(0, len(messages), 10):
        batch = messages[i:i + 10]
        entries = []
        for idx, msg in enumerate(batch):
            entries.append({
                'Id': str(idx),
                'MessageBody': json.dumps(msg, default=str)
            })

        try:
            response = sqs.send_message_batch(
                QueueUrl=SQS_QUEUE_URL,
                Entries=entries
            )
            success_count += len(response.get('Successful', []))
        except Exception as e:
            logger.error(f"Failed to send batch to SQS: {e}")

    return success_count


def fetch_links_by_category(category, start_date, end_date):
    raw_vacancies = fetch_dou_jobs_ajax(category)
    messages_to_send = []

    for item in raw_vacancies:
        title_div = item.find("div", class_="title")
        if not title_div:
            continue

        link_tag = title_div.find("a", class_="vt")
        if not link_tag:
            continue

        link = link_tag['href']

        date_div = item.find("div", class_="date")
        date_text = date_div.text.strip() if date_div else ""
        is_hot = '__hot' in item.get('class', [])
        job_date = parse_dou_date(date_text)

        if not job_date:
            continue

        is_valid_date = False
        if start_date <= job_date <= end_date:
            is_valid_date = True
        elif job_date > end_date:
            continue
        else:
            # Fetch the detail page to get the real date (DOU often caches
            # old dates for bumped jobs).
            real_date = get_real_date_from_page(link)
            if real_date and start_date <= real_date <= end_date:
                is_valid_date = True
                job_date = real_date
            elif not is_hot:
                break

        if is_valid_date:
            messages_to_send.append({
                "url": link,
                "category": category,
                "date": job_date.isoformat() if job_date else None
            })

    return messages_to_send


def lambda_handler(event, context):
    start_date_str = event.get("start_date")
    end_date_str = event.get("end_date")
    category = event.get("category")

    if not start_date_str or not end_date_str or not category:
        logger.error("Missing required parameters in event payload.")
        return {'statusCode': 400, 'body': 'Missing parameters'}

    start_date = date.fromisoformat(start_date_str)
    end_date = date.fromisoformat(end_date_str)

    logger.info(f"Processing category '{category}' from {start_date} to {end_date}")

    total_sent = 0

    try:
        messages = fetch_links_by_category(category, start_date, end_date)

        if messages:
            total_sent = send_to_sqs_in_batches(messages)
            logger.info(f"Successfully sent {total_sent} messages to SQS for category '{category}'")
        else:
            logger.info(f"No valid jobs found for category '{category}' in the specified date range.")

    except Exception as e:
        logger.error(f"CRASH in category '{category}': {e}")
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully sent {total_sent} links to SQS.')
    }
