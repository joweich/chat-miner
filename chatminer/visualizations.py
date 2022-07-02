import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def sunburst(df: pd.DataFrame):
    df_circle = df.groupby(by='hour')['message'].count().reset_index()

    time = df_circle['hour']
    count = df_circle['message']

    c = np.zeros(24)
    c[time] = count
    count = c

    ax = plt.subplot(111, projection="polar")

    x = np.arange(0, 2 * np.pi, 2 * np.pi / len(count)) + np.pi / len(count)

    ax.bar(x, count, width=2 * np.pi / len(count), alpha=0.4, color='#e76f51',
           bottom=0)

    max_ind = np.argmax(count)
    ax.bar(x[max_ind], count[max_ind], bottom=0, width=2 * np.pi / len(count),
           alpha=1, color='#e76f51')

    ax.bar(x, np.max(count) * np.ones(len(count)),
           width=2 * np.pi / len(count), alpha=0.15, bottom=0, color='#cb997e',
           edgecolor="black")

    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.spines["polar"].set_visible(False)
    ax.set_theta_offset(np.pi / 2)
    ax.set_xticks(np.linspace(0, 2 * np.pi, 24, endpoint=False))
    ticks = ["12 AM", "", "", "3 AM", "", "", "6 AM", "", "", "9 AM",
             "", "", "12 PM", "", "", "3 PM", "", "", "6 PM", "", "",
             "9 PM", "", ""]
    ax.set_xticklabels(ticks)
    ax.set_title("Messages per Daytime", fontdict={"fontsize": 15})
    plt.setp(ax.get_yticklabels(), visible=False)
    plt.tight_layout()
    plt.show()


# def wordcloud(df: pd.DataFrame, stopwords: list):
#     messages = [word.split() for word in df["message"].values]
#     words = [word.lower() for sublist in messages for word in sublist]

#     stopwords = STOPWORDS.update(stopwords)

#     wordcloud = WordCloud(stopwords=stopwords, max_font_size=90, width=800,
#                           height=400, background_color='white',
#                           colormap='magma', min_word_length=2, max_words=400,
#                           min_font_size=12)
#     wordcloud.generate(' '.join(words))

#     plt.figure(figsize=(8, 4))
#     plt.imshow(wordcloud, interpolation="bilinear")
#     plt.axis("off")
#     plt.tight_layout()
#     plt.show()
