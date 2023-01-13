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
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D


def sunburst(
    df,
    color="C0",
    edgecolor="black",
    linewidth=0.5,
    highlight_max=False,
    isolines=None,
    isolines_relative=True,
    ax=None,
    authors=None,
):
    if authors:
        df = df[df["author"].isin(authors)]

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


def wordcloud(df, ax=None, stopwords=None, authors=None, **kwargs):
    if authors:
        df = df[df["author"].isin(authors)]

    messages = [mess.split() for mess in df["message"].values]
    words = [word.lower() for sublist in messages for word in sublist]

    if stopwords:
        STOPWORDS.update(stopwords)
    stopwords = STOPWORDS

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
    authors=None,
    **kwargs,
):
    """
    Adapted from https://github.com/MarvinT/calmap.
    Copyright (c) 2015 by Martijn Vermaat and contributors
    """

    if authors:
        df = df[df["author"].isin(authors)]

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


def radar(
    df,
    color="C0",
    alpha=0.3,
    ax=None,
    authors=None,
):
    if authors:
        df = df[df["author"].isin(authors)]

    cats = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    df_radar = df.groupby(by="weekday")["message"].count().reindex(cats)

    theta = radar_factory(7, frame="polygon")

    if ax is None:
        _, ax = plt.subplots(subplot_kw={"projection": "radar"})

    ax.plot(theta, df_radar.values, color=color)
    ax.fill(theta, df_radar.values, facecolor=color, alpha=alpha)
    ax.set_varlabels(cats)
    return ax


def radar_factory(num_vars, frame="circle"):
    """
    Source: https://matplotlib.org/stable/gallery/specialty_plots/radar_chart.html
    """
    # calculate evenly-spaced axis angles
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    class RadarTransform(PolarAxes.PolarTransform):
        def transform_path_non_affine(self, path):
            # Paths with non-unit interpolation steps correspond to gridlines,
            # in which case we force interpolation (to defeat PolarTransform's
            # autoconversion to circular arcs).
            if path._interpolation_steps > 1:
                path = path.interpolated(num_vars)
            return Path(self.transform(path.vertices), path.codes)

    class RadarAxes(PolarAxes):

        name = "radar"
        PolarTransform = RadarTransform

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # rotate plot such that the first axis is at the top
            self.set_theta_zero_location("N")

        def fill(self, *args, closed=True, **kwargs):
            """Override fill so that line is closed by default"""
            return super().fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            # FIXME: markers at x[0], y[0] get doubled-up
            if x[0] != x[-1]:
                x = np.append(x, x[0])
                y = np.append(y, y[0])
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
            # in axes coordinates.
            if frame == "circle":
                return Circle((0.5, 0.5), 0.5)
            elif frame == "polygon":
                return RegularPolygon((0.5, 0.5), num_vars, radius=0.5, edgecolor="k")
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

        def _gen_axes_spines(self):
            if frame == "circle":
                return super()._gen_axes_spines()
            elif frame == "polygon":
                # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
                spine = Spine(
                    axes=self,
                    spine_type="circle",
                    path=Path.unit_regular_polygon(num_vars),
                )
                # unit_regular_polygon gives a polygon of radius 1 centered at
                # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
                # 0.5) in axes coordinates.
                spine.set_transform(
                    Affine2D().scale(0.5).translate(0.5, 0.5) + self.transAxes
                )
                return {"polar": spine}
            else:
                raise ValueError("Unknown value for 'frame': %s" % frame)

    register_projection(RadarAxes)
    return theta


def is_radar_registered():
    try:
        plt.subplots(subplot_kw={"projection": "radar"})
    except ValueError:
        return False
    return True
