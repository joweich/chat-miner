## Getting your data
---
As of now, only WhatsApp chats are supported. Steps to export a WhatsApp chat:
 - Go to the app
 - Go to Settings/Chats/Chat History
 - Tap *Export chat*
 - Select the chat you want to export

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