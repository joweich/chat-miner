import unicodedata
import json
import logging
import re
import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from dateutil import parser as datetimeparser
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
)


class Parser(ABC):
    def __init__(self, filepath):
        self._file = Path(filepath)
        assert self._file.is_file()

        self.messages = None
        self.df = None

        self._logger = logging.getLogger(__name__)
        self._logger.info(
            """
            Depending on the platform, the message format in chat logs might not be
            standardized accross devices/versions/localization and might change over
            time. Please report issues including your message format via GitHub.
            """
        )
        self._logger.info("Initialized parser.")
        self._read_file_into_list()

    def parse_file_into_df(self):
        self._logger.info("Starting parsing raw messages into dataframe...")
        parsed_messages = []
        with logging_redirect_tqdm():
            for mess in tqdm(self.messages):
                parsed_mess = self._parse_message(mess)
                if parsed_mess:
                    parsed_messages.append(parsed_mess)

        self.df = pd.DataFrame(parsed_messages)
        self._add_metadata()
        self._logger.info("Finished parsing raw messages into dataframe.")

    def write_df_to_csv(self, filename):
        if self.df is not None:
            self.df.to_csv(filename, index=False)
            self._logger.info("Finished writing dataframe to csv.")
        else:
            self._logger.error("Failed writing to csv. Parse file first.")

    def _add_metadata(self):
        self.df["weekday"] = self.df["datetime"].dt.day_name()
        self.df["hour"] = self.df["datetime"].dt.hour
        self.df["words"] = self.df["message"].apply(lambda s: len(s.split(" ")))
        self.df["letters"] = self.df["message"].apply(len)

    @abstractmethod
    def _read_file_into_list(self):
        return

    @abstractmethod
    def _parse_message(self, mess):
        return


class SignalParser(Parser):
    def _read_file_into_list(self):
        def _is_new_message(line):
            regex = r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\]"
            return re.match(regex, line)

        self._logger.info("Starting reading raw messages into memory...")
        self.messages = []
        buffer = []
        with self._file.open(encoding="utf-8") as f:
            messages_raw = reversed(list(f))

        for line in messages_raw:
            line = line.strip()
            if not line:
                continue
            if _is_new_message(line):
                if buffer:
                    buffer.append(line)
                    buffer.reverse()
                    self.messages.append(" ".join(buffer))
                    buffer.clear()
                else:
                    self.messages.append(line)
            else:
                buffer.append(line)
        self._logger.info(
            "Finished reading %i raw messages into memory.", len(self.messages)
        )

    def _parse_message(self, mess):
        datetime_raw, mess = mess.split("]", 1)
        time = datetimeparser.parse(datetime_raw[1:])
        author, mess = mess.split(":", 1)
        author = author.strip()
        mess = mess.strip()
        parsed_message = {"datetime": time, "author": author, "message": mess}
        return parsed_message


class WhatsAppParser(Parser):
    def __init__(self, filepath):
        super().__init__(filepath)
        self._infer_datetime_format()

    def _read_file_into_list(self):
        def _is_new_message(line):
            regex = r"(^[\u200e]?\[?((\d{1})|(\d{2}))((\.)|(\/)|(\-))((\d{1})|(\d{2}))((\.)|(\/)|(\-))((\d{4})|(\d{2})))"
            return re.match(regex, line)

        self._logger.info("Starting reading raw messages into memory...")
        self.messages = []
        buffer = []
        with self._file.open(encoding="utf-8") as f:
            messages_raw = reversed(list(f))

        for line in messages_raw:
            if not line:
                continue

            if _is_new_message(line):
                line = line.replace("\u200e", "")
                line = unicodedata.normalize("NFKC", line.strip())
                if buffer:
                    buffer.append(line)
                    buffer.reverse()
                    joined_buffer = " ".join(buffer)
                    self.messages.append("".join(joined_buffer.splitlines()))
                    buffer.clear()
                else:
                    self.messages.append(line)
            else:
                buffer.append(line)

        self._logger.info(
            "Finished reading %i raw messages into memory.", len(self.messages)
        )

    def _infer_datetime_format(self):
        max_first = 0
        max_second = 0
        for line in self.messages:
            line = line.replace(r"/", ".", 2).replace("-", ".", 2).lstrip("[")
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
                "Can't infer format of date. \
                No message with day > 12. Assuming day first."
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

        parsed_message = {"datetime": time, "author": author, "message": body}
        return parsed_message


class FacebookMessengerParser(Parser):
    def _read_file_into_list(self):
        self._logger.info("Starting reading raw messages into memory...")
        self.messages = []
        with self._file.open(encoding="utf-8") as f:
            messages_raw = reversed((json.load(f)["messages"]))

        for line in messages_raw:
            self.messages.append(line)
        self._logger.info(
            "Finished reading %i raw messages into memory.", len(self.messages)
        )

    def _parse_message(self, mess):
        if mess["type"] == "Share":
            body = mess["share"]["link"]
        elif "sticker" in mess:
            body = mess["sticker"]["uri"]
        else:
            body = mess["content"]

        parsed_message = {
            "datetime": datetime.datetime.fromtimestamp(mess["timestamp_ms"] / 1000),
            "author": mess["sender_name"],
            "message": body,
        }
        return parsed_message


class TelegramJsonParser(Parser):
    def _read_file_into_list(self):
        self._logger.info("Starting reading raw messages into memory...")
        with self._file.open(encoding="utf-8") as f:
            json_objects = json.load(f)

        self.messages = json_objects["messages"]
        self._logger.info(
            "Finished reading %i raw messages into memory.", len(self.messages)
        )

    def _parse_message(self, mess):
        if "from" in mess and "text" in mess:
            text = ""
            if type(mess["text"]) is str:
                text = mess["text"]
            elif type(mess["text"]) is list:
                assert all(
                    [
                        (type(m) is dict and "text" in m) or type(m) is str
                        for m in mess["text"]
                    ]
                )
                text = " ".join(
                    map(lambda m: m["text"] if type(m) is dict else m, mess["text"])
                )
            else:
                raise ValueError(f"Unable to parse type {type(mess['text'])} in {mess}")

            parsed_message = {
                "author": mess["from"],
                "datetime": datetime.datetime.fromtimestamp(int(mess["date_unixtime"])),
                "message": text,
            }
            return parsed_message

        return False


class TelegramHtmlParser(Parser):
    def _read_file_into_list(self):
        self._logger.info("Starting reading raw messages into memory...")
        with self._file.open(encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            self.messages = list(
                soup.find_all("div", class_="message default clearfix")
            )
        self._logger.info(
            "Finished reading %i raw messages into memory.", len(self.messages)
        )

    def _parse_message(self, mess):
        from_name = mess.find("div", class_="from_name")
        message = from_name.find_next("div")
        if "text" in message["class"]:
            message = message.text
        else:
            message = "Media"
        parsed_message = {
            "author": from_name.text,
            "datetime": datetimeparser.parse(mess.find("div", class_="date")["title"]),
            "message": message,
        }
        return parsed_message
