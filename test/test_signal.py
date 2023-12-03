from chatminer.chatparsers import ParsedMessageCollection, SignalParser


def test_signal():
    target = ParsedMessageCollection()
    target.read_from_json("test/signal/target.json")
    parser = SignalParser("test/signal/test_export.txt")
    parser.parse_file()
    assert parser.parsed_messages == target
