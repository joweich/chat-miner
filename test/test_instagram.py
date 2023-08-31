import pandas as pd
from pandas.testing import assert_frame_equal

from chatminer.chatparsers import InstagramJsonParser


def test_instagram():
    parser = InstagramJsonParser("test/instagram/testlog.json")
    parser.parse_file()
    df_res = parser.parsed_messages.get_df()
    df_test = pd.read_csv(
        "test/instagram/testlog_target.csv",
        parse_dates=["timestamp"],
    )
    assert_frame_equal(
        df_test[["author", "message", "words", "letters"]],
        df_res[["author", "message", "words", "letters"]],
    )
