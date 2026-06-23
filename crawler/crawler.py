import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "news.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

KEYWORDS = ["CVE", "취약점", "정보유출", "개인정보", "랜섬웨어", "해킹", "보안사고"]


def get_soup(url):
    response = requests.get(url, headers=HEADERS, timeout=5)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def classify_category(title):
    if "랜섬웨어" in title:
        return "랜섬웨어"
    if "유출" in title or "개인정보" in title:
        return "정보유출"
    if "CVE" in title or "취약점" in title:
        return "CVE"
    if "해킹" in title or "공격" in title:
        return "보안사고"
    return "보안동향"


def extract_tags(title):
    return [keyword for keyword in KEYWORDS if keyword in title]


def normalize_date(text):
    """
    2026-06-24, 2026.06.24, 2026/06/24 형태를 YYYY-MM-DD로 변환
    """
    match = re.search(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})", text)
    if not match:
        return None

    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def is_article_url(url):
    """
    실제 기사 URL만 허용
    """
    allow_patterns = [
        "boannews.com/media/view.asp?idx=",
        "dailysecu.com/news/articleView.html?idxno="
    ]

    block_keywords = [
        "privacy",
        "ad_info",
        "login",
        "member",
        "company",
        "com/privacy"
    ]

    if not any(pattern in url for pattern in allow_patterns):
        return False

    if any(keyword in url for keyword in block_keywords):
        return False

    return True


def crawl_article_detail(url, source):
    soup = get_soup(url)
    page_text = soup.get_text(" ", strip=True)

    article_date = normalize_date(page_text)

    title = ""

    if soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    elif soup.find("h3"):
        title = soup.find("h3").get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    title = re.sub(r"\s+", " ", title).strip()

    if not title:
        return None

    if not any(keyword in title for keyword in KEYWORDS):
        return None

    return {
        "article_date": article_date,
        "category": classify_category(title),
        "title": title,
        "summary": title,
        "detail": "기사 원문을 통해 상세 내용을 확인할 수 있습니다.",
        "source": source,
        "url": url,
        "tags": extract_tags(title)
    }


def collect_links_from_boannews():
    search_urls = [
        "https://www.boannews.com/search/news_total.asp?search=title&find=취약점",
        "https://www.boannews.com/search/news_total.asp?search=title&find=CVE",
        "https://www.boannews.com/search/news_total.asp?search=title&find=공격",
        "https://www.boannews.com/search/news_total.asp?search=title&find=랜섬웨어"
    ]

    links = []

    for search_url in search_urls:
        soup = get_soup(search_url)

        for a in soup.select("a[href]"):
            href = a.get("href")
            url = urljoin("https://www.boannews.com", href)

            if is_article_url(url):
                links.append({
                    "url": url,
                    "source": "보안뉴스"
                })

    return links


def collect_links_from_dailysecu():
    search_urls = [
        "https://www.boannews.com/search/news_total.asp?search=title&find=유출",
        "https://www.boannews.com/search/news_total.asp?search=title&find=개인정보",
        "https://www.boannews.com/search/news_total.asp?search=title&find=해킹"
    ]

    links = []

    for search_url in search_urls:
        soup = get_soup(search_url)

        for a in soup.select("a[href]"):
            href = a.get("href")
            url = urljoin("https://www.dailysecu.com", href)

            if is_article_url(url):
                links.append({
                    "url": url,
                    "source": "데일리시큐"
                })

    return links


def remove_duplicate_links(link_list):
    seen = set()
    result = []

    for item in link_list:
        if item["url"] not in seen:
            seen.add(item["url"])
            result.append(item)

    return result


def save_news(news_list):
    today = datetime.now().strftime("%Y-%m-%d")

    result = []

    for idx, news in enumerate(news_list, start=1):
        result.append({
            "id": idx,
            "crawl_date": today,
            "article_date": news["article_date"],
            "category": news["category"],
            "title": news["title"],
            "summary": news["summary"],
            "detail": news["detail"],
            "source": news["source"],
            "url": news["url"],
            "tags": news["tags"]
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def main():
    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

    links = []
    links.extend(collect_links_from_boannews())
    links.extend(collect_links_from_dailysecu())

    links = remove_duplicate_links(links)

    news_list = []

    for item in links:
        try:
            article = crawl_article_detail(item["url"], item["source"])

            if article is None:
                continue

            if article["article_date"] != today:
                continue

            news_list.append(article)

            time.sleep(0.5)

        except Exception as e:
            print(f"[기사 수집 실패] {item['url']} / {e}")

    save_news(news_list)

    print(f"오늘 기사 {len(news_list)}개를 저장했습니다.")


if __name__ == "__main__":
    main()