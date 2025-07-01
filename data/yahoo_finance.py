import argparse
import json
import requests
import feedparser
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from yahoo_fin import news as si_news


class YahooFinanceClient:
    """
    Client for fetching and parsing news from Yahoo Finance.
    Supports top stories, market news, and ticker-specific news with retry/backoff.
    """
    RSS_URLS = {
        'top_stories': 'https://finance.yahoo.com/rss/topstories',
        'market_news': 'https://finance.yahoo.com/rss/rssmarketnews',
    }
    MAX_RETRIES = 5
    BACKOFF_FACTOR = 1  # base seconds for exponential backoff

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YahooFinanceClient/1.0 (+https://github.com/yourrepo)'
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

    def fetch_page(self, url):
        """Fetch HTML page content with retry/backoff on 503s and 429s."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self.session.get(url)
                if response.status_code in (429, 503):
                    wait = self.BACKOFF_FACTOR * (2 ** (attempt - 1)) + random.random()
                    print(f"{response.status_code} received; backing off {wait:.1f}s (retry {attempt}/{self.MAX_RETRIES})")
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

    def get_top_stories(self):
        """Return top story news items from RSS."""
        feed = self.fetch_rss(self.RSS_URLS['top_stories'])
        return self._parse_feed(feed) if feed else []

    def get_market_news(self):
        """Return market news items from RSS."""
        feed = self.fetch_rss(self.RSS_URLS['market_news'])
        return self._parse_feed(feed) if feed else []

    def get_ticker_news(self, ticker, count=10):
        """
        Fetch news for a specific ticker symbol using yahoo_fin's get_yf_rss.
        Returns a list of dicts with keys: title, link, summary.
        """
        try:
            news_items = si_news.get_yf_rss(ticker)
            result = []
            for item in news_items[:count]:
                result.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "summary": item.get("summary"),
                })
            return result
        except Exception as e:
            print(f"Error fetching ticker news for {ticker}: {e}")
            return []


    def get_news_from_html(self, html, count=10):
        """
        Extract ticker news from Yahoo Finance HTML page content.
        Returns a list of news items.
        """
        data = self._extract_json(html)
        return self._parse_ticker_json(data, count)

    def get_rss_from_html(self, html):
        """
        Parse RSS feed items from HTML/XML content.
        Returns a list of news items.
        """
        feed = feedparser.parse(html)
        return self._parse_feed(feed) if feed else []

    def get_atoms_wrapper_text_from_url(self, url):
        """
        Fetch the HTML page from the URL and return the text inside the first div with class 'atoms-wrapper'.
        Returns None if not found or on error.
        """
        html = self.fetch_page(url)
        if not html:
            return None
        return self.get_atoms_wrapper_text_from_html(html)

    def get_atoms_wrapper_text_from_html(self, html):
        """
        Extract and return the text inside the first div with class 'atoms-wrapper' from the given HTML.
        Returns None if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", class_="atoms-wrapper")
        if div:
            return div.get_text(strip=True)
        return None

    def _parse_feed(self, feed):
        """Convert a feedparser feed to a list of dicts."""
        items = []
        for entry in feed.entries:
            summary = entry.get('summary') or entry.get('description') or ''
            items.append({
                'title': entry.get('title'),
                'link': entry.get('link'),
                'published': entry.get('published') or entry.get('updated'),
                'summary': summary.strip(),
            })
        return items

    def _extract_json(self, html):
        """Extract JSON data from Yahoo Finance page HTML."""
        import re
        pattern = re.compile(r'root.App.main\s*=\s*(\{.*?\});', re.DOTALL)
        match = pattern.search(html)
        if not match:
            print("Could not find JSON data in page HTML.")
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            print("Error decoding JSON data.")
            return None

    def _parse_ticker_json(self, data, count):
        """Parse the ticker JSON to extract the news list."""
        if not data:
            return []
        try:
            store = data['context']['dispatcher']['stores']['StreamStore']
            key = next(k for k in store.get('streams', {}) if k.endswith('_news'))
            items = store['streams'][key]['data']
        except Exception as e:
            print(f"Unexpected JSON structure: {e}")
            return []

        parsed = []
        for it in items[:count]:
            summary = it.get('summary') or (it.get('content') and it['content'][0].get('content')) or ''
            parsed.append({
                'title': it.get('title'),
                'link': it.get('link'),
                'publisher': it.get('publisher', {}).get('name'),
                'providerPublishTime': datetime.fromtimestamp(it.get('providerPublishTime')).isoformat() if it.get('providerPublishTime') else None,
                'summary': summary.strip(),
            })
        return parsed


def main():
    parser = argparse.ArgumentParser(description="Yahoo Finance News Client")
    parser.add_argument('--top', action='store_true', help='Fetch top stories')
    parser.add_argument('--market', action='store_true', help='Fetch market news')
    parser.add_argument('--ticker', type=str, help='Fetch news for a specific stock ticker symbol (e.g., AAPL, GOOGL)')
    parser.add_argument('--count', type=int, default=10, help='Number of items to fetch for ticker news')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--summary-only', action='store_true', help='Print only the summary of each item')
    args = parser.parse_args()

    client = YahooFinanceClient()
    if args.top:
        results = client.get_top_stories()
    elif args.market:
        results = client.get_market_news()
    elif args.ticker:
        results = client.get_ticker_news(args.ticker.upper(), args.count)
    else:
        parser.print_help()
        return

    # Output
    if args.json:
        output = [item.get('summary') for item in results] if args.summary_only else results
        print(json.dumps(output, indent=2))
    else:
        for item in results:
            print(item)
            if args.summary_only:
                print(f"Summary: {item.get('summary')}\n")
            else:
                print(f"Title: {item.get('title')}")
                print(f"Link: {item.get('link')}")
                print(f"Published: {item.get('published') or item.get('providerPublishTime')}")
                print(f"Summary: {item.get('summary')}\n")

if __name__ == '__main__':
    main()
