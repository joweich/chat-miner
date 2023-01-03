import pandas as pd
from chatminer.chatparsers import WhatsAppParser


def test_whatsapp():
    parser = WhatsAppParser("test/whatsapp/testlog.txt")
    parser.parse_file_into_df()
    df_test = pd.read_json("test/whatsapp/target.json", orient="records", lines=True)
    for (_, row_res), (_, row_target) in zip(parser.df.iterrows(), df_test.iterrows()):
        assert row_res.equals(row_target), row_res.compare(
            row_target, result_names=("result", "target")
        )
