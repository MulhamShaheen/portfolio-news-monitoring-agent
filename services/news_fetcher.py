import os
import random
import time

import feedparser
import requests
from bs4 import BeautifulSoup


class YahooFinanceClient:
    """
        Client for fetching and parsing news from Yahoo Finance.
        Supports top stories, market news, and ticker-specific news with retry/backoff.
        """
    RSS_URLS = {
        'top_stories': 'https://finance.yahoo.com/rss/topstories',
        'market_news': 'https://finance.yahoo.com/rss/rssmarketnews',
        'ticker_news': 'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
    }
    MAX_RETRIES = 5
    BACKOFF_FACTOR = 1  # base seconds for exponential backoff
    CONTENT_BLOCK_CLASS = 'atoms-wrapper'
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YahooFinanceClient/1.0 (+https://github.com/yourrepo)',
            'Accept': 'application/rss+xml, application/xml;q=0.9, text/html;q=0.8, text/plain;q=0.7, */*;q=0.5',
            'Accept-Encoding': 'identity',
        })

    def fetch_rss(self, url):
        """Fetch RSS feed content with retry/backoff on 429s."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.session.get(url)
                if response.status_code == 429:
                    wait = self.BACKOFF_FACTOR * (2 ** (attempt - 1)) + random.random()
                    print(f"429 received for RSS; backing off {wait:.1f}s (retry {attempt}/{self.MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return feedparser.parse(response.content)
            except requests.RequestException as e:
                # If non-429 or final attempt, bail out
                if attempt == self.MAX_RETRIES or not getattr(e, 'response', None) or e.response.status_code != 429:
                    print(f"Error fetching RSS feed (attempt {attempt}): {e}")
                    return None
        print("Exceeded maximum retries for RSS feed.")
        return None

    def fetch_page(self, url) -> str:
        """Fetch HTML page content with retry/backoff on 503s and 429s."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.session.get(url)
                if response.status_code in (429, 503):
                    wait = self.BACKOFF_FACTOR * (2 ** (attempt - 1)) + random.random()
                    print(
                        f"{response.status_code} received; backing off {wait:.1f}s (retry {attempt}/{self.MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                # If non-retryable or last try, return None
                status = getattr(e, 'response', None).status_code if getattr(e, 'response', None) else None
                if attempt == self.MAX_RETRIES or status not in (429, 503):
                    print(f"Error fetching page (attempt {attempt}): {e}")
                    return None
        print("Exceeded maximum retries for page fetch.")
        return None

    def get_ticker_news(self, ticker, count=10, with_content=False):
        """
        Fetch news for a specific ticker symbol using yahoo_fin's get_yf_rss.
        Returns a list of dicts with keys: title, link, summary.
        Handles errors gracefully and skips problematic articles.
        """
        yf_rss_url = self.RSS_URLS['ticker_news'].format(ticker=ticker)
        try:
            feed = feedparser.parse(yf_rss_url)
            news_items = feed.entries
            result = []
            for item in news_items[:count]:
                try:
                    article = {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "summary": item.get("summary"),
                    }
                    if with_content:
                        item_page = self.fetch_page(item.get("link"))
                        if item_page:
                            content = self.get_content_from_html(item_page)
                            article["content"] = content
                        else:
                            print(f"Failed to fetch content for article '{item.get('title', '')}'")
                            continue
                    result.append(article)
                except Exception as article_exc:
                    print(f"Error processing article '{item.get('title', '')}': {article_exc}")
                    continue
            return result
        except Exception as e:
            print(f"Error fetching ticker news for {ticker}: {e}")
            return []

    def get_html_from_url(self, url):
        """
        Fetch the HTML page from the URL and return the text inside the first div with content block class.
        Returns None if not found or on error.
        """
        html = self.fetch_page(url)
        if not html:
            return None
        return html

    def get_content_from_html(self, html):
        """
        Extract and return the text inside the first div with content block class from the given HTML.
        Returns None if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", class_=self.CONTENT_BLOCK_CLASS)
        if div:
            return div.get_text(strip=True)
        return None


    def fetch_news(self, ticker: str, max_articles: int = 5):
        return self.get_ticker_news(ticker, count=max_articles)


fetcher = YahooFinanceClient()