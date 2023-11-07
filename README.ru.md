<picture>
  <source media="(prefers-color-scheme: dark)" srcset="doc/_static/logo-wide-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="doc/_static/logo-wide-light.png">
  <img alt="chat-miner: turn your chats into artwork" src="doc/_static/logo-wide-light.png">
</picture>

-----------------

# chat-miner: Превратите свои чаты в искусство!

[![PyPI Version](https://img.shields.io/pypi/v/chat-miner.svg)](https://pypi.org/project/chat-miner/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/chat-miner/month)](https://pepy.tech/project/chat-miner)
[![codecov](https://codecov.io/gh/joweich/chat-miner/branch/main/graph/badge.svg?token=6EQF0YNGLK)](https://codecov.io/gh/joweich/chat-miner)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

🌐
[English][EN]
**Русский**

[EN]:README.md
[RU]:README.ru.md

-----------------

**chat-miner** предоставляет эффективные парсеры для любой крупной платформы, представляющие чаты как pandas-датафреймы. Художественная визуализация позволяет вам исследовать данные ваших переписок и создавать из них произведения искусства.


## 1. Установка
Последний выпуск, включая зависимости, можно установить с помощью PyPI:
```sh
pip install chat-miner
```
Если вы заинтересованы в участии в проекте, запуске свежего исходного кода или просто любите все билдить сами:
```sh
git clone https://github.com/joweich/chat-miner.git
cd chat-miner
pip install -r requirements.txt
```

## 2. Экспортирование чатов
Ознакомьтесь с официальными руководствами для [WhatsApp](https://faq.whatsapp.com/1180414079177245/), [Signal](https://github.com/carderne/signal-export), [Telegram](https://telegram.org/blog/export-and-more), [Facebook Messenger](https://www.facebook.com/help/messenger-app/713635396288741) или [Instagram Chats](https://help.instagram.com/181231772500920), чтобы узнать, как экспортировать чаты для вашей платформы.

## 3. Парсинг
Код ниже показывает работу модуля ``WhatsAppParser``.
``SignalParser``, ``TelegramJsonParser``, ``FacebookMessengerParser`` и ``InstagramJsonParser`` используются тем же образом.
```python
from chatminer.chatparsers import WhatsAppParser

parser = WhatsAppParser(FILEPATH)
parser.parse_file()
df = parser.parsed_messages.get_df()
```
**Внимание:**
В зависимости от вашей ОС, python может требовать конвертирования пути к файлу в "сырую" строку.
```python
import os
FILEPATH = r"C:\Users\Username\chat.txt" # Windows
FILEPATH = "/home/username/chat.txt" # Unix
assert os.path.isfile(FILEPATH)

```

## 4. Визуализация
```python
import chatminer.visualizations as vis
import matplotlib.pyplot as plt
```
### 4.1 Тепловая карта: Количество сообщений в день
```python
fig, ax = plt.subplots(2, 1, figsize=(9, 3))
ax[0] = vis.calendar_heatmap(df, year=2020, cmap='Oranges', ax=ax[0])
ax[1] = vis.calendar_heatmap(df, year=2021, linewidth=0, monthly_border=True, ax=ax[1])
```

<p align="center">
  <img src="examples/heatmap.svg">
</p>

### 4.2 Sunburst-диаграмма: Количество сообщений по времени суток
```python
fig, ax = plt.subplots(1, 2, figsize=(7, 3), subplot_kw={'projection': 'polar'})
ax[0] = vis.sunburst(df, highlight_max=True, isolines=[2500, 5000], isolines_relative=False, ax=ax[0])
ax[1] = vis.sunburst(df, highlight_max=False, isolines=[0.5, 1], color='C1', ax=ax[1])
```

<p align="center">
  <img src="examples/sunburst.svg">
</p>

### 4.3 Облако слов: Частота слов
```python
fig, ax = plt.subplots(figsize=(8, 3))
stopwords = ['these', 'are', 'stopwords']
kwargs={"background_color": "white", "width": 800, "height": 300, "max_words": 500}
ax = vis.wordcloud(df, ax=ax, stopwords=stopwords, **kwargs)
```
<p align="center">
  <img src="examples/wordcloud.svg">
</p>

### 4.4 Радарная диаграмма: Количество сообщений по дням недели
```python
if not vis.is_radar_registered():
	vis.radar_factory(7, frame="polygon")
fig, ax = plt.subplots(1, 2, figsize=(7, 3), subplot_kw={'projection': 'radar'})
ax[0] = vis.radar(df, ax=ax[0])
ax[1] = vis.radar(df, ax=ax[1], color='C1', alpha=0)
```
<p align="center">
  <img src="examples/radar.svg">
</p>

## 5. Обработка естесственного языка

### 5.1 Добавьте настрой

```python
from chatminer.nlp import add_sentiment

df_sentiment = add_sentiment(df)
```
### 5.2 Пример диаграммы: Настрой каждого автора в групповом чате

```python
df_grouped = df_sentiment.groupby(['author', 'sentiment']).size().unstack(fill_value=0)
ax = df_grouped.plot(kind='bar', stacked=True, figsize=(8, 3))
```

<p align="center">
  <img src="examples/nlp.svg">
</p>


## 6. Интерфейс коммандной строки
Через коммандную строку поддерживается парс чатов в csv-файлы.
На данный момент, напрямую через коммандную строку создавать визуализации **нельзя!**

Пример использования:
```bash
$ chatminer -p whatsapp -i exportfile.txt -o output.csv
```

Руководство к использованию:
```
usage: chatminer [-h] [-p {whatsapp,instagram,facebook,signal,telegram}] [-i INPUT] [-o OUTPUT]

options:
  -h, --help 
                        Show this help message and exit
  -p {whatsapp,instagram,facebook,signal,telegram}, --parser {whatsapp,instagram,facebook,signal,telegram}
                        The platform from which the chats are imported
  -i INPUT, --input INPUT
                        Input file to be processed
  -o OUTPUT, --output OUTPUT
                        Output file for the results
```
