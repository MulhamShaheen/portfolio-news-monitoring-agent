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
