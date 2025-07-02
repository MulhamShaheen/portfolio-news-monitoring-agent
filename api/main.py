from fastapi import FastAPI, Query, HTTPException
from models.schemas import SummarizedNewsResponse, SummarizedNewsItem, NewsResponse
from services.news_fetcher import fetcher as news_fetcher
from services.summarizer import Summarizer

app = FastAPI()

@app.get("/summarize-news", response_model=SummarizedNewsResponse)
def summarize_news(ticker: str = Query(..., description="Ticker symbol (e.g., AAPL)"), max_articles: int = 5):
    summarizer = Summarizer()
    try:
        news_items = news_fetcher.get_ticker_news(ticker, count=max_articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {e}")
    if not news_items:
        raise HTTPException(status_code=404, detail="No news found for ticker.")
    summaries = []
    for item in news_items:
        text = item.get('summary') or item.get('title') or ''
        if not text:
            continue
        summary = summarizer.summarize(text)
        summaries.append(SummarizedNewsItem(
            title=item.get('title', ''),
            summary=summary,
            url=item.get('link', '')
        ))
    return SummarizedNewsResponse(ticker=ticker, summaries=summaries)

@app.get("/news", response_model=NewsResponse)
def get_news(ticker: str = Query(..., description="Ticker symbol (e.g., AAPL)"), max_articles: int = 5):
    try:
        news = news_fetcher.get_ticker_news(ticker, count=max_articles)
        return {"ticker": ticker, "news": news}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
