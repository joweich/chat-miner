import datetime
import json
import logging
import re
import unicodedata
from abc import ABC, abstractmethod
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


class ParsedMessage:
    def __init__(self, time, author, body):
        self.time = time
        self.author = author
        self.body = body

    def get_dict(self):
        return {"datetime": self.time, "author": self.author, "message": self.body}


class ParsedMessageCollection:
    def __init__(self):
        self._parsed_messages = []

    def append(self, mess):
        assert isinstance(mess, ParsedMessage)
        self._parsed_messages.append(mess)

    def get_df(self):
        messages_as_dict = []
        for mess in self._parsed_messages:
            messages_as_dict.append(mess.get_dict())

        df = pd.DataFrame(messages_as_dict)
        df["weekday"] = df["datetime"].dt.day_name()
        df["hour"] = df["datetime"].dt.hour
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
        self._datetime_format = None

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

        self._infer_datetime_format()

    def _infer_datetime_format(self):
        max_first = 0
        max_second = 0
        for line in self._raw_messages:
            line = (
                line.replace(r"/", ".", 2)
                .replace("-", ".", 2)
                .replace(",", ".", 2)
                .lstrip("[")
            )
            check_year_first = int(line.split(".")[0]) >= 100
            if check_year_first:
                day_and_month = [int(num) for num in line.split(".")[1:3]]
            else:
                day_and_month = [int(num) for num in line.split(".")[:2]]

            max_first = max(max_first, day_and_month[0])
            max_second = max(max_second, day_and_month[1])

            if (max_first > 12) and (max_second > 12):
                raise ValueError(f"Invalid date format: {line}")

        if max_first > 12 and max_second <= 12:
            self._logger.info("Inferred DMY format for date.")
            self._datetime_format = "DMY"
        elif max_first <= 12 and max_second > 12:
            self._logger.info("Inferred MDY format for date.")
            self._datetime_format = "MDY"
        else:
            self._logger.warning(
                "Can't infer date format. No message with day > 12. Assuming DMY."
            )
            self._datetime_format = "DMY"

    def _parse_message(self, mess):
        timestamp_author_sep = " - " if mess[0].isnumeric() else "] "
        if timestamp_author_sep not in mess:
            self._logger.warning(
                "Failed to parse message. Message [%s] will be skipped.", mess
            )
            return None

        datestring, author_and_body = mess.split(timestamp_author_sep, 1)
        dayfirst = self._datetime_format == "DMY"
        time = datetimeparser.parse(datestring, dayfirst=dayfirst, fuzzy=True)

        if ":" in author_and_body:
            author, body = author_and_body.split(": ", 1)
        else:
            author = "System"
            body = author_and_body
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
                        lambda m: m["text"] if isinstance(m) is dict else m,
                        mess["text"],
                    )
                )
            else:
                raise ValueError(f"Unable to parse type {type(mess['text'])} in {mess}")

            time = datetime.datetime.fromtimestamp(int(mess["date_unixtime"]))
            author = mess["from"]
            return ParsedMessage(time, author, body)
        return False
