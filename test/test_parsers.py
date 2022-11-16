import pandas as pd
from chatminer.chatparsers import WhatsAppParser, FacebookMessengerParser
import datetime


def test_whatsapp():
    parser = WhatsAppParser("test/whatsapp/testlog.txt")
    parser.parse_file_into_df()
    df_test = pd.read_json("test/whatsapp/target.json", orient="records", lines=True)
    for (_, row_res), (_, row_target) in zip(parser.df.iterrows(), df_test.iterrows()):
        assert row_res.equals(row_target), row_res.compare(
            row_target, result_names=("result", "target")
        )


def test_facebookMessenger():
    parser = FacebookMessengerParser("test/facebookMessenger/testlog.json")
    parser.parse_file_into_df()
    # set convert_dates to false since if set to true, the conversion will use UTC 0 instead of using the users local timezone
    df_test = pd.read_json(
        "test/facebookMessenger/target.json", orient="records", convert_dates=False
    )
    adjustUtcTimestamp(df_test)
    for (_, row_res), (_, row_target) in zip(parser.df.iterrows(), df_test.iterrows()):
        assert row_res.equals(row_target), row_res.compare(
            row_target, result_names=("result", "target")
        )


def adjustUtcTimestamp(df: pd.DataFrame):
    for index in df.index:
        # Convert timestamp to datetime format with the local timezone
        df.at[index, "datetime"] = datetime.datetime.fromtimestamp(
            df.at[index, "datetime"] / 1000
        )
        # Adjust the hour by the UTC hour difference. i.e. If hour is 15 and the timezone is UTC-6, then hour will be 9
        df.at[index, "hour"] = df.at[index, "hour"] + (
            round(
                (
                    round(
                        (
                            datetime.datetime.now() - datetime.datetime.utcnow()
                        ).total_seconds()
                    )
                    / 1800
                )
                / 2
            )
        )
