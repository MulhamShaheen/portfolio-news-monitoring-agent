# QuadCode News Summarization Service

This service provides APIs for fetching, analyzing, and summarizing financial news for stock tickers, leveraging Yahoo Finance, Mistral LLM, and transformer-based summarization models.

## Components

### 1. API (`api/main.py`)
- **FastAPI**-based REST API exposing endpoints for:
  - Fetching news for a ticker (`/news`)
  - Summarizing news for a ticker (`/summarize-news`)
  - Finding relevant tickers for a query (`/relevant-tickers`)
  - Summarizing news for the most relevant tickers (`/summarize-relevant-news`)
- Uses Pydantic models for request/response validation (`models/schemas.py`).

### 2. YahooFinanceClient (`services/news_fetcher.py`)
- Fetches news articles for a given ticker from Yahoo Finance RSS feeds.
- Optionally fetches and parses the main content of news articles from their HTML pages.
- Handles retries and backoff for rate-limited requests.

### 3. Summarizer (`services/summarizer.py`)
- Uses HuggingFace Transformers (`AutoModelForSeq2SeqLM` and `AutoTokenizer`) for abstractive summarization.
- Loads a fine-tuned model for financial news summarization.

### 4. MistralClient (`services/chat.py`)
- Integrates with the Mistral LLM API via the `mistralai` package.
- Used for:
  - Selecting the most relevant tickers for a user query based on ticker descriptions.
  - Generating high-level summaries or introductions for sets of news summaries.

### 5. Configuration (`api/config.py`)
- Loads environment variables (API keys, model names) using `python-dotenv`.

### 6. Data Models (`models/schemas.py`)
- Defines Pydantic models for news items, summaries, ticker selection, and API responses.

### 7. Notebooks
- `notebooks/model_training.ipynb`: Shows model training and evaluation for summarization.
- `notebooks/news_parsing.ipynb`: Demonstrates news parsing and dataset creation.

### 8. Docker Support
- `Dockerfile` for containerized deployment.

## Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-small-2506
```

## Running the Service

1. Install dependencies (preferably in a virtual environment):

   ```
   pip install -r requirements.txt
   ```

2. Start the API:

   ```
   uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## Using docker compose

1. Ensure Docker and Docker Compose are installed.
2. Run the following command to start the service:

   ```
   docker-compose up --build
   ```

## Example Usage

- **Summarize news for a ticker:**
  ```
  GET /summarize-news?ticker=AAPL&max_articles=5
  ```
- **Get relevant tickers for a query:**
  ```
  GET /relevant-tickers?query=AI companies&top_k=3
  ```
- **Summarize news for relevant tickers:**
  ```
  POST /summarize-relevant-news
  {
    "query": "Find me news of the stock of AI related companies",
    "top_k": 3,
    "max_articles": 5
  }
  ```

## Notes

- The service is designed for extensibility and can be adapted to other news sources or LLM providers.
- For production, ensure API keys are kept secure and rate limits are respected.


