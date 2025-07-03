from fastapi import FastAPI, Query, HTTPException, Body

from database.dummy_tickers import TICKERS_DB
from models.schemas import *
from services.news_fetcher import fetcher as news_fetcher
from services.summarizer import summarizer
from services.chat import mistral_client

app = FastAPI()


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


@app.get("/relevant-tickers", response_model=RelevantTickersResponse)
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


@app.post("/summarize-relevant-news", response_model=SummarizeRelevantNewsResponse)
def summarize_relevant_news(request: SummarizeRelevantNewsRequest = Body(...)):
    try:
        symbols = mistral_client.pick_relevant_tickers(
            query=request.query,
            tickers=TICKERS_DB,
            top_k=request.top_k
        )
        results = []
        for symbol in symbols:
            news_items = news_fetcher.get_ticker_news(symbol, count=request.max_articles)
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
            results.append(TickerNewsSummary(ticker=symbol, summaries=summaries))

        txt_summaries = [summary.summary for ticker_summary in results for summary in ticker_summary.summaries]
        message = mistral_client.generate(
            prompt=f"Summaries: {', '.join(txt_summaries)}",
            sys_prompt="You will be given a list of stock news summaries. "
                       "Introduce this summaries with a brief overview of them.",
            max_tokens=200,
            temperature=0.7
        )
        return SummarizeRelevantNewsResponse(results=results, message=message[0] if message else "No summaries generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize relevant news: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
