from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt

from evt_processing import PressedKeyEvt


def plot_evts_by_hour_minute(evts: list[PressedKeyEvt]) -> None:
    timestamps = []
    for evt in evts:
        date = datetime.fromtimestamp(evt.timestamp)
        timestamps.append(date.hour + date.minute / 60)
    plt.hist(timestamps)
    plt.show()


def plot_key_frequencies(key_frequencies: dict[str, int], title='Key Frequencies'):
    key_freq_items = [[key, count] for key, count in key_frequencies.items()]
    # key_freq_items.sort(key=lambda x: ord(x[0]) if len(x) == 0 else x[0])
    key_freq_items.sort(key=lambda x: x[1], reverse=True)
    y_pos = np.arange(len(key_freq_items))
    x_labels = [entry[0] for entry in key_freq_items]
    y_values = [entry[1] for entry in key_freq_items]

    fig = plt.figure(1, (25.0, 8.0))
    plt.bar(y_pos, y_values, align='center', alpha=0.5)
    plt.xticks(y_pos, x_labels, rotation=90)
    plt.ylabel('count')
    plt.title(title)
    plt.show()
