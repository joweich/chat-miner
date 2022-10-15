## Getting your data
---
As of now, only WhatsApp and Signal chats are supported. 

### Steps to export a WhatsApp chat:
 - Go to the app
 - Go to Settings/Chats/Chat History
 - Tap *Export chat*
 - Select the chat you want to export

### Steps to export a Signal chat (from Signal-Desktop):
 - Open a Terminal
 - Run `pip install signal-export` (This will install [signal-export](https://github.com/carderne/signal-export) on your computer)
 - Run `sigexport ~/signal-chats` (This saves the Signal chats in `~/signal-chats`)

### Steps to export a Telegram chat (from Telegram-Desktop):
- Open the telegram-desktop app
- Go to the chat you want to export
- Click on the three dots (...) on the upper right side of the chat
- Click on *export chat history*
- For now this tool only accepts JSON parsing, so select the *json* format and click on export.

 ## Parsing the chatfile
 ---
 The following code uses the ``WhatsAppParser`` module to:
 - Read a chatfile
 - Infer its datetime format
 - Parse its content into a DataFrame
 - Add additonal metadata columns
 ```python
from chatminer.chatparsers import WhatsAppParser

parser = WhatsAppParser(FILEPATH)
parser.parse_file_into_df()
print(parser.df.describe())
```

## Creating Visualizations
---
### Sunburst Chart
```python
import chatminer.visualizations as vis
vis.sunburst(parser.df)
```
![Sunburst](examples/sunburst.png)

---
### Wordcloud
```python
import chatminer.visualizations as vis
stopwords = ['media', 'omitted', 'missed', 'voice', 'call']
vis.wordcloud(parser.df, stopwords)
```
![Wordcloud](examples/wordcloud.png)
