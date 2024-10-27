from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt

from evt_processing import PressedKeyEvt
from frequencies import LetterFrequencies


def plot_evts_by_hour_minute(evts: list[PressedKeyEvt]) -> None:
    timestamps = []
    for evt in evts:
        date = datetime.fromtimestamp(evt.timestamp)
        timestamps.append(date.hour + date.minute / 60)
    plt.hist(timestamps)
    plt.show()


def plot_key_frequencies(key_frequencies: dict[str, int], relative=False, title='Key Frequencies',
                         comp_rel_frequencies: LetterFrequencies | None = None):
    key_freq_items = [[key, count] for key, count in key_frequencies.items()]
    ylabel = 'count'
    if relative:
        total_count = sum(entry[1] for entry in key_freq_items)
        for entry in key_freq_items:
            entry[1] /= total_count
        ylabel = 'frequency'
    # key_freq_items.sort(key=lambda x: ord(x[0]) if len(x) == 0 else x[0])
    key_freq_items.sort(key=lambda x: x[1], reverse=True)
    y_pos = np.arange(len(key_freq_items))

    x_labels = [entry[0] for entry in key_freq_items]
    y_values = [entry[1] for entry in key_freq_items]

    fig = plt.figure(1, (25.0, 8.0))

    colors = ['#1f77b4', '#b41f1f']
    offset = 0
    width = 0.8
    if comp_rel_frequencies is not None:
        offset = -0.2
        width = 0.4
        y2_values = [comp_rel_frequencies.frequencies[entry[0]] for entry in key_freq_items]
        plt.bar(y_pos - offset, y2_values, width=width, color=colors[1], alpha=0.5)
        labels = ['data', comp_rel_frequencies.name]
        handles = [plt.Rectangle((0, 0), 1, 1, color=colors[0]),
                   plt.Rectangle((0, 0), 1, 1, color=colors[1])]
        plt.legend(handles, labels)

    plt.bar(y_pos + offset, y_values, width=width, color=colors[0], alpha=0.5)
    plt.xticks(y_pos, x_labels, rotation=90)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()
