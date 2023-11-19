import pandas as pd
from pandas.testing import assert_frame_equal

from chatminer.chatparsers import TelegramJsonParser


def test_telegram_single_export():
    parser = TelegramJsonParser("test/telegram/test_single_export.json")
    parser.parse_file()
    df_res = parser.parsed_messages.get_df()
    df_test = pd.read_csv(
        "test/telegram/test_target.csv",
        parse_dates=["timestamp"],
    )
    assert_frame_equal(
        df_test[["author", "message", "words", "letters"]],
        df_res[["author", "message", "words", "letters"]],
    )


def test_telegram_batch_export():
    parser = TelegramJsonParser("test/telegram/test_batch_export.json", "Chatname")
    parser.parse_file()
    df_res = parser.parsed_messages.get_df()
    df_test = pd.read_csv(
        "test/telegram/test_target.csv",
        parse_dates=["timestamp"],
    )
    assert_frame_equal(
        df_test[["author", "message", "words", "letters"]],
        df_res[["author", "message", "words", "letters"]],
    )
