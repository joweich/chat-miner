from chatminer.chatparsers import WhatsAppParser
import chatminer.visualizations as vis

FILEPATH = "C:/Users/qwerk/Downloads/WhatsApp_Chat_with__Dudu__Gang_.txt"
parser = WhatsAppParser(FILEPATH)
parser.parse_file_into_df()
print(parser.df.describe())

vis.sunburst(parser.df)