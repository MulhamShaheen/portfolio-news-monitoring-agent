from pydantic import BaseModel
from typing import List

class SummarizedNewsItem(BaseModel):
    title: str
    summary: str
    url: str

class SummarizedNewsResponse(BaseModel):
    ticker: str
    summaries: List[SummarizedNewsItem]

class NewsItem(BaseModel):
    title: str
    link: str
    summary: str

class NewsResponse(BaseModel):
    ticker: str
    news: List[NewsItem]

class TickerInput(BaseModel):
    symbol: str
    description: str

class RelevantTickersRequest(BaseModel):
    query: str
    top_k: int = 3

class RelevantTickersResponse(BaseModel):
    symbols: List[str]

class SummarizeRelevantNewsRequest(BaseModel):
    query: str
    top_k: int = 3
    max_articles: int = 5


class TickerNewsSummary(BaseModel):
    ticker: str
    summaries: list[SummarizedNewsItem]


class SummarizeRelevantNewsResponse(BaseModel):
    message: str
    results: list[TickerNewsSummary]
