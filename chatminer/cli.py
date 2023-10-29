#!/usr/bin/env python3

import argparse
import sys

from chatminer.chatparsers import (
    FacebookMessengerParser,
    InstagramJsonParser,
    SignalParser,
    TelegramJsonParser,
    WhatsAppParser,
)


def get_args():
    try:
        cliparser = argparse.ArgumentParser(
            description="chat-miner provides lean parsers for every major platform transforming chats into pandas dataframes.\
             Artistic visualizations allow you to explore your data and create artwork from your chats."
        )

        cliparser.add_argument(
            "-p",
            "--parser",
            type=str,
            help="The platform from which the chats are imported",
            choices=["whatsapp", "instagram", "facebook", "signal", "telegram"],
        )

        cliparser.add_argument(
            "-i", "--input", type=str, help="Input file to be processed"
        )

        cliparser.add_argument(
            "-o", "--output", type=str, help="Output file for the results"
        )

        return cliparser.parse_args(), cliparser
    except KeyboardInterrupt:
        sys.exit()


def main():
    try:
        args, cliparser = get_args()

        if args.input is None or OUTPUT_FILE is None or args.parser is None:
            raise ValueError

        if (args.parser).lower() == "whatsapp":
            chatparser = WhatsAppParser(args.input)

        elif (args.parser).lower() == "facebook":
            chatparser = FacebookMessengerParser(args.input)
        elif (args.parser).lower() == "instagram":
            chatparser = InstagramJsonParser(args.input)
        elif (args.parser).lower() == "signal":
            chatparser = SignalParser(args.input)
        elif (args.parser).lower() == "telegram":
            chatparser = TelegramJsonParser(args.input)
        else:
            raise ValueError

        chatparser.parse_file()
        df = chatparser.parsed_messages.get_df()
        df.to_csv(args.output, index=False)

    except ValueError:
        cliparser.print_usage()

    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
