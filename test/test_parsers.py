import pandas as pd
from pandas.testing import assert_frame_equal

from chatminer.chatparsers import InstagramJsonParser, WhatsAppParser


def test_whatsapp():
    def assert_equal_from_file(file):
        parser = WhatsAppParser(f"test/whatsapp/test_{file}.txt")
        parser.parse_file()
        df_res = parser.parsed_messages.get_df()
        df_test = pd.read_csv(
            f"test/whatsapp/test_{file}_target.csv",
            parse_dates=["timestamp"],
            infer_datetime_format=True,
        )
        assert_frame_equal(df_test, df_res)

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

    test_dateformat1()
    test_dateformat2()
    test_dateformat3()
    test_dateformat4()
    test_dateformat5()
    test_unicode()


def test_instagram():
    parser = InstagramJsonParser("test/instagram/testlog.json")
    parser.parse_file()
    df_res = parser.parsed_messages.get_df()
    df_test = pd.read_csv(
        "test/instagram/testlog_target.csv",
        parse_dates=["timestamp"],
        infer_datetime_format=True,
    )
    assert_frame_equal(
        df_test[["author", "message", "words", "letters"]],
        df_res[["author", "message", "words", "letters"]],
    )
