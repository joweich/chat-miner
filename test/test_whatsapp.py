from chatminer.chatparsers import ParsedMessageCollection, WhatsAppParser


def is_equal_to_target(sourcefile):
    targetfile = "test/whatsapp/target.json"
    target = ParsedMessageCollection()
    target.read_from_json(targetfile)
    parser = WhatsAppParser(sourcefile)
    parser.parse_file()
    return parser.parsed_messages == target


def test_mmddyy_24hrs():
    assert is_equal_to_target("test/whatsapp/test_mmddyy_24hrs.txt")


def test_ddmmyy_24hrs():
    assert is_equal_to_target("test/whatsapp/test_ddmmyy_24hrs.txt")


def test_mmddyyyy_12hrs():
    assert is_equal_to_target("test/whatsapp/test_mmddyyyy_12hrs.txt")


def test_yyyymmdd_24hrs():
    assert is_equal_to_target("test/whatsapp/test_yyyymmdd_24hrs.txt")


def test_mmddyy_brackets_24hrs():
    assert is_equal_to_target("test/whatsapp/test_[mmddyy]_24hrs.txt")
