import datetime
import json
import logging
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
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
    timestamp: datetime
    author: str
    message: str


class ParsedMessageCollection:
    def __init__(self):
        self._parsed_messages = []

    def append(self, mess):
        assert isinstance(mess, ParsedMessage)
        self._parsed_messages.append(mess)

    def get_df(self):
        messages_as_dict = []
        for mess in self._parsed_messages:
            messages_as_dict.append(asdict(mess))

        df = pd.DataFrame(messages_as_dict)
        df["weekday"] = df["timestamp"].dt.day_name()
        df["hour"] = df["timestamp"].dt.hour
        df["words"] = df["message"].apply(lambda s: len(s.split(" ")))
        df["letters"] = df["message"].apply(len)
        return df


class Parser(ABC):
    def __init__(self, filepath):
        self._file = Path(filepath)
        assert self._file.is_file()

        self._raw_messages = []
        self.parsed_messages = ParsedMessageCollection()

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            """
            Depending on the platform, the message format in chat logs might not be
            standardized accross devices/versions/localization and might change over
            time. Please report issues including your message format via GitHub.
            """
        )
        self._logger.info("Initialized parser.")

    def parse_file(self):
        self._logger.info("Starting reading raw messages...")
        self._read_raw_messages_from_file()
        self._logger.info("Finished reading %i raw messages.", len(self._raw_messages))

        self._logger.info("Starting parsing raw messages...")
        self._parse_raw_messages()
        self._logger.info("Finished parsing raw messages.")

    @abstractmethod
    def _read_raw_messages_from_file(self):
        return

    def _parse_raw_messages(self):
        with logging_redirect_tqdm():
            for raw_mess in tqdm(self._raw_messages):
                parsed_mess = self._parse_message(raw_mess)
                if parsed_mess:
                    self.parsed_messages.append(parsed_mess)

    @abstractmethod
    def _parse_message(self, mess):
        return


class SignalParser(Parser):
    def _read_raw_messages_from_file(self):
        def _is_new_message(line):
            regex = r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\]"
            return re.match(regex, line)

        with self._file.open(encoding="utf-8") as f:
            lines = reversed(list(f))

        buffer = []
        for line in lines:
            if not line:
                continue

            if _is_new_message(line):
                if buffer:
                    buffer.append(line)
                    buffer.reverse()
                    self._raw_messages.append(" ".join(buffer))
                    buffer.clear()
                else:
                    self._raw_messages.append(line)
            else:
                buffer.append(line)

    def _parse_message(self, mess):
        datetime_raw, mess = mess.split("]", 1)
        time = datetimeparser.parse(datetime_raw[1:])
        author, body = mess.split(":", 1)
        author = author.strip()
        body = body.strip()
        return ParsedMessage(time, author, body)


class WhatsAppParser(Parser):
    def __init__(self, filepath):
        super().__init__(filepath)
        self._datefmt = WhatsAppDateFormat(self._logger)

    def _read_raw_messages_from_file(self):
        def _is_new_message(line):
            regex = r"^[\u200e]?\[?((\d{1})|(\d{2})|(\d{4}))((\.)|(\/)|(\-))((\d{1})|(\d{2}))((\.)|(\/)|(\-))((\d{4})|(\d{2}))((\,)|(\ ))"
            return re.match(regex, line)

        with self._file.open(encoding="utf-8") as f:
            lines = reversed(list(f))

        buffer = []
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

    def _parse_message(self, mess):
        datestr, author_and_body = mess.split(self._datefmt.date_author_sep, 1)
        time = datetimeparser.parse(
            datestr, dayfirst=self._datefmt.is_dayfirst, fuzzy=True
        )

        if ":" in author_and_body:
            author, body = [x.strip() for x in author_and_body.split(": ", 1)]
        else:
            author = "System"
            body = author_and_body.strip()
        return ParsedMessage(time, author, body)


class FacebookMessengerParser(Parser):
    def _read_raw_messages_from_file(self):
        with self._file.open(encoding="utf-8") as f:
            self._raw_messages = json.load(f)["messages"]

    def _parse_message(self, mess):
        if "type" in mess and mess["type"] == "Share":
            body = mess["share"]["link"]
        elif "sticker" in mess:
            body = mess["sticker"]["uri"]
        elif "content" in mess:
            body = mess["content"]
        else:
            self._logger.warning("Skipped message with unknown format: %s", mess)
            return None

        time = datetime.datetime.fromtimestamp(mess["timestamp_ms"] / 1000)
        author = mess["sender_name"].encode("latin-1").decode("utf-8")
        body = body.encode("latin-1").decode("utf-8")
        return ParsedMessage(time, author, body)


class InstagramJsonParser(Parser):
    def _read_raw_messages_from_file(self):
        with self._file.open(encoding="utf-8") as f:
            self._raw_messages = json.load(f)["messages"]

    def _parse_message(self, mess):
        if "share" in mess:
            body = "sentshare"
        elif "photos" in mess:
            body = "sentphoto"
        elif "videos" in mess:
            body = "sentvideo"
        elif "audio_files" in mess:
            body = "sentaudio"
        elif "content" in mess:
            if any(
                flag in mess["content"]
                for flag in (
                    " to your message",
                    " in the poll.",
                    " created a poll: ",
                    " liked a message",
                    "This poll is no longer available.",
                    "'s poll has multiple updates.",
                )
            ):
                return None
            body = mess["content"]
        elif all(key in ("sender_name", "timestamp_ms", "reactions") for key in mess):
            body = "disappearingmessage"
        else:
            self._logger.warning("Skipped message with unknown format: %s", mess)
            return None

        time = datetime.datetime.fromtimestamp(mess["timestamp_ms"] / 1000)
        author = mess["sender_name"].encode("latin-1").decode("utf-8")
        body = body.encode("latin-1").decode("utf-8")
        return ParsedMessage(time, author, body)


class TelegramJsonParser(Parser):
    def __init__(self, filepath, chat_name=None):
        super().__init__(filepath)
        self.chat_name = chat_name

    def _read_raw_messages_from_file(self):
        with self._file.open(encoding="utf-8") as f:
            json_objects = json.load(f)

        if "messages" in json_objects:
            self._raw_messages = json_objects["messages"]
        else:
            if self.chat_name:
                self._logger.info("Searching for chat %s...", self.chat_name)
                for chat in json_objects["chats"]["list"]:
                    if "name" in chat and chat["name"] == self.chat_name:
                        self._raw_messages = chat["messages"]
                        break
            else:
                self._logger.info(
                    'No chat name was specified, searching for chat "Saved Messages"...'
                )
                for chat in json_objects["chats"]["list"]:
                    if chat["type"] == "saved_messages":
                        self._raw_messages = chat["messages"]
                        break
        if not self._raw_messages:
            self._logger.error(
                "Chat %s was not found.",
                self.chat_name if self.chat_name else "Saved Messages",
            )

    def _parse_message(self, mess):
        if "from" in mess and "text" in mess:
            if isinstance(mess["text"], str):
                body = mess["text"]
            elif isinstance(mess["text"], list):
                assert all(
                    [
                        (isinstance(m, dict) and "text" in m) or isinstance(m, str)
                        for m in mess["text"]
                    ]
                )
                body = " ".join(
                    map(
                        lambda m: m["text"] if isinstance(m, dict) else m,
                        mess["text"],
                    )
                )
            else:
                raise ValueError(f"Unable to parse type {type(mess['text'])} in {mess}")

            time = datetime.datetime.fromtimestamp(int(mess["date_unixtime"]))
            author = mess["from"]
            return ParsedMessage(time, author, body)
        return False


class WhatsAppDateFormat:
    def __init__(self, logger):
        self.is_dayfirst = None
        self.is_yearfirst = None
        self.has_brackets = None
        self.date_sep = None
        self.date_author_sep = None
        self._logger = logger

    def infer_format(self, raw_messages):
        self.has_brackets = self._infer_brackets(raw_messages[0])
        self.date_author_sep = self._infer_date_author_sep()
        self.date_sep = self._infer_date_sep(raw_messages[0])
        self.is_yearfirst = self._infer_yearfirst(raw_messages[0])
        self.is_dayfirst = self._infer_dayfirst(raw_messages)
        self._log_resulting_format()

    def _infer_brackets(self, mess):
        return mess[0] == "["

    def _infer_date_author_sep(self):
        return "]" if self.has_brackets else " - "

    def _infer_date_sep(self, mess):
        datestr = mess.split(self.date_author_sep, 1)[0]
        if self.has_brackets:
            datestr = datestr.lstrip("[").rstrip("]")
        for c in datestr:
            if not c.isdigit():
                return c
        raise ValueError("No non-numeric character in datestring.")

    def _infer_yearfirst(self, mess):
        datestr = mess.split(self.date_author_sep, 1)[0]
        if self.has_brackets:
            datestr = datestr.lstrip("[").rstrip("]")
        return int(datestr.split(self.date_sep)[0]) >= 100

    def _infer_dayfirst(self, raw_messages):
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

    def _log_resulting_format(self):
        start = "[" if self.has_brackets else ""
        end = "]" if self.has_brackets else ""
        if self.is_yearfirst:
            date1 = "year"
            if self.is_dayfirst:
                date2 = "day"
                date3 = "month"
            else:
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
