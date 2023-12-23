from typing import Optional

import polars as pl
from transformers import pipeline


def add_sentiment(df: pl.DataFrame, lang: str = "en") -> pl.DataFrame:
    """
    Add sentiment column to the input dataframe

    Parameters:
    df (pl.DataFrame): The input dataframe
    lang (str): Language of the messages, defaults to "en"

    Returns:
    pl.DataFrame: The input dataframe with an additional column "sentiment"

    """
    if "message" not in df.columns:
        raise ValueError("Input dataframe does not contain a 'message' column")

    model_path = (
        "cardiffnlp/twitter-roberta-base-sentiment-latest"
        if lang == "en"
        else "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    )
    sentiment_pipeline = pipeline("sentiment-analysis", model=model_path)

    def extract_sentiment(message: str) -> Optional[str]:
        """
        Extract sentiment from message

        Parameters:
        message (str): The input message

        Returns:
        str: The sentiment of the message

        """
        try:
            return sentiment_pipeline(message)[0]["label"]
        except Exception as e:
            print(f"Error processing message: {message}: {e}")
            return None

    df = df.with_columns(
        (pl.col("message")).map_elements(extract_sentiment).alias("sentiment"),
    )
    return df
