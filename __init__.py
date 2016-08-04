from kivy.uix.label import Label
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, DictProperty,\
    StringProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.graphics.vertex_instructions import Quad
from kivy.animation import AnimationTransition
from kivy.compat import string_types
from itertools import chain
from math import pi, cos, sin

try:
    from ttfquery import ttfgroups
    groups = ttfgroups.buildTable()
    # just get a flat list of (font name, path) tupples
    fonts = list(
        chain(*(
            x.values() for x in chain(*(
                x.values() for x in (
                    v for v in groups.values()
                )
            ))
        ))
    )
    font_names = [f[0] for f in fonts]
    font_paths = dict(fonts)

except ImportError:
    print("TTFQuery or fontTools not found, no font selection")
    font_names = []
    font_paths = dict()


# WARNING:: not supported
# - markup
# - ligattures (letters are rendered individually)


class Transformations(object):
    @staticmethod
    def bouncey(points, alpha):
        x = AnimationTransition.out_elastic(alpha)
        x0, y0, x1, y1 = points
        h = (y1 - y0) * x  # tend to correct height, from 0
        w = (x1 - x0) * (2 - x)
        return (
            x0 + w * (1 - alpha*alpha), y0,
            x0 + w * (1 - alpha*alpha) + w, y0,
            x0 + w * (1 - alpha*alpha) + w, y0 + h,
            x0 + w * (1 - alpha*alpha), y0 + h,
        )

    @staticmethod
    def sky_down(points, alpha):
        x = AnimationTransition.out_quad(alpha)
        x0, y0, x1, y1 = points
        h = (y1 - y0) * (4 - 3 * x)  # tend to correct height, from 0
        w = (x1 - x0) * (x)
        cx = (x0 + x1) / 2

        return (
            cx - w * .5, y0,
            cx + w * .5, y0,
            cx + w * .5, y0 + h,
            cx - w * .5, y0 + h,
        )

    @staticmethod
    def pop_in(points, alpha):
        x = AnimationTransition.out_elastic(alpha)
        x0, y0, x1, y1 = points
        h = (y1 - y0) * x  # tend to correct height, from 0
        w = (x1 - x0) * x
        cx = (x0 + x1) / 2

        return (
            cx - w * .5, y0,
            cx + w * .5, y0,
            cx + w * .5, y0 + h,
            cx - w * .5, y0 + h,
        )

    @staticmethod
    def comes_and_go(points, alpha):
        x = AnimationTransition.in_out_quad(alpha)
        x0, y0, x1, y1 = points
        h = (y1 - y0) * (1 - 2 * abs(x - .5))
        center_y = (y0 + y1) / 2

        w = (x1 - x0) * (1 - 2 * abs(x - .5))
        center_x = (x0 + x1) / 2
        return (
            center_x - w / 2, center_y - h / 2,
            center_x + w / 2, center_y - h / 2,
            center_x + w / 2, center_y + h / 2,
            center_x - w / 2, center_y + h / 2
        )

    @staticmethod
    def roll_in(points, alpha):
        x0, y0, x1, y1 = points
        x = AnimationTransition.out_quad(alpha)
        H = (y1 - y0)
        W = (x1 - x0)
        h = H * x
        w = W * x
        h2 = h / 2
        w2 = w / 2
        cx = (x0 + x1) / 2 + H * (1 - x)
        cy = (y0 + y1) / 2 - H * .4 * (1 - x)
        a = pi * x
        pi4 = pi / 4

        return (
            cx + cos(a + 1 * pi4) * w2, cy + sin(a + 1 * pi4) * h2,
            cx + cos(a + 3 * pi4) * w2, cy + sin(a + 3 * pi4) * h2,
            cx + cos(a + 5 * pi4) * w2, cy + sin(a + 5 * pi4) * h2,
            cx + cos(a + 7 * pi4) * w2, cy + sin(a + 7 * pi4) * h2,
        )


class AnimLabel(Label):
    '''duration of the animation of each letter'''
    letter_duration = NumericProperty()

    '''time to wait before starting to animate each letter'''
    letter_offset = NumericProperty()

    '''target text to set to animate'''
    target_text = StringProperty(u'')

    '''this function will get the destination coordinates of the letter,
    and the progress for this letter, must return the current
    coordinates, for a Quad to use
    (x3, y3)---------------(x2, y2)
       |         ____         |
       |       /  __  \       |
       |      /  /__\  \      |
       |     /  ______  \     |
       |    /__/      \__\    |
    (x0, y0)---------------(x1, y1)
    '''
    transform = ObjectProperty(Transformations.bouncey)

    _cache = DictProperty({})
    _time = NumericProperty()

    def on_transform(self, instance, value):
        if isinstance(value, string_types):
            self.transform = getattr(Transformations, value)

    def on_target_text(self, instance, value):
        self.markup = True
        self.text = ''.join(
            u'[ref={}]{}[/ref]'.format(i, l)
            for i, l in enumerate(value)
        )

    def cache_text(self, *args):
        self._cache = {}
        for l in self.target_text:
            if l not in self._cache:
                self._cache[l] = l = Label(
                    text=l,
                    color=self.color,
                    font_size=self.font_size,
                    font_name=self.font_name)

    def on_texture(self, instance, value):
        self.canvas.clear()
        quads = self.quads = []
        self.cache_text()
        with self.canvas:
            for l in self.target_text:
                quads.append(
                    Quad(
                        points=[0, 0, 0, 0, 0, 0, 0, 0],
                        texture=self._cache[l].texture
                        )
                    )

    def tick(self, dt):
        self._time += dt

    def on__time(self, instance, value):
        if not self.texture:
            print("texture not ready")
            return
        elif len(self.refs) != len(self.target_text):
            print("still no refs?")
            return

        offset = self.letter_offset
        duration = self.letter_duration

        for i, l in enumerate(self.target_text):
            a = (value - i * offset) / duration
            a = min(1, max(0, a))
            # ref can contain multiple rects, but we will always have
            # just one, assuming no letter is cut in half
            coords = list(self.refs[str(i)][0])
            coords[0] += self.center_x - self.texture_size[0] / 2
            coords[1] += self.center_y - self.texture_size[1] / 2
            coords[2] += self.center_x - self.texture_size[0] / 2
            coords[3] += self.center_y - self.texture_size[1] / 2

            points = self.transform(coords, a)
            self.quads[i].points = points
            self.quads[i].texture = self._cache[l].texture

        # alhpa for the last letter is 1, we are done
        if a == 1:
            Clock.unschedule(self.tick)

    def animate(self):
        if self.target_text:
            self._time = 0
            Clock.unschedule(self.tick)
            Clock.schedule_interval(self.tick, 0)


KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

BoxLayout:
    orientation: 'vertical'

    AnimLabel:
        id: target
        target_text:
            """some text that will be animated"""
        letter_duration: duration.value
        letter_offset: offset.value
        font_size: font_size.value
        transform: transform.text
        on_transform: self.animate()
        on_font_name: self.animate()

    TextInput:
        multiline: False
        size_hint_y: None
        height: self.minimum_height
        on_text_validate:
            target.target_text = self.text
            target.animate()

    Spinner:
        id: transform
        values: ['sky_down', 'pop_in', 'bouncey', 'comes_and_go', 'roll_in']
        text: 'pop_in'
        size_hint_y: None
        height: self.texture_size[1] + dp(10)

    Spinner:
        id: font
        text: target.font_name
        values: app.fonts
        size_hint_y: None
        height: self.texture_size[1] + dp(10)
        on_text:
            f = app.font_paths.get(self.text)
            if f: target.font_name = f

    GridLayout:
        cols: 3
        Label:
            text: 'letter duration'
        Slider:
            id: duration
            value: 1
            min: 0.01
            max: 10
        Label:
            text: str(duration.value)

        Label:
            text: 'letter time offset'
        Slider:
            id: offset
            value: .1
            min: 0.01
            max: 10
        Label:
            text: str(offset.value)

        Label:
            text: 'font size'
        Slider:
            id: font_size
            value: target.font_size
            value: 50
            min: 5
            max: 100
            step: 1

        Label:
            text: str(target.font_size)

        Label:
            text: 'animation progress'
        Slider:
            id: alpha
            value: target._time
            min: 0
            max: len(target.target_text) * target.letter_offset + target.letter_duration
            on_value:
                target._time = self.value
        Label:
            text: str(alpha.value)

'''  # noqa


class AnimLabelApp(App):
    fonts = ListProperty(font_names)
    font_paths = DictProperty(font_paths)

    def build(self):
        return Builder.load_string(KV)


if __name__ == '__main__':
    AnimLabelApp().run()
