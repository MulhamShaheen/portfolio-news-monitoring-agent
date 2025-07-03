from fastapi import FastAPI, Query, HTTPException
from models.schemas import SummarizedNewsResponse, SummarizedNewsItem, NewsResponse, RelevantTickersRequest, \
    RelevantTickersResponse
from services.news_fetcher import fetcher as news_fetcher
from services.summarizer import summarizer
from services.chat import mistral_client

app = FastAPI()

# Hardcoded example tickers and discriptions
TICKERS_DB = [
    {"symbol": "AAPL",
     "description": "Apple Inc. designs, manufactures, and markets consumer electronics, software, and services."},
    {"symbol": "GOOGL",
     "description": "Alphabet Inc. is a multinational conglomerate specializing in internet-related services and products."},
    {"symbol": "MSFT",
     "description": "Microsoft Corporation develops, licenses, and supports a wide range of software products and services."},
    {"symbol": "AMZN",
     "description": "Amazon.com, Inc. is a global e‑commerce and cloud computing giant, also involved in digital streaming and AI."},
    {"symbol": "JPM",
     "description": "JPMorgan Chase & Co. provides financial services including investment banking, asset management, and consumer banking."},
    {"symbol": "XOM",
     "description": "Exxon Mobil Corporation explores for, produces, and distributes crude oil, natural gas, and petroleum products."},
    {"symbol": "PFE",
     "description": "Pfizer Inc. discovers, develops, and manufactures healthcare products, including vaccines and specialty medicines."},
    {"symbol": "TSLA",
     "description": "Tesla, Inc. designs, manufactures, and sells electric vehicles, energy storage systems, and solar products."},
    {"symbol": "KO",
     "description": "The Coca‑Cola Company produces, markets, and sells nonalcoholic beverage concentrates and syrups worldwide."},
    {"symbol": "BA",
     "description": "The Boeing Company designs, manufactures, and services commercial jetliners, defense, space, and security systems."},
    {"symbol": "NFLX",
     "description": "Netflix, Inc. provides subscription streaming entertainment services and produces original films and series."},
    {"symbol": "NVDA",
     "description": "NVIDIA Corporation designs graphics processing units (GPUs) and AI computing technology for gaming, professional visualization, and data centers."},
    {"symbol": "DIS",
     "description": "The Walt Disney Company operates media networks, parks and resorts, studio entertainment, and direct‑to‑consumer streaming services."},
]


@app.get("/summarize-news", response_model=SummarizedNewsResponse)
def summarize_news(ticker: str = Query(..., description="Ticker symbol (e.g., AAPL)"), max_articles: int = 5):
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


@app.post("/relevant-tickers", response_model=RelevantTickersResponse)
def relevant_tickers(request: RelevantTickersRequest):
    try:
        symbols = mistral_client.pick_relevant_tickers(
            query=request.query,
            tickers=TICKERS_DB,
            top_k=request.top_k
        )
        return RelevantTickersResponse(symbols=symbols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pick relevant tickers: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
