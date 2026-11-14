from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp


def пульсировать(widget):
    widget._пульсация = True
    def шаг(dt):
        if not getattr(widget, "_пульсация", False):
            return False
        Animation(opacity=0.55, duration=0.4).start(widget)
        Clock.schedule_once(
            lambda d: Animation(opacity=1.0, duration=0.4).start(widget), 0.4)
        return True
    Clock.schedule_interval(шаг, 0.8)


def остановить_пульсацию(widget):
    widget._пульсация = False
    widget.opacity = 1.0


def появление(widget, duration=0.3):
    widget.opacity = 0
    Animation(opacity=1, duration=duration).start(widget)


def тряхнуть(widget):
    x = widget.x
    (Animation(x=x + dp(8), duration=0.05) +
     Animation(x=x - dp(8), duration=0.05) +
     Animation(x=x, duration=0.05)).start(widget)