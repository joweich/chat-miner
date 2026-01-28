"""
Forensic export wrapper for parsed chat messages.

Provides deterministic, chain-of-custody metadata suitable for
audit and evidence workflows.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _hash_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Compute deterministic hash over message content only.
    
    Hash excludes metadata to ensure stability across re-exports
    with different timestamps or operators.
    
    Args:
        messages: List of parsed message dictionaries.
        
    Returns:
        Hex-encoded SHA256 hash of sorted JSON representation.
    """
    payload = json.dumps(
        messages,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def export_forensic_evidence(
    messages: List[Dict[str, Any]],
    *,
    source_file: str,
    parser_name: str,
    parser_version: str,
    exported_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export parsed chat messages with forensic chain-of-custody metadata.

    This function does NOT:
    - filter messages
    - interpret content
    - assign relevance

    It only wraps parsed output for audit and evidence workflows.

    Args:
        messages: List of parsed message dictionaries from a chat parser.
        source_file: Original source file name (e.g., 'whatsapp_chat.txt').
        parser_name: Name of the chat parser (e.g., 'chat-miner').
        parser_version: Version of the chat parser (e.g., '0.6.3').
        exported_by: Optional identifier of the operator/system exporting.

    Returns:
        Dictionary with metadata, messages, and integrity information.

    Example:
        >>> from chatminer.chatparsers import SignalParser
        >>> parser = SignalParser('signal_export.txt')
        >>> parser.parse_file()
        >>> export = export_forensic_evidence(
        ...     parser.parsed_messages.to_list(),
        ...     source_file='signal_export.txt',
        ...     parser_name='chat-miner',
        ...     parser_version='0.6.3',
        ...     exported_by='analyst@agency.gov'
        ... )
    """
    content_hash = _hash_messages(messages)

    return {
        "metadata": {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_file": source_file,
            "parser": {
                "name": parser_name,
                "version": parser_version,
            },
            "exported_by": exported_by,
            "record_count": len(messages),
            "content_hash": f"sha256:{content_hash}",
        },
        "messages": messages,
        "integrity": {
            "hash_algorithm": "sha256",
            "hash_scope": "messages_only",
            "verified": True,
        },
    }
