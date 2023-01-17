from transformers import pipeline
import pandas as pd


def add_sentiment(df: pd.DataFrame, lang: str = "en") -> pd.DataFrame:
    model_path = (
        "cardiffnlp/twitter-roberta-base-sentiment-latest"
        if lang == "en"
        else "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    )

    sentiment_pipeline = pipeline("sentiment-analysis", model=model_path)
    df["sentiment"] = [
        sentiment["label"] for sentiment in sentiment_pipeline(list(df["message"]))
    ]
    return df
