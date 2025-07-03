import os

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class Summarizer:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join('checkpoints', 'bert-small-finetuned-cnn')

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


        self.tokenizer = AutoTokenizer.from_pretrained(model_path, truncation=True, max_length=512)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(self.device)
        self.model.eval()

    def summarize(self, text: str, max_length: int = 512, min_length: int = 10) -> str:
        try:
            inputs = self.tokenizer([text], return_tensors="pt", truncation=True, max_length=max_length, padding="max_length")
            with torch.no_grad():
                summary_ids = self.model.generate(
                    inputs["input_ids"].to(self.device),
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
            return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        except Exception as e:
            print(f'Something went wrong: {e}')
            return text[:max_length] + '...'

summarizer = Summarizer()
