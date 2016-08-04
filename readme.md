AnimLabel
=========

`AnimLabel` is a Label derivative class, that adds letter-wise animations to the
target text. It allows writing and passing custom functions to transform each
letter at each instant of the animation.

The module can be ran standalone to demonstrate the capabilities:

```
python __init__.py
```


To use in your own modules, you must import `AnimLabel,` and use it, setting
`target_text` instead of the normal `text` property (which is managed by the
class itself). You can set the `transform` property either to the name of
a method of the `Transformations` class, or to one of your custom functions.
Start the animation using the `animate` method of the `AnimLabel`.

Not all features of Label will work, since the `AnimLabel` splits by letter,
and use markup to get letters positions, it's not possible for the
`target_text` to use markup. Fonts with ligatures will not be able to use them,
as each letter is rendered individually.

Tweaking the animation is possible using the `letter_duration` and
`letter_offset` properties, which describe respectively the duration of the
animation for each letter, and the time between starting the animation for each
letter.

Here is a simple example:

```python
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.garden.animlabel import AnimLabel  # noqa

KV = '''
BoxLayout:
    AnimLabel:
        id: label
        target_text: 'this is some text'
        transform: 'sky_down'
        letter_duration: 1
        letter_offset: .5

    Button:
        text: 'animate'
        on_press: label.animate()
'''

runTouchApp(Builder.load_string(KV))
```

A custom transform function must have the following form:

```python
def my_transform((x0, y0, x1, y1), progress):
    # x0, y0 and x1, y1 are the bottom left and top right corners of the
    # original position.
    # we return position of the 4 corners of the quad that displays the letter
    # this example is noop, just translates the coordinates we got into the
    # quad format
    return (
        x0, y0,
        x1, y0,
        x1, y1,
        x0, y1
    )
```
