"""
Tests for forensic export functionality.
"""

from chatminer.exporters.forensic import export_forensic_evidence


def test_forensic_export_structure():
    """Verify export includes metadata, messages, and integrity sections."""
    messages = [
        {
            "timestamp": "2026-01-01T10:00:00Z",
            "sender": "Alice",
            "text": "Hello",
            "attachments": [],
        }
    ]

    export = export_forensic_evidence(
        messages,
        source_file="chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
        exported_by="tester",
    )

    assert "metadata" in export
    assert "messages" in export
    assert "integrity" in export


def test_forensic_export_metadata():
    """Verify metadata fields are correctly populated."""
    messages = [
        {
            "timestamp": "2026-01-01T10:00:00Z",
            "sender": "Alice",
            "text": "Test",
            "attachments": [],
        }
    ]

    export = export_forensic_evidence(
        messages,
        source_file="test_chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
        exported_by="analyst",
    )

    metadata = export["metadata"]

    assert metadata["source_file"] == "test_chat.txt"
    assert metadata["parser"]["name"] == "chat-miner"
    assert metadata["parser"]["version"] == "0.6.3"
    assert metadata["exported_by"] == "analyst"
    assert metadata["record_count"] == 1
    assert metadata["content_hash"].startswith("sha256:")


def test_forensic_export_messages_untouched():
    """Verify messages are included without modification."""
    messages = [
        {
            "timestamp": "2026-01-01T10:00:00Z",
            "sender": "Alice",
            "text": "Hello",
            "attachments": [],
        }
    ]

    export = export_forensic_evidence(
        messages,
        source_file="chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
    )

    assert export["messages"] == messages
    assert export["messages"][0]["text"] == "Hello"


def test_hash_is_deterministic():
    """Verify message hash is independent of metadata and consistent across exports."""
    messages = [
        {"timestamp": "t", "sender": "s", "text": "x", "attachments": []}
    ]

    # Same messages, different metadata
    a = export_forensic_evidence(
        messages,
        source_file="a.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
        exported_by="user1",
    )
    b = export_forensic_evidence(
        messages,
        source_file="b.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
        exported_by="user2",
    )

    # Hash must be identical (messages untouched, metadata excluded)
    assert a["metadata"]["content_hash"] == b["metadata"]["content_hash"]


def test_hash_changes_with_message_content():
    """Verify hash changes when message content differs."""
    messages_a = [
        {"timestamp": "t", "sender": "s", "text": "x", "attachments": []}
    ]
    messages_b = [
        {"timestamp": "t", "sender": "s", "text": "y", "attachments": []}
    ]

    export_a = export_forensic_evidence(
        messages_a,
        source_file="chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
    )
    export_b = export_forensic_evidence(
        messages_b,
        source_file="chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
    )

    assert export_a["metadata"]["content_hash"] != export_b["metadata"]["content_hash"]


def test_exported_by_optional():
    """Verify exported_by is optional."""
    messages = [
        {
            "timestamp": "2026-01-01T10:00:00Z",
            "sender": "Alice",
            "text": "Hello",
            "attachments": [],
        }
    ]

    export = export_forensic_evidence(
        messages,
        source_file="chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
    )

    assert export["metadata"]["exported_by"] is None


def test_empty_messages():
    """Verify handling of empty message list."""
    messages = []

    export = export_forensic_evidence(
        messages,
        source_file="empty.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
    )

    assert export["metadata"]["record_count"] == 0
    assert export["messages"] == []


def test_integrity_verified_field():
    """Verify integrity section includes verified flag."""
    messages = [
        {
            "timestamp": "2026-01-01T10:00:00Z",
            "sender": "Alice",
            "text": "Test",
            "attachments": [],
        }
    ]

    export = export_forensic_evidence(
        messages,
        source_file="chat.txt",
        parser_name="chat-miner",
        parser_version="0.6.3",
    )

    integrity = export["integrity"]
    assert integrity["hash_algorithm"] == "sha256"
    assert integrity["hash_scope"] == "messages_only"
    assert integrity["verified"] is True
