class LetterFrequencies:
    def __init__(self, frequencies: dict[str, int], name: str):
        self.frequencies = frequencies
        self.name = name


letter_frequencies_en = LetterFrequencies(
    {'e': 0.127, 't': 0.091, 'a': 0.082, 'o': 0.075, 'i': 0.07, 'n': 0.067, 's': 0.063, 'h': 0.061,
     'r': 0.06, 'd': 0.043, 'l': 0.04, 'c': 0.028, 'u': 0.028, 'm': 0.024, 'w': 0.024, 'f': 0.022,
     'g': 0.02, 'y': 0.02, 'p': 0.019, 'b': 0.015, 'v': 0.0098, 'k': 0.0077, 'j': 0.0015,
     'x': 0.0015, 'q': 0.00095, 'z': 0.00074}, 'rel. freq. en')
