import math
import sys
import os
from dotenv import load_dotenv
from evt_processing import get_today_evts, get_events_between, filter_key_down_evts_apply_modifiers, evts_to_frequencies
from plotting import plot_evts_by_hour_minute, plot_key_frequencies

load_dotenv()
INPUT_EVENTS_PATH = os.getenv('INPUT_EVENTS_PATH')

todays_evts = get_today_evts(INPUT_EVENTS_PATH)
all_evts = get_events_between(INPUT_EVENTS_PATH, 0)
evts = filter_key_down_evts_apply_modifiers(all_evts)
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

plot_evts_by_hour_minute(evts)
plot_key_frequencies(key_frequencies)
