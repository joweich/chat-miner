import datetime as dt
import json
import logging
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl
from dateutil import parser as datetimeparser
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
)


@dataclass(frozen=True)
class ParsedMessage:
    timestamp: dt.datetime
    author: str
    message: str


class ParsedMessageCollection:
    def __init__(self) -> None:
        self._parsed_messages: List[ParsedMessage] = []

    def append(self, mess: ParsedMessage) -> None:
        self._parsed_messages.append(mess)

    def get_df(self, as_pandas: bool = False) -> Union[pd.DataFrame, pl.DataFrame]:
        messages_as_dict = [asdict(mess) for mess in self._parsed_messages]
        df = pl.DataFrame(messages_as_dict)
        return df.to_pandas() if as_pandas else df

    def write_to_json(self, file: str) -> None:
        def serialize_message(mess: ParsedMessage) -> Dict[str, Any]:
            return {
                "timestamp": mess.timestamp.isoformat(),
                "author": mess.author,
                "message": mess.message,
            }

        with open(file, "w") as json_file:
            json.dump(
                [serialize_message(mess) for mess in self._parsed_messages],
                json_file,
                indent=4,
            )

    def read_from_json(self, file: str) -> None:
        def deserialize_message(mess: Dict[str, Any]) -> ParsedMessage:
            timestamp = dt.datetime.fromisoformat(mess["timestamp"])
            author = mess["author"]
            message = mess["message"]
            return ParsedMessage(timestamp=timestamp, author=author, message=message)

        with open(file, "r") as json_file:
            self._parsed_messages = [
                deserialize_message(mess) for mess in json.load(json_file)
            ]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParsedMessageCollection):
            return NotImplemented
        return self._parsed_messages == other._parsed_messages


class Parser(ABC):
    def __init__(self, filepath: str):
        self._file = Path(filepath)
        assert self._file.is_file()

        self._raw_messages: List[Dict[str, Any]] | List[str] = []
        self.parsed_messages = ParsedMessageCollection()

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            """
            Depending on the platform, the message format in chat logs might not be
            standardized across devices/versions/localization and might change over
            time. Please report issues including your message format via GitHub.
            """
        )
        self._logger.info("Initialized parser.")

    def parse_file(self) -> None:
        self._logger.info("Starting reading raw messages...")
        self._read_raw_messages_from_file()
        self._logger.info("Finished reading %i raw messages.", len(self._raw_messages))

        self._logger.info("Starting parsing raw messages...")
        self._parse_raw_messages()
        self._logger.info("Finished parsing raw messages.")

    @abstractmethod
    def _read_raw_messages_from_file(self) -> None: ...

    def _parse_raw_messages(self) -> None:
        with logging_redirect_tqdm():
            for raw_mess in tqdm(self._raw_messages):
                parsed_mess = self._parse_message(raw_mess)
                if parsed_mess:
                    self.parsed_messages.append(parsed_mess)

    @abstractmethod
    def _parse_message(self, mess: Any) -> Optional[ParsedMessage]: ...


class SignalParser(Parser):
    def _read_raw_messages_from_file(self) -> None:
        def _is_new_message(line: str) -> bool:
            regex = r"^\[\d{4}-\d{2}-\d{2}, \d{2}:\d{2}\]"
            return re.match(regex, line) is not None

        with self._file.open(encoding="utf-8") as f:
            lines = reversed(list(f))

        self._raw_messages: List[str]
        buffer: List[str] = []
        for line in lines:
            if not line:
                continue

            if _is_new_message(line):
                if buffer:
                    buffer.append(line)
                    buffer.reverse()
                    joined_buffer = " ".join(buffer)
                    self._raw_messages.append("".join(joined_buffer.splitlines()))
                    buffer.clear()
                else:
                    self._raw_messages.append(line)
            else:
                buffer.append(line)

    def _parse_message(self, mess: str) -> ParsedMessage:
        datetime_raw, mess = mess.split("]", 1)
        time = datetimeparser.parse(datetime_raw[1:])
        author, body = mess.split(":", 1)
        author = author.strip()
        body = body.strip()
        return ParsedMessage(time, author, body)


class WhatsAppParser(Parser):
    def __init__(self, filepath: str):
        super().__init__(filepath)
        self._datefmt = WhatsAppDateFormat(self._logger)

    def _read_raw_messages_from_file(self) -> None:
        def _is_new_message(line: str) -> bool:
            regex = r"^[\u200e]?\[?(\d{1,4})([./,-])\d{1,2}\2\d{2,4}(?:\s|,\s)(0?\d|1\d|2[0-4]):([0-5]?\d)"
            return re.match(regex, line) is not None

        with self._file.open(encoding="utf-8") as f:
            lines = reversed(list(f))

        self._raw_messages: List[str]
        buffer: List[str] = []
        for line in lines:
            if not line:
                continue

            if _is_new_message(line):
                line = line.replace("\u200e", "")
                line = unicodedata.normalize("NFKC", line.strip())
                if buffer:
                    buffer.append(line)
                    buffer.reverse()
                    joined_buffer = " ".join(buffer)
                    self._raw_messages.append("".join(joined_buffer.splitlines()))
                    buffer.clear()
                else:
                    self._raw_messages.append(line)
            else:
                buffer.append(line)

        self._datefmt.infer_format(self._raw_messages)

    def _parse_message(self, mess: str) -> Optional[ParsedMessage]:
        datestr, author_and_body = mess.split(self._datefmt.date_author_sep, 1)
        time = datetimeparser.parse(
            datestr, dayfirst=self._datefmt.is_dayfirst, fuzzy=True
        )

        if ": " in author_and_body:
            author, body = [x.strip() for x in author_and_body.split(": ", 1)]
            return ParsedMessage(time, author, body)
        elif ":." in author_and_body:
            self._logger.info(f"Ignoring self-destroying message on {time}.")
        else:
            body = author_and_body.strip()
            self._logger.info(f"Ignoring sytem message on {time}: {body}.")
        return None


class FacebookMessengerParser(Parser):
    def _read_raw_messages_from_file(self) -> None:
        with self._file.open(encoding="utf-8") as f:
            self._raw_messages: List[Dict[str, Any]] = json.load(f)["messages"]

    def _parse_message(self, mess: Dict[str, Any]) -> Optional[ParsedMessage]:
        if "content" not in mess:
            return None

        body = mess["content"]

        time = dt.datetime.utcfromtimestamp(mess["timestamp_ms"] / 1000)
        author = mess["sender_name"].encode("latin-1").decode("utf-8")
        body = body.encode("latin-1").decode("utf-8")
        return ParsedMessage(time, author, body)


class InstagramJsonParser(Parser):
    def _read_raw_messages_from_file(self) -> None:
        with self._file.open(encoding="utf-8") as f:
            self._raw_messages: List[Dict[str, Any]] = json.load(f)["messages"]

    def _parse_message(self, mess: Dict[str, Any]) -> Optional[ParsedMessage]:
        if "content" not in mess:
            return None

        system_messages = [
            "to your message",
            "in the poll.",
            "created a poll: ",
            "liked a message",
            "This poll is no longer available.",
            "'s poll has multiple updates.",
        ]

        if any(flag in mess["content"] for flag in system_messages):
            return None

        body = mess["content"]

        time = dt.datetime.utcfromtimestamp(mess["timestamp_ms"] / 1000)
        author = mess["sender_name"].encode("latin-1").decode("utf-8")
        body = body.encode("latin-1").decode("utf-8")
        return ParsedMessage(time, author, body)


class TelegramJsonParser(Parser):
    def __init__(self, filepath: str, chat_name: Optional[str] = None):
        super().__init__(filepath)
        self.chat_name: Optional[str] = chat_name

    def _read_raw_messages_from_file(self) -> None:
        with self._file.open(encoding="utf-8") as f:
            json_objects = json.load(f)

        if "messages" in json_objects:
            self._logger.info("Detected single chat export.")
            self._raw_messages = json_objects["messages"]
        else:
            self._logger.info("Detected batch export.")
            if self.chat_name:
                for chat in json_objects["chats"]["list"]:
                    if "name" in chat and chat["name"] == self.chat_name:
                        self._raw_messages = chat["messages"]
                        break
            else:
                raise ValueError(f"{self.chat_name} not found in {self._file}")

    def _parse_message(self, mess: Dict[str, Any]) -> Optional[ParsedMessage]:
        if "from" not in mess or "text" not in mess:
            return None

        if isinstance(mess["text"], str):
            body = mess["text"]
        elif isinstance(mess["text"], list):
            text_elements = [
                m["text"] if isinstance(m, dict) else m for m in mess["text"]
            ]
            body = " ".join(text_elements)

        time = dt.datetime.utcfromtimestamp(int(mess["date_unixtime"]))
        author = mess["from"]
        return ParsedMessage(time, author, body)


class WhatsAppDateFormat:
    def __init__(self, logger: logging.Logger):
        self.is_dayfirst: Optional[bool] = None
        self.is_yearfirst: Optional[bool] = None
        self.has_brackets: Optional[bool] = None
        self.date_sep: Optional[str] = None
        self.date_author_sep: Optional[str] = None
        self._logger = logger

    def infer_format(self, raw_messages: List[str]) -> None:
        self.has_brackets = self._infer_brackets(raw_messages[0])
        self.date_author_sep = self._infer_date_author_sep()
        self.date_sep = self._infer_date_sep(raw_messages[0])
        self.is_yearfirst = self._infer_yearfirst(raw_messages[0])
        self.is_dayfirst = self._infer_dayfirst(raw_messages)
        self._log_resulting_format()

    @staticmethod
    def _infer_brackets(mess: str) -> bool:
        return mess[0] == "["

    def _infer_date_author_sep(self) -> str:
        return "]" if self.has_brackets else " - "

    def _infer_date_sep(self, mess: str) -> str:
        datestr = mess.split(self.date_author_sep, 1)[0]
        if self.has_brackets:
            datestr = datestr.lstrip("[").rstrip("]")
        for c in datestr:
            if not c.isdigit():
                return c
        raise ValueError("No non-numeric character in datestring.")

    def _infer_yearfirst(self, mess: str) -> bool:
        datestr = mess.split(self.date_author_sep, 1)[0]
        if self.has_brackets:
            datestr = datestr.lstrip("[").rstrip("]")
        return int(datestr.split(self.date_sep)[0]) >= 100

    def _infer_dayfirst(self, raw_messages: List[str]) -> bool:
        max_first = 0
        max_second = 0
        for mess in raw_messages:
            datestr = mess.split(self.date_author_sep, 1)[0]

            if self.has_brackets:
                datestr = datestr.lstrip("[").rstrip("]")

            if self.is_yearfirst:
                datepart = datestr.split(",")[0]
                day_and_month = [int(num) for num in datepart.split(self.date_sep)[1:3]]
            else:
                day_and_month = [int(num) for num in datestr.split(self.date_sep)[:2]]

            max_first = max(max_first, day_and_month[0])
            max_second = max(max_second, day_and_month[1])

            if max_first > 12 or max_second > 12:
                break

        if max_first > 12 >= max_second:
            return True
        if max_first <= 12 < max_second:
            return False
        self._logger.warning(
            "Can't infer date format: No day > 12. Falling back on day first."
        )
        return True

    def _log_resulting_format(self) -> None:
        start = "[" if self.has_brackets else ""
        end = "]" if self.has_brackets else ""
        if self.is_yearfirst:
            date1 = "year"
            date2 = "month"
            date3 = "day"
        elif self.is_dayfirst:
            date1 = "day"
            date2 = "month"
            date3 = "year"
        else:
            date1 = "month"
            date2 = "day"
            date3 = "year"
        composition = f"{start}{date1}{self.date_sep}{date2}{self.date_sep}{date3}{end}"
        self._logger.info("Inferred date format: %s", composition)
