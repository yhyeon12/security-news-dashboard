import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

OUTPUT_PATH = "./data/news.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

KEYWORDS = [
    "CVE",
    "취약점",
    "정보유출",
    "개인정보",
    "랜섬웨어",
    "해킹",
    "보안사고"
]


def classify_category(title):
    if "CVE" in title or "취약점" in title:
        return "CVE"
    elif "유출" in title or "개인정보" in title:
        return "정보유출"
    elif "랜섬웨어" in title:
        return "랜섬웨어"
    elif "해킹" in title or "공격" in title:
        return "보안사고"
    else:
        return "보안동향"


def crawl_boannews():
    url = "https://www.boannews.com/search/news_total.asp?search=title&find=CVE"
    base_url = "https://www.boannews.com"

    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    news_list = []

    links = soup.select("a")

    for link in links:
        title = link.get_text(strip=True)
        href = link.get("href")

        if not title or not href:
            continue

        if any(keyword in title for keyword in KEYWORDS):
            news_list.append({
                "title": title,
                "url": urljoin(base_url, href),
                "source": "보안뉴스",
                "category": classify_category(title)
            })

    return news_list


def crawl_dailysecu():
    url = "https://www.dailysecu.com/news/articleList.html?sc_area=A&view_type=sm&sc_word=CVE"
    base_url = "https://www.dailysecu.com"

    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    news_list = []

    links = soup.select("a")

    for link in links:
        title = link.get_text(strip=True)
        href = link.get("href")

        if not title or not href:
            continue

        if any(keyword in title for keyword in KEYWORDS):
            news_list.append({
                "title": title,
                "url": urljoin(base_url, href),
                "source": "데일리시큐",
                "category": classify_category(title)
            })

    return news_list


def remove_duplicates(news_list):
    seen = set()
    unique_news = []

    for news in news_list:
        key = news["url"]

        if key not in seen:
            seen.add(key)
            unique_news.append(news)

    return unique_news


def save_news(news_list):
    today = datetime.now().strftime("%Y-%m-%d")

    result = []

    for idx, news in enumerate(news_list, start=1):
        result.append({
            "id": idx,
            "date": today,
            "category": news["category"],
            "title": news["title"],
            "summary": news["title"],
            "detail": "기사 원문을 통해 상세 내용을 확인할 수 있습니다.",
            "source": news["source"],
            "url": news["url"],
            "tags": extract_tags(news["title"])
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def extract_tags(title):
    tags = []

    for keyword in KEYWORDS:
        if keyword in title:
            tags.append(keyword)

    return tags


def main():
    all_news = []

    try:
        all_news.extend(crawl_boannews())
    except Exception as e:
        print(f"[보안뉴스 크롤링 실패] {e}")

    try:
        all_news.extend(crawl_dailysecu())
    except Exception as e:
        print(f"[데일리시큐 크롤링 실패] {e}")

    all_news = remove_duplicates(all_news)

    save_news(all_news)

    print(f"{len(all_news)}개의 기사를 저장했습니다.")


if __name__ == "__main__":
    main()