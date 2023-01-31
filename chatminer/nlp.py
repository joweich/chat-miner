import pandas as pd
from transformers import pipeline


def add_sentiment(df: pd.DataFrame, lang: str = "en") -> pd.DataFrame:
    """
    Add sentiment column to the input dataframe

    Parameters:
    df (pd.DataFrame): The input dataframe
    lang (str): Language of the messages, defaults to "en"

    Returns:
    pd.DataFrame: The input dataframe with an additional column "sentiment"

    """
    if "message" not in df.columns:
        raise ValueError("Input dataframe does not contain a 'message' column")

    model_path = (
        "cardiffnlp/twitter-roberta-base-sentiment-latest"
        if lang == "en"
        else "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    )
    sentiment_pipeline = pipeline("sentiment-analysis", model=model_path)

    def extract_sentiment(message: str) -> str:
        """
        Extract sentiment from message

        Parameters:
        message (str): The input message

        Returns:
        str: The sentiment of the message

        """
        try:
            return sentiment_pipeline(message)[0]["label"]
        except:
            print(f"Error processing message: {message}")
            return None

    df["sentiment"] = df["message"].apply(extract_sentiment)

    return df
