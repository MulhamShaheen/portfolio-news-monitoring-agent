import os
from typing import Any, Dict, List, Optional
from mistralai import Mistral

from api.config import MISTRAL_API_KEY, MISTRAL_MODEL


class MistralClient:
    """
    Client for interacting with the Mistral API using the mistralai package.

    Usage:
        client = MistralClient(api_key="YOUR_API_KEY")
        response = client.generate(
            model="mistral-7b",
            prompt="Hello, world!",
            max_tokens=50,
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-small-2506",
    ):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided via constructor or MISTRAL_API_KEY env var.")
        self.model = model
        self.client = Mistral(api_key=self.api_key)

    def generate(
        self,
        model: str,
        prompt: str,
        sys_prompt: Optional[str] = None,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        n: int = 1,
        **kwargs,
    ) -> List[str]:
        """
        Generate completions from the specified model.
        """
        # mistralai expects a list of prompts for batch generation
        params = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
        }
        if sys_prompt:
            params["messages"].insert(0, {"role": "system", "content": sys_prompt})

        params.update(kwargs)
        result = self.client.chat.complete(**params)
        return [choice.message.content for choice in result.choices]


    def pick_relevant_tickers(
        self,
        query: str,
        tickers: List[Dict[str, str]],
        top_k: int = 3,
        model: Optional[str] = None,
    ) -> List[str]:
        """
        Pick the most relevant tickers based on the query and ticker descriptions.

        Args:
            query: The user query (e.g., "Find me news of the stock of AI related companies")
            tickers: List of dicts with keys 'symbol' and 'description'
            top_k: Number of most relevant tickers to return
            model: Optional override for the model to use

        Returns:
            List of ticker symbols (str) that are most relevant to the query
        """
        model = model or self.model
        # Prepare the context for the LLM
        tickers_text = "\n".join(
            [f"{i+1}. {t['symbol']}: {t['description']}" for i, t in enumerate(tickers)]
        )
        sys_prompt = ("You are an expert stock analyst. "
                      "Given a list of stock tickers and their descriptions:\n"
                      f"{tickers_text}\n\n"
                      "You should pick the most relevant ticker symbols based on the user's query. "
                      f"From the list above, pick the {top_k} most relevant ticker symbols (by symbol only)"
                      "Return only a comma-separated list of symbols.")
        prompt = (
            f"User query: \"{query}\"\n"
        )
        completions = self.generate(
            model=model,
            prompt=prompt,
            sys_prompt=sys_prompt,
            max_tokens=32,
            temperature=0.2,
        )
        # Parse the output: expect a comma-separated list of symbols
        if completions:
            symbols = [s.strip().upper() for s in completions[0].split(",") if s.strip()]
            # Filter to only those in the original list
            valid_symbols = {t['symbol'].upper() for t in tickers}
            return [s for s in symbols if s in valid_symbols][:top_k]
        return []

    def __repr__(self) -> str:
        return f"<MistralClient model={self.model}>"


mistral_client = MistralClient(api_key=MISTRAL_API_KEY, model=MISTRAL_MODEL)
