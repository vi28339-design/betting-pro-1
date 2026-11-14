import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.text import LabelBase

from theme_manager import получить_тему, получить_акцент, цвет_статуса


def _safe_font(path, default="Roboto"):
    if os.path.exists(path):
        try:
            имя = os.path.basename(path).replace(".ttf", "")
            LabelBase.register(name=имя, fn_regular=path)
            return имя
        except Exception:
            pass
    return default


FONT_REGULAR = _safe_font("static/fonts/Roboto-Regular.ttf")
FONT_BOLD = _safe_font("static/fonts/Roboto-Bold.ttf")
FONT_MEDIUM = _safe_font("static/fonts/Roboto-Medium.ttf")
FONT_ICONS = _safe_font("static/fonts/MaterialIcons-Regular.ttf")
ICONS_OK = FONT_ICONS != "Roboto"


def иконка(символ, эмодзи):
    return символ if ICONS_OK else эмодзи


class Карточка(BoxLayout):
    def __init__(self, заголовок="", иконка_символ="", **kw):
        super().__init__(orientation="vertical", size_hint_y=None,
                         spacing=dp(8), padding=[dp(14), dp(12)], **kw)
        self._заголовок = заголовок
        self._иконка = иконка_символ
        self._высота_зафиксирована = None
        self._пересчёт_активен = False
        тема = получить_тему()
        with self.canvas.before:
            self._border_color = Color(*тема["card_border"])
            self._border = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
            self._bg_color = Color(*тема["card"])
            self._bg = RoundedRectangle(pos=(self.x + dp(1), self.y + dp(1)),
                                        size=(self.width - dp(2), self.height - dp(2)),
                                        radius=[dp(14)])
        self.bind(pos=self._обновить_фон, size=self._обновить_фон)
        if заголовок:
            self.add_widget(self._сделать_заголовок())
        Clock.schedule_once(lambda dt: self._обновить_высоту(), 0.05)

    def _сделать_заголовок(self):
        row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
        if self._иконка:
            ic = Label(text=self._иконка, font_name=FONT_ICONS, font_size=sp(18),
                       size_hint=(None, 1), width=dp(24), color=получить_акцент())
            row.add_widget(ic)
        lbl = Label(text=self._заголовок, font_name=FONT_BOLD, font_size=sp(13),
                    color=получить_тему()["muted"], halign="left", valign="middle")
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
        row.add_widget(lbl)
        return row

    def _обновить_фон(self, *a):
        self._border.pos = self.pos
        self._border.size = self.size
        self._bg.pos = (self.x + dp(1), self.y + dp(1))
        self._bg.size = (self.width - dp(2), self.height - dp(2))

    def _обновить_высоту(self, *a):
        if self._пересчёт_активен:
            return
        if self._высота_зафиксирована is not None:
            self.height = self._высота_зафиксирована
            return
        if self.opacity == 0:
            self.height = 0
            return
        self._пересчёт_активен = True
        try:
            высота = self.padding[1] + self.padding[3]
            for child in self.children:
                высота += child.height if child.size_hint_y is None else dp(50)
                высота += self.spacing
            if self.children:
                высота -= self.spacing
            self.height = max(dp(40), высота)
        finally:
            self._пересчёт_активен = False

    def установить_высоту(self, h):
        self._высота_зафиксирована = h
        self.height = h
        if h == 0:
            self.opacity = 0
            self.disabled = True
        else:
            self.opacity = 1
            self.disabled = False


class Поле(BoxLayout):
    def __init__(self, подпись="", подсказка="", иконка_символ="", **kw):
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(76), spacing=dp(4), **kw)
        тема = получить_тему()
        row = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(6))
        if иконка_символ:
            ic = Label(text=иконка_символ, font_name=FONT_ICONS, font_size=sp(14),
                       size_hint=(None, 1), width=dp(20), color=тема["muted"])
            row.add_widget(ic)
        lbl = Label(text=подпись, font_name=FONT_REGULAR, font_size=sp(12),
                    color=тема["muted"], halign="left", valign="middle")
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
        row.add_widget(lbl)
        self.add_widget(row)
        self._контейнер = FloatLayout(size_hint_y=None, height=dp(46))
        with self._контейнер.canvas.before:
            self._border_color = Color(*тема["input_border"])
            self._border = RoundedRectangle(pos=self._контейнер.pos,
                                              size=self._контейнер.size, radius=[dp(10)])
            self._bg_color = Color(*тема["input_bg"])
            self._bg = RoundedRectangle(
                pos=(self._контейнер.x + dp(2), self._контейнер.y + dp(2)),
                size=(self._контейнер.width - dp(4), self._контейнер.height - dp(4)),
                radius=[dp(9)])
        self.input = TextInput(
            text=подсказка, multiline=False, font_size=sp(15), font_name=FONT_REGULAR,
            background_normal="", background_color=(0, 0, 0, 0),
            foreground_color=тема["text"], cursor_color=получить_акцент(),
            padding=[dp(14), dp(12)], size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.input.bind(focus=self._фокус)
        self._контейнер.add_widget(self.input)
        self.add_widget(self._контейнер)
        self._контейнер.bind(pos=self._обновить_фон, size=self._обновить_фон)

    def _фокус(self, instance, value):
        тема = получить_тему()
        self._border_color.rgba = получить_акцент() if value else тема["input_border"]

    def _обновить_фон(self, *a):
        c = self._контейнер
        self._border.pos = c.pos
        self._border.size = c.size
        self._bg.pos = (c.x + dp(2), c.y + dp(2))
        self._bg.size = (c.width - dp(4), c.height - dp(4))

    @property
    def значение(self):
        return self.input.text.strip()

    def установить(self, текст):
        self.input.text = str(текст)


class Кнопка(Button):
    def __init__(self, текст="", тип="основная", **kw):
        тема = получить_тему()
        акцент = получить_акцент()
        if тип == "основная":
            цвет_фона, цвет_текста = акцент, (1, 1, 1, 1)
        elif тип == "вторичная":
            цвет_фона, цвет_текста = тема["input_bg"], тема["text"]
        elif тип == "опасная":
            цвет_фона, цвет_текста = цвет_статуса("опасность"), (1, 1, 1, 1)
        elif тип == "успех":
            цвет_фона, цвет_текста = цвет_статуса("успех"), (1, 1, 1, 1)
        else:
            цвет_фона, цвет_текста = акцент, (1, 1, 1, 1)
        super().__init__(text=текст, size_hint_y=None, height=dp(48),
                         background_normal="", background_color=цвет_фона,
                         color=цвет_текста, font_name=FONT_BOLD,
                         font_size=sp(14), **kw)
        self.bind(on_press=self._нажатие)

    def _нажатие(self, *a):
        pass  # Вибрация убрана (требует pyjnius)


class ПрогрессБар(Widget):
    значение = NumericProperty(0)
    максимум = NumericProperty(100)

    def __init__(self, значение=0, максимум=100, цвет=None, **kw):
        super().__init__(size_hint_y=None, height=dp(10), **kw)
        self._цвет = цвет or получить_акцент()
        self.значение = значение
        self.максимум = максимум
        self.bind(pos=self._перерисовать, size=self._перерисовать,
                  значение=self._перерисовать)

    def установить(self, знач, animate=True):
        if animate:
            Animation(значение=знач, duration=0.4, t="out_quad").start(self)
        else:
            self.значение = знач

    def _перерисовать(self, *a):
        self.canvas.clear()
        тема = получить_тему()
        доля = min(1, max(0, self.значение / self.максимум)) if self.максимум else 0
        with self.canvas:
            Color(*тема["card_border"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
            if доля > 0:
                Color(*self._цвет)
                RoundedRectangle(pos=self.pos,
                                 size=(self.width * доля, self.height),
                                 radius=[dp(5)])
        if self.pos == (0, 0):
            Clock.schedule_once(lambda dt: self._перерисовать(), 0.1)


class ПустоеСостояние(FloatLayout):
    def __init__(self, иконка_текст="📭", заголовок="Нет данных", подзаголовок="",
                 кнопка_текст="", on_кнопка=None, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        content = BoxLayout(orientation="vertical", spacing=dp(10),
                            size_hint=(1, None), height=dp(280),
                            pos_hint={"center_y": 0.5})
        content.add_widget(Label(text=иконка_текст, font_size=sp(56),
                                  size_hint_y=None, height=dp(80), color=тема["muted"]))
        content.add_widget(Label(text=заголовок, font_name=FONT_BOLD, font_size=sp(18),
                                  color=тема["text"], size_hint_y=None, height=dp(32),
                                  halign="center"))
        if подзаголовок:
            sub = Label(text=подзаголовок, font_name=FONT_REGULAR, font_size=sp(13),
                        color=тема["muted"], size_hint_y=None, height=dp(60),
                        halign="center", valign="top")
            sub.bind(size=lambda *a: setattr(sub, "text_size", sub.size))
            content.add_widget(sub)
        content.add_widget(Widget())
        if кнопка_текст and on_кнопка:
            holder = FloatLayout(size_hint_y=None, height=dp(50))
            b = Кнопка(кнопка_текст, "основная", size_hint=(None, None),
                       size=(dp(220), dp(46)),
                       pos_hint={"center_x": 0.5, "center_y": 0.5})
            b.bind(on_press=on_кнопка)
            holder.add_widget(b)
            content.add_widget(holder)
        self.add_widget(content)


class _ТостPopup(ModalView):
    def __init__(self, текст, цвет, цвет_текста, **kw):
        super().__init__(size_hint=(0.85, None), height=dp(56),
                         background_color=(0, 0, 0, 0), background="",
                         auto_dismiss=False, **kw)
        content = BoxLayout(padding=dp(12))
        with content.canvas.before:
            Color(*цвет)
            bg = RoundedRectangle(pos=content.pos, size=content.size, radius=[dp(12)])
        content.bind(pos=lambda *a: setattr(bg, "pos", content.pos),
                     size=lambda *a: setattr(bg, "size", content.size))
        lbl = Label(text=текст, font_name=FONT_MEDIUM, font_size=sp(13),
                    color=цвет_текста, halign="center", valign="middle")
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
        content.add_widget(lbl)
        self.add_widget(content)


class Тосты:
    _текущий = None

    @classmethod
    def показать(cls, текст, тип="нейтральный", длительность=2.5):
        try:
            if cls._текущий:
                cls._текущий.dismiss()
        except Exception:
            pass
        тема = получить_тему()
        if тип == "нейтральный":
            цвет, цвет_текста = тема["card"], тема["text"]
        else:
            цвет, цвет_текста = цвет_статуса(тип), (1, 1, 1, 1)
        popup = _ТостPopup(текст, цвет, цвет_текста)
        popup.open()
        cls._текущий = popup
        Clock.schedule_once(lambda dt: cls._закрыть(popup), длительность)

    @classmethod
    def _закрыть(cls, popup):
        try:
            popup.dismiss()
            if cls._текущий is popup:
                cls._текущий = None
        except Exception:
            pass


class Метрика(BoxLayout):
    def __init__(self, значение="", подпись="", цвет=None, **kw):
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(72), spacing=dp(2), **kw)
        тема = получить_тему()
        цвет = цвет or тема["text"]
        val = Label(text=str(значение), font_name=FONT_BOLD, font_size=sp(22),
                    color=цвет, halign="center", size_hint_y=None, height=dp(36))
        val.bind(size=lambda *a: setattr(val, "text_size", val.size))
        self.add_widget(val)
        lbl = Label(text=подпись, font_name=FONT_REGULAR, font_size=sp(11),
                    color=тема["muted"], halign="center", size_hint_y=None, height=dp(20))
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
        self.add_widget(lbl)
