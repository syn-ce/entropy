import functools
import logging
import math
import string
import struct
import sys

import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from os.path import isfile
import time
import evdev
from dotenv import load_dotenv
from evdev import InputEvent

# Define format of input_event structure (24 bytes)
# 'Q' for tv_sec (8 bytes), 'Q' for tv_usec (8 bytes), 'H' for type (2 bytes),
# 'H' for code (2 bytes), 'i' for value (4 bytes)
input_event_format = 'QQHHI'
# Size of input_event structure (24 bytes)
event_size = struct.calcsize(input_event_format)


def is_file_modified_after(path: os.DirEntry[str], start_time: float):
    return isfile(path) and os.stat(path).st_mtime >= start_time


def read_evts(path: os.DirEntry[str]) -> list[InputEvent]:
    # Contains raw input
    with open(path, 'rb') as file:
        evts = []
        while True:
            # Read next event
            evt_data = file.read(event_size)

            if len(evt_data) < event_size:  # Reached end of file
                break

            # Unpack event according to input_event structure
            tv_sec, tv_usec, event_type, event_code, event_value = struct.unpack(input_event_format, evt_data)
            evts.append(InputEvent(tv_sec, tv_usec, event_type, event_code, event_value))

        return evts


def read_evts_between(path: os.DirEntry[str], start_time: float, end_time: float = sys.float_info.max) -> list[
    InputEvent]:
    return [evt for evt in read_evts(path) if start_time <= evt.timestamp() < end_time]


def get_events_between(path: str, start_time: float, end_time: float = sys.float_info.max, sort=False) -> list[
    InputEvent]:
    # Get files which have been modified after (including) start_time
    files = [file for file in os.scandir(path) if is_file_modified_after(file, start_time)]

    evts = []
    for file in files:
        for evt in read_evts_between(file, start_time, end_time):
            evts.append(evt)

    if sort:
        evts.sort(key=lambda evt: evt.timestamp())
    return evts


def filter_key_down_evts(evts: list[InputEvent]) -> list[evdev.InputEvent]:
    key_down_evts = []
    for evt in evts:
        categorized = evdev.categorize(evt)
        if isinstance(categorized, evdev.KeyEvent) and categorized.keystate == evdev.KeyEvent.key_down:
            key_down_evts.append(evt)
    return key_down_evts


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def evts_to_frequencies(evts: list[InputEvent], multivalue_code_mappings: dict[str, list[str]]) -> dict[str, int]:
    """
    :param evts:
    :param multivalue_code_mappings: Maps code name to list of values it maps (would be better the other way around,
    but lists aren't hashable)
    :return:
    """
    frequencies = dict()
    for evt in evts:
        code_name = evdev.ecodes.keys[evt.code]
        if isinstance(code_name, list):
            code_names = code_name
            # Find matching list and its specified code (if there are multiple matches, this depends on items())
            for code, l in multivalue_code_mappings.items():
                if code_names == l:
                    code_name = code
                    break
            if isinstance(code_name, list):  # Haven't found matching (or valid) entry in list
                logging.warning(f'No match for multiple-valued event key {evt.code}: {code_name}')
                continue
            else:
                logging.info(f'Mapped multiple-valued event key {evt.code}: {code_names} to {code_name}')
        frequencies[code_name] = frequencies.get(code_name, 0) + 1
    return frequencies


def get_day_evts(path: str, day_timestamp: float) -> list[InputEvent]:
    date = datetime.fromtimestamp(day_timestamp)
    day_date = datetime(date.year, date.month, date.day)
    day_start = day_date.timestamp()
    next_day_start = (day_date + timedelta(days=1)).timestamp()
    return get_events_between(path, day_start, next_day_start)


def get_today_evts(path: str) -> list[InputEvent]:
    return get_day_evts(path, time.time())


load_dotenv()
INPUT_EVENTS_PATH = os.getenv('INPUT_EVENTS_PATH')

todays_evts = get_today_evts(INPUT_EVENTS_PATH)
# all_evts = get_events_after(INPUT_EVENTS_PATH, 0)
evts = filter_key_down_evts_apply_modifiers(todays_evts)
multival_code_maps = {'KEY_MUTE': ['KEY_MIN_INTERESTING', 'KEY_MUTE']}
key_frequencies = evts_to_frequencies(evts, multival_code_maps)


def calc_entropy(distribution: list[float]):
    """
    :param distribution: List of [probability, nr_occurrences]
    :return:
    """
    # Probabilities have to sum to 1
    assert abs(sum(distribution) - 1) < sys.float_info.epsilon
    entropy = -sum([p * math.log2(p) for p in distribution])
    return entropy


print(key_frequencies)
print(len(key_frequencies.keys()))
probabilities = [count / sum(key_frequencies.values()) for count in key_frequencies.values()]
print(calc_entropy(probabilities))
print(calc_entropy([1 / len(key_frequencies.values()) for _ in key_frequencies.values()]))

total_nr_keypresses = sum(key_frequencies.values())
print(total_nr_keypresses)

timestamps = []
for evt in evts:
    date = datetime.fromtimestamp(evt.timestamp())
    timestamps.append(date.hour)

plt.hist(timestamps)
plt.show()

a = "1234567890ß"
b = "¹²³¼$¬{[]}\\"
c = "!\"§$%&/()=?"

for i in range(10):
    print(f'\'{a[i]}\': \'{c[i]}\',')

print(string.ascii_letters)
print(string.ascii_lowercase)
print(string.ascii_uppercase)

# type_code_matrix = np.array(type_code_matrix)
# print(type_code_matrix)
# plt.imshow(type_code_matrix, cmap='hot')
# plt.show()
