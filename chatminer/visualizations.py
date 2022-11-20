import calendar
import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from wordcloud import WordCloud, STOPWORDS
from dateutil.relativedelta import relativedelta
from matplotlib.patches import Polygon
from matplotlib.colors import ColorConverter, ListedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable


def sunburst(
    df,
    color="C0",
    edgecolor="black",
    linewidth=0.5,
    highlight_max=False,
    isolines=None,
    isolines_relative=True,
    ax=None,
):
    df_circle = df.groupby(by="hour")["message"].count().reset_index()

    hourly_count = np.zeros(24)
    hourly_count[df_circle["hour"]] = df_circle["message"]

    if ax is None:
        _, ax = plt.subplots(subplot_kw={"projection": "polar"})

    x = np.arange(0, 2 * np.pi, 2 * np.pi / len(hourly_count)) + np.pi / len(
        hourly_count
    )

    alpha = 0.6 if highlight_max else 1
    ax.bar(
        x,
        hourly_count,
        width=2 * np.pi / len(hourly_count),
        alpha=alpha,
        color=color,
        bottom=0,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )

    if highlight_max:
        max_ind = np.argmax(hourly_count)
        ax.bar(
            x[max_ind],
            hourly_count[max_ind],
            bottom=0,
            width=2 * np.pi / len(hourly_count),
            alpha=1,
            color=color,
            edgecolor=edgecolor,
            linewidth=linewidth,
        )

    ax.bar(
        x,
        np.max(hourly_count) * np.ones(len(hourly_count)),
        width=2 * np.pi / len(hourly_count),
        alpha=0.1,
        bottom=0,
        color=color,
    )

    ax.set_theta_direction(-1)
    ax.spines["polar"].set_visible(True)
    ax.set_rmax(np.max(hourly_count))
    ax.grid(True)
    ax.set_axisbelow(True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))
    ticks = [f"{x}:00" for x in range(0, 24, 3)]
    ax.set_xticklabels(ticks)

    if isolines:
        if isolines_relative:
            ax.set_yticks(np.asarray(isolines) * np.max(hourly_count))
        else:
            ax.set_yticks(isolines)

    plt.tight_layout()
    return ax


def wordcloud(df, ax=None, stopwords=None, **kwargs):
    messages = [mess.split() for mess in df["message"].values]
    words = [word.lower() for sublist in messages for word in sublist]

    if stopwords:
        stopwords = STOPWORDS.update(stopwords)

    wc = WordCloud(
        stopwords=stopwords,
        **kwargs,
    )
    wc.generate(" ".join(words))

    if ax is None:
        _, ax = plt.subplots()

    ax.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    return ax


def calendar_heatmap(
    df,
    year,
    vmin=None,
    vmax=None,
    cmap="Blues",
    fillcolor="whitesmoke",
    linewidth=1,
    linecolor=None,
    daylabels=calendar.day_abbr[:],
    dayticks=True,
    monthlabels=calendar.month_abbr[1:],
    monthticks=True,
    monthly_border=False,
    ax=None,
    **kwargs,
):
    """
    Adapted from https://github.com/MarvinT/calmap.
    Copyright (c) 2015 by Martijn Vermaat and contributors
    """

    df = df[df["datetime"].dt.year == year]
    df = df.groupby(by=df["datetime"].dt.date).count()["message"].reset_index()

    idx = pd.date_range(start=str(year), end=str(year + 1), freq="D")[:-1]
    df = df.set_index("datetime").reindex(idx)

    if vmin is None:
        vmin = df.min()
    if vmax is None:
        vmax = df.max()

    if ax is None:
        ax = plt.gca()

    if linecolor is None:
        linecolor = ax.get_facecolor()
        if ColorConverter().to_rgba(linecolor)[-1] == 0:
            linecolor = "white"

    df["fill"] = 1
    df["day"] = df.index.dayofweek
    df["week"] = df.index.isocalendar().week

    df.loc[(df.index.month == 1) & (df.week > 50), "week"] = 0
    df.loc[(df.index.month == 12) & (df.week < 10), "week"] = df.week.max() + 1

    plot_data = df.pivot(index="day", columns="week", values="message").values[::-1]
    plot_data = np.ma.masked_where(np.isnan(plot_data), plot_data)

    fill_data = df.pivot(index="day", columns="week", values="message").values[::-1]
    fill_data = np.ma.masked_where(np.isnan(fill_data), fill_data)

    ax.pcolormesh(fill_data, vmin=0, vmax=1, cmap=ListedColormap([fillcolor]))

    kwargs["linewidth"] = linewidth
    kwargs["edgecolors"] = linecolor
    pc = ax.pcolormesh(plot_data, vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.08)
    plt.colorbar(
        pc, cax=cax, ticks=[min(vmin), int((min(vmin) + max(vmax)) / 2), max(vmax)]
    )

    ax.set(xlim=(0, plot_data.shape[1]), ylim=(0, plot_data.shape[0]))

    ax.set_aspect("equal")

    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.xaxis.set_tick_params(which="both", length=0)
    ax.yaxis.set_tick_params(which="both", length=0)

    if monthticks is True:
        monthticks = range(len(monthlabels))
    elif monthticks is False:
        monthticks = []
    elif isinstance(monthticks, int):
        monthticks = range(len(monthlabels))[monthticks // 2 :: monthticks]

    if dayticks is True:
        dayticks = range(len(daylabels))
    elif dayticks is False:
        dayticks = []
    elif isinstance(dayticks, int):
        dayticks = range(len(daylabels))[dayticks // 2 :: dayticks]

    ax.set_xlabel("")

    xticks, labels = [], []
    for month in range(1, 13):
        first = datetime.datetime(year, month, 1)
        last = first + relativedelta(months=1, days=-1)
        y0 = 6 - first.weekday()
        y1 = 6 - last.weekday()
        start = datetime.datetime(year, 1, 1).weekday()
        x0 = (int(first.strftime("%j")) + start - 1) // 7
        x1 = (int(last.strftime("%j")) + start - 1) // 7
        P = [
            (x0, y0 + 1),
            (x0, 0),
            (x1, 0),
            (x1, y1),
            (x1 + 1, y1),
            (x1 + 1, 7),
            (x0 + 1, 7),
            (x0 + 1, y0 + 1),
        ]

        xticks.append(x0 + (x1 - x0 + 1) / 2)
        labels.append(first.strftime("%b"))
        if monthly_border:
            poly = Polygon(
                P,
                edgecolor="black",
                facecolor="None",
                linewidth=1,
                zorder=20,
                clip_on=False,
            )
            ax.add_artist(poly)

    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    ax.set_ylabel("")
    ax.yaxis.set_ticks_position("left")
    ax.set_yticks([6 - i + 0.5 for i in dayticks])
    ax.set_yticklabels(
        [daylabels[i] for i in dayticks], rotation="horizontal", va="center"
    )
    plt.tight_layout()
    return ax
