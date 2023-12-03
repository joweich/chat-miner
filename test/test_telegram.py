from chatminer.chatparsers import ParsedMessageCollection, TelegramJsonParser


def test_telegram_single_export():
    target = ParsedMessageCollection()
    target.read_from_json("test/telegram/target.json")
    parser = TelegramJsonParser("test/telegram/test_single_export.json")
    parser.parse_file()
    assert parser.parsed_messages == target


def test_telegram_batch_export():
    target = ParsedMessageCollection()
    target.read_from_json("test/telegram/target.json")
    parser = TelegramJsonParser("test/telegram/test_batch_export.json", "Chatname")
    parser.parse_file()
    assert parser.parsed_messages == target
