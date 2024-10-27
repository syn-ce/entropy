# Define format of input_event structure (24 bytes)
# 'Q' for tv_sec (8 bytes), 'Q' for tv_usec (8 bytes), 'H' for type (2 bytes),
# 'H' for code (2 bytes), 'i' for value (4 bytes)
import logging
import os
import struct
import sys
from datetime import datetime, timedelta
import time
from os.path import isfile

import evdev
from evdev import InputEvent

from mappings import keycode_conversion, altgr_conversion, shift_conversion, multivalue_code_maps

input_event_format = 'QQHHI'
# Size of input_event structure (24 bytes)
event_size = struct.calcsize(input_event_format)


class PressedKeyEvt:
    def __init__(self, value: str, timestamp: float):
        self.value = value
        self.timestamp = timestamp


class KeyModifier:
    def __init__(self, name: str, key_codes: list[int], conversion_table: dict[str, str], timestamp: float,
                 active: bool):
        self.name = name
        self.key_codes = key_codes
        self.conversion_table = conversion_table
        self.timestamp = timestamp
        self.active = active


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
    print(end_time - start_time)
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


def filter_key_down_evts(evts: list[InputEvent]) -> list[PressedKeyEvt]:
    key_down_evts = []
    for evt in evts:
        categorized = evdev.categorize(evt)
        if isinstance(categorized, evdev.KeyEvent) and categorized.keystate == evdev.KeyEvent.key_down:
            key_down_evts.append(PressedKeyEvt(
                keycode_conversion.get(evt.code, evdev.ecodes.keys[evt.code]), evt.timestamp()))
    return key_down_evts


def apply_multivalue_code_mapping(code_name: list[str]) -> str | None:
    code_names = code_name
    # Find matching list and its specified code (if there are multiple matches, this depends on items())
    for code, l in multivalue_code_maps.items():
        if code_names == l:
            code_name = code
            break
    if isinstance(code_name, list):  # Haven't found matching (or valid) entry in list
        logging.warning(f'No match for multiple-valued event key {code_name}')
        return None
    else:
        logging.info(f'Mapped multiple-valued event key {code_names} to {code_name}')
        return code_name


def deactivate_modifiers_if_expired(modifiers: list[KeyModifier], max_allowed_age: float) -> None:
    """
    Deactivate modifiers in list if they are too old (we have probably missed a keyup event if we are registering a 'Shift'-Keypress for 10 seconds straight
    :param max_allowed_age: Maximum allowed time allowed for a modifier, in seconds
    :param modifiers: Modifiers to (potentially) deactivate
    :return: None
    """

    now = time.time()
    for modifier in modifiers:
        if modifier.timestamp - now > max_allowed_age and modifier.active:
            logging.warning('Deactivated modifier %s because it was pressed longer than %f seconds', modifier.name,
                            max_allowed_age)
            modifier.active = False


def update_modifiers(evt: InputEvent, modifiers: list[KeyModifier], state: bool) -> [int, int]:
    categorized = evdev.categorize(evt)

    for modifier in modifiers:
        if categorized.event.code in modifier.key_codes:
            modifier.active = state
            modifier.timestamp = evt.timestamp()

    deactivate_modifiers_if_expired(modifiers, 10)  # Deactivate after 10 seconds


def apply_modifiers(key_value: str, timestamp: float, modifiers: list[KeyModifier]) -> PressedKeyEvt:
    for modifier in modifiers:
        if modifier.active:
            key_value = modifier.conversion_table.get(key_value, key_value)
            break  # Only apply one modifier
    return PressedKeyEvt(key_value, timestamp)


def filter_key_down_evts_apply_modifiers(evts: list[InputEvent]) -> list[PressedKeyEvt]:
    """
    Filter the events for keydown presses, returning a list of form ['a', 'F', '{', 'a', 'Z', ...],
    i.e. with modifiers (shift, altgr) applied
    :param evts:
    :return:
    """

    # Altgr takes precedence over shift (as per our convention)
    modifiers = [KeyModifier('altgr', [100], altgr_conversion, 0, False),  # 100->'KEY_RIGHTALT'
                 KeyModifier('shift', [42, 54], shift_conversion, 0,
                             False)]  # 42->'KEY_LEFTSHIFT', 54->'KEY_RIGHTSHIFT'
    modifier_codes = {key_code for modifier in modifiers for key_code in modifier.key_codes}
    key_down_evts = []
    for evt in evts:
        categorized = evdev.categorize(evt)
        if isinstance(categorized, evdev.KeyEvent):  # Key
            if categorized.keystate == evdev.KeyEvent.key_down:  # Keydown
                update_modifiers(evt, modifiers, True)
                if evt.code not in modifier_codes:  # Ignore modifier-keys (only apply them to other keys)
                    key_value = keycode_conversion.get(evt.code, evdev.ecodes.keys[evt.code])
                    if isinstance(key_value, list):
                        key_value = apply_multivalue_code_mapping(key_value)
                    if key_value is not None:
                        key_down_evt = apply_modifiers(key_value, evt.timestamp(), modifiers)
                        key_down_evts.append(key_down_evt)
            elif categorized.keystate == evdev.KeyEvent.key_up:  # Keyup
                update_modifiers(evt, modifiers, False)

    return key_down_evts


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def evts_to_frequencies(evts: list[PressedKeyEvt]) -> dict[str, int]:
    """
    :param evts:
    :param multivalue_code_mappings: Maps code name to list of values it maps (would be better the other way around,
    but lists aren't hashable)
    :return:
    """
    frequencies = dict()
    for evt in evts:
        code_name = evt.value
        if isinstance(code_name, list):
            code_name = apply_multivalue_code_mapping(code_name)
        if code_name is not None:
            frequencies[code_name] = frequencies.get(code_name, 0) + 1
    return frequencies


def get_day_evts(path: str, day_timestamp: float) -> list[InputEvent]:
    date = datetime.fromtimestamp(day_timestamp)
    day_date = datetime(date.year, date.month, date.day)
    day_start = day_date.timestamp()
    next_day_start = (day_date + timedelta(days=1)).timestamp()
    return get_events_between(path, day_start, next_day_start, sort=True)


def get_today_evts(path: str) -> list[InputEvent]:
    return get_day_evts(path, time.time())
