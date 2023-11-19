import pandas as pd
from pandas.testing import assert_frame_equal

from chatminer.chatparsers import SignalParser


def test_signal():
    parser = SignalParser("test/signal/test_export.txt")
    parser.parse_file()
    df_res = parser.parsed_messages.get_df()
    df_test = pd.read_csv(
        "test/signal/test_target.csv",
        parse_dates=["timestamp"],
    )
    assert_frame_equal(df_test, df_res, check_dtype=False)
