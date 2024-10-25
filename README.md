I spend a lot of time in front of a computer, doing very important stuff [reference] (like writing questionable code -
link to image displaying some sort of programming-crime I have commited, perhaps in this very project?). A substantial
share of that time is devoted to thinking about what to type, and a little less is then spent actually typing it.
However, I have to wonder: How much information do I actually produce?

TODO: Introduce Entropy

First we have to define the possible events we are looking at.
To get a baseline, we can consider all input events which
are  [mapped by the Linux kernel](https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h).
For our purposes we'll use the evdev python library, which among other things exposes these integer constants.

However, we are quick to start suspecting that

```python
import evdev

print(len(evdev.ecodes.keys))  # 596
```

596 (!) possible input events exceeds the number of keys on my laptop keyboard by a fair bit (it's got 81 in case you're
wondering, and even my external full-size one doesn't sport more than 109). Granted, some of these (looking at the
function keys) can cause different events, but even if we're being generous here, the number of keys we are nowhere near
almost 600. Turns out this has a good reason:
Here are some of my favorites (some are mapped to multiple values):

- 209: KEY_BASSBOOST
- 152: [KEY_COFFEE, KEY_SCREENLOCK]
- 85: KEY_ZENKAKUHANKAKU (according to
  a [quick search](https://sqa.stackexchange.com/questions/7929/what-is-keys-zenkaku-hankaku-in-webdriver), this
  Japanese modifier key will switch between half- (Hankaku) and full-width (Zenkaku))
- along with [BTN_TRIGGER_HAPPY1 up to BTN_TRIGGER_HAPPY40](https://anvilproject.org/guides/content/creating-links)

It doesn't make sense to include events which I physically won't be able to trigger. Instead, as a crude first measure I
simply pressed every key (you can find a list [here], it consists of 83 elements - remember the function keys) and will
for now work with whatever keys for which there are events in the file from which I'll read them. This means that we
won't be getting any keys pressed 0 times, which will even simplify the calculations later on a tad bit.

```python
# convert event numbers to "names"
import evdev

l = ['KEY_0', 'KEY_1', ..., 'KEY_Y', 'KEY_Z']
l.sort(key=lambda x: evdev.ecodes.ecodes[x])
for elem in l:
    print(f'{evdev.ecodes.ecodes[elem]}: \'{elem[4:].lower()}\',')  # 1: 'esc', 2: '1', ... , 125: 'leftmeta', 140: 'calc'
```
