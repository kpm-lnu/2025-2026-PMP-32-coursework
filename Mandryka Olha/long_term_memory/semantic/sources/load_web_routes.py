# -*- coding: utf-8 -*-

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("ТЕСТ ЗАПУСК") 
import os
import time
import requests
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://karpaty.rocks"
TRACKS_URL = f"{BASE_URL}/tracks"
SEPARATOR = "=" * 81

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KarpatyRAG/1.0)"
}

DELAY = 0.3  

def get_all_track_urls() -> List[str]:
    urls = []
    page = 1

    while True:
        url = TRACKS_URL if page == 1 else f"{TRACKS_URL}?page={page}"
     
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            break

        try:
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"Parse error page {page}: {e}")
            continue
        links = soup.find_all("a", href=True, string=lambda t: t and "Докладніше" in t)

        added = 0
        for a in links:
            full = urljoin(BASE_URL, a["href"])
            if full not in urls:
                urls.append(full)
                added += 1

        if added == 0:
            break

        page += 1
        time.sleep(DELAY)

    print(f"Found {len(urls)} routes")
    return urls


def extract_semantic_description(soup: BeautifulSoup) -> str:
   
    raw_text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if line.startswith("Про маршрут"):
            start_idx = i + 1
        if start_idx and (
            line.startswith("Що подивитись")
            or line.startswith("Проживання")
            or line.startswith("Коментар")
        ):
            end_idx = i
            break

    if start_idx is None:
        return ""

    content = lines[start_idx:end_idx]

    NOISE = (
        "Facebook", "Tweet", "LinkedIn",
        "Karpaty.ROCKS",
        "Leaflet",
        "OpenStreetMap",
        "Завантажити",
        "Поради туристу від рятувальників",
        "Щоб додати коментар ви можете:",
        "Протягом маршруту Ви зможете побачити:"
    )

    cleaned = []
    for line in content:
        if any(n.lower() in line.lower() for n in NOISE):
            continue
        if len(line) < 20:
            continue
        cleaned.append(line)

    return "\n\n".join(cleaned)


def load_routes(urls: List[str]) -> List[str]:
    docs = []

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")

        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else "Назва маршруту"

        description = extract_semantic_description(soup)

        if not description:
            print("опис не знайдено")
            continue

        docs.append(
            f"""Назва маршруту:
{title}

Опис маршруту:
{description}"""
        )

        time.sleep(DELAY)

    return docs


def save(docs: List[str], path="./long_term_memory/semantic/data/karpaty_routes.txt"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for i, d in enumerate(docs):
            f.write(d)
            if i < len(docs) - 1:
                f.write("\n\n" + SEPARATOR + "\n\n")

    print(f"Saved: {len(docs)} routes")

def main():
    urls = get_all_track_urls()
    docs = load_routes(urls)

    if docs:
        save(docs)
    else:
        print(" НІЧОГО НЕ ЗЧИТАНО")


#if __name__ == "__main__":
#    main()

def main():
    print("Скрепер запуск,,") 
    urls = get_all_track_urls()
    print(f"URL: {len(urls)}")
    docs = load_routes(urls)
    if docs:
        save(docs)
    
if __name__ == "__main__":
    main()