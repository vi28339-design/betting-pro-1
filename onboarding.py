from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.metrics import dp, sp
from theme_manager import получить_тему, получить_акцент
from ui import Кнопка, FONT_BOLD, FONT_REGULAR

СЛАЙДЫ = [
    {"иконка": "🏒", "заголовок": "Шорт-хоккей",
     "текст": "Добавь команды с их средней результативностью. Модель посчитает вероятности."},
    {"иконка": "⚽", "заголовок": "4 вида спорта",
     "текст": "Хоккей, футбол, теннис, настольный теннис. Каждый — своя модель."},
    {"иконка": "📊", "заголовок": "Веди учёт",
     "текст": "После матча внеси счёт в Историю. Дашборд покажет, работает ли модель."},
]


class Слайд(Screen):
    def __init__(self, данные, индекс, всего, on_next, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = FloatLayout()
        with root.canvas.before:
            Color(*тема["bg"])
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(bg, "pos", root.pos),
                  size=lambda *a: setattr(bg, "size", root.size))
        content = BoxLayout(orientation="vertical", padding=dp(32), spacing=dp(16),
                            size_hint=(1, None), height=dp(440),
                            pos_hint={"center_x": 0.5, "center_y": 0.5})
        content.add_widget(Label(text=данные["иконка"], font_size=sp(72),
                                  size_hint_y=None, height=dp(100)))
        content.add_widget(Label(text=данные["заголовок"], font_name=FONT_BOLD,
                                  font_size=sp(22), color=тема["text"],
                                  size_hint_y=None, height=dp(40), halign="center"))
        text = Label(text=данные["текст"], font_name=FONT_REGULAR, font_size=sp(14),
                     color=тема["muted"], halign="center", valign="top")
        text.bind(size=lambda *a: setattr(text, "text_size", text.size))
        content.add_widget(text)
        content.add_widget(Widget())
        root.add_widget(content)
        dots = BoxLayout(size_hint=(None, None), size=(dp(80), dp(16)),
                         pos_hint={"center_x": 0.5, "y": 0.20}, spacing=dp(8))
        for i in range(всего):
            dot = Widget(size_hint=(None, 1), width=dp(8))
            with dot.canvas:
                Color(*(получить_акцент() if i == индекс else тема["muted"]))
                Ellipse(pos=dot.pos, size=(dp(8), dp(8)))
            dots.add_widget(dot)
        root.add_widget(dots)
        is_last = индекс == всего - 1
        btn = Кнопка("Начать!" if is_last else "Далее", "основная",
                     size_hint=(None, None), size=(dp(260), dp(48)),
                     pos_hint={"center_x": 0.5, "y": 0.08})
        btn.bind(on_press=lambda x: on_next(индекс + 1))
        root.add_widget(btn)
        if not is_last:
            skip = Button(text="Пропустить", font_name=FONT_REGULAR, font_size=sp(12),
                          size_hint=(None, None), size=(dp(120), dp(36)),
                          pos_hint={"right": 0.98, "top": 0.98},
                          background_normal="", background_color=(0, 0, 0, 0),
                          color=тема["muted"])
            skip.bind(on_press=lambda x: on_next(len(СЛАЙДЫ)))
            root.add_widget(skip)
        self.add_widget(root)


class Онбординг(ScreenManager):
    def __init__(self, on_finish, **kw):
        super().__init__(transition=SlideTransition(duration=0.3), **kw)
        self.on_finish = on_finish
        self._показать(0)

    def _показать(self, индекс):
        if индекс >= len(СЛАЙДЫ):
            self.on_finish()
            return
        name = f"слайд_{индекс}"
        if name not in [s.name for s in self.screens]:
            self.add_widget(Слайд(СЛАЙДЫ[индекс], индекс, len(СЛАЙДЫ),
                                    self._показать, name=name))
        self.current = name