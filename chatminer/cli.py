#!/usr/bin/env python3

import argparse,sys
from chatminer.chatparsers import WhatsAppParser,FacebookMessengerParser,InstagramJsonParser,SignalParser,TelegramJsonParser

def get_args():
        
    try:
        #Initialising the argument parser
        parser=argparse.ArgumentParser(description="chat-miner provides lean parsers for every major platform transforming chats into pandas dataframes. Artistic visualizations allow you to explore your data and create artwork from your chats.")

        #Adding the argument for the name of the parser 
        parser.add_argument('-p','--parser',type=str,help='The platform from which the chats are imported',choices=['whatsapp','instagram','facebook','signal','telegram'])

        #Adding the argument for the name of the input file
        parser.add_argument('-i','--input',type=str,help='Input file to be processed')

        #adding the argument for the name of the output file
        parser.add_argument('-o','--output',type=str,help='Output file for the results')

        return parser.parse_args(),parser
    except:
        sys.exit()


def main():

    try:
        args,parser=get_args()

        parser_type=args.parser
        INPUT_FILE=args.input
        OUTPUT_FILE=args.output

        if INPUT_FILE==None or OUTPUT_FILE==None or parser_type==None:
            raise ValueError

        #Logic to parse the file and make a csv file
        if((parser_type).lower()=='whatsapp'):
            parser_type=WhatsAppParser(INPUT_FILE)
            parser_type.parse_file()
            output=parser_type.parsed_messages.get_df()

        elif((parser_type).lower()=='facebook'):
            parser_type=FacebookMessengerParser(INPUT_FILE)
            parser_type.parse_file()
            output=parser_type.parsed_messages.get_df()

        elif((parser_type).lower()=='instagram'):
            parser_type=InstagramJsonParser(INPUT_FILE)
            parser_type.parse_file()
            output=parser_type.parsed_messages.get_df()

        elif((parser_type).lower()=='signal'):
            parser_type=SignalParser(INPUT_FILE)
            parser_type.parse_file()
            output=parser_type.parsed_messages.get_df()

        elif((parser_type).lower()=='telegram'):
            parser_type=TelegramJsonParser(INPUT_FILE)
            parser_type.parse_file()
            output=parser_type.parsed_messages.get_df()

        #csv file made and saved to the path specified by the user
        output.to_csv(OUTPUT_FILE,index=False)
            

    except ValueError:
        parser.print_usage()

    except:
        sys.exit()

if __name__=="__main__":
    main()
