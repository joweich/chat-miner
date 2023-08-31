import pandas as pd
from pandas.testing import assert_frame_equal

from chatminer.chatparsers import WhatsAppParser


def assert_equal_from_file(file):
    parser = WhatsAppParser(f"test/whatsapp/test_{file}.txt")
    parser.parse_file()
    df_res = parser.parsed_messages.get_df()
    df_test = pd.read_csv(
        f"test/whatsapp/test_{file}_target.csv",
        parse_dates=["timestamp"],
    )
    assert_frame_equal(df_test, df_res, check_dtype=False)


def test_dateformat1():
    assert_equal_from_file("dateformat1")


def test_dateformat2():
    assert_equal_from_file("dateformat2")


def test_dateformat3():
    assert_equal_from_file("dateformat3")


def test_dateformat4():
    assert_equal_from_file("dateformat4")


def test_dateformat5():
    assert_equal_from_file("dateformat5")


def test_unicode():
    assert_equal_from_file("unicode")
