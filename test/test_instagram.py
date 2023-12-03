from chatminer.chatparsers import InstagramJsonParser, ParsedMessageCollection


def test_instagram():
    target = ParsedMessageCollection()
    target.read_from_json("test/instagram/target.json")
    parser = InstagramJsonParser("test/instagram/test_export.json")
    parser.parse_file()
    assert parser.parsed_messages == target
