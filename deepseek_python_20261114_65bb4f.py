import os
import csv
import threading
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.animation import Animation

from database import db
from model import (
    predict_hockey, poisson_over, kelly_stake, edge,
    validate_input, elo_update, elo_boost,
    calibrate_probability, remove_margin,
    odds_divergence, интерпретация_расхождения,
)
from sports_models import универсальный_прогноз
from analytics import (
    собрать_статистику, монте_карло,
    статистика_по_стратегиям, статистика_по_расхождению,
)
from chart import ГрафикБанка
from notifications import share_text
from theme_manager import получить_тему, получить_акцент, цвет_статуса
from ui import (
    Карточка, Поле, Кнопка, Тосты, ПустоеСостояние,
    Метрика, ПрогрессБар,
    FONT_REGULAR, FONT_BOLD, FONT_MEDIUM, FONT_ICONS, ICONS_OK, иконка,
)
from animations import пульсировать, остановить_пульсацию, появление
from onboarding import Онбординг
from strategies import автоматический_анализ

Window.clearcolor = получить_тему()["bg"]


def диалог(заголовок, текст):
    тема = получить_тему()
    p = Popup(title=заголовок,
              content=Label(text=текст, font_name=FONT_REGULAR,
                            font_size=sp(13), color=тема["text"]),
              size_hint=(0.9, 0.4))
    p.open()


class ЭкранПрогноза(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        title = Label(text="Прогноз", font_name=FONT_BOLD, font_size=sp(24),
                      color=тема["text"], halign="left", valign="middle")
        title.bind(size=lambda *a: setattr(title, "text_size", title.size))
        header.add_widget(title)
        header.add_widget(Widget())
        root.add_widget(header)

        scroll = ScrollView()
        self.форма = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        self.форма.bind(minimum_height=self.форма.setter("height"))

        карт1 = Карточка("Участники", иконка("\ue7fb", "👥"))
        self.sp_спорт = Spinner(
            text=db.get_setting("sport_default", "шорт-хоккей"),
            values=["шорт-хоккей", "футбол", "теннис", "настольный теннис"],
            size_hint_y=None, height=dp(44), background_normal="",
            background_color=тема["input_bg"], color=тема["text"])
        self.sp_спорт.bind(text=self._сменить_спорт)
        карт1.add_widget(self.sp_спорт)
        self.sp_к1 = self._спиннер()
        self.sp_к2 = self._спиннер()
        карт1.add_widget(self.sp_к1)
        карт1.add_widget(self.sp_к2)
        self.форма.add_widget(карт1)

        self.карт_голы = Карточка("Статистика", иконка("\ue85b", "📊"))
        self.ф_к1з = Поле("К1 — заброшенных", "5.2")
        self.ф_к1п = Поле("К1 — пропущенных", "4.1")
        self.ф_к2з = Поле("К2 — заброшенных", "4.8")
        self.ф_к2п = Поле("К2 — пропущенных", "4.5")
        self.ф_дом = Поле("Домашнее преимущество", "1.05")
        for f in (self.ф_к1з, self.ф_к1п, self.ф_к2з, self.ф_к2п, self.ф_дом):
            self.карт_голы.add_widget(f)
        self.форма.add_widget(self.карт_голы)

        self.карт_эло = Карточка("Игроки (Elo)", иконка("\ue7ee", "🎾"))
        self.ф_игрок1 = Поле("Игрок 1", "")
        self.ф_эло1 = Поле("Elo игрока 1", "2000")
        self.ф_игрок2 = Поле("Игрок 2", "")
        self.ф_эло2 = Поле("Elo игрока 2", "1950")
        for f in (self.ф_игрок1, self.ф_эло1, self.ф_игрок2, self.ф_эло2):
            self.карт_эло.add_widget(f)
        self.карт_эло.opacity = 0
        self.карт_эло.установить_высоту(0)
        self.форма.add_widget(self.карт_эло)

        self.карт_ставка = Карточка("Ставка", иконка("\ue227", "💰"))
        self.ф_линия = Поле("Линия тотала", "9.5")
        self.ф_кэф_тб = Поле("Кэф на ТБ", "1.85")
        self.ф_кэф_тм = Поле("Кэф на ТМ", "1.95")
        for f in (self.ф_линия, self.ф_кэф_тб, self.ф_кэф_тм):
            self.карт_ставка.add_widget(f)
        self.форма.add_widget(self.карт_ставка)

        карт5 = Карточка("Дополнительно", иконка("\ue8b8", "⚙️"))
        self.ф_кэф_п1 = Поле("Кэф на П1", "1.85")
        self.ф_кэф_п2 = Поле("Кэф на П2", "1.95")
        self.ф_банк = Поле("Банк", "10000")
        self.ф_время = Поле("Время матча (YYYY-MM-DD HH:MM)", "")
        self.ф_заметка = Поле("Заметка", "")
        for f in (self.ф_кэф_п1, self.ф_кэф_п2, self.ф_банк,
                  self.ф_время, self.ф_заметка):
            карт5.add_widget(f)
        self.форма.add_widget(карт5)

        self.карт_результат = Карточка("", "")
        self.карт_результат.opacity = 0
        self.карт_результат.установить_высоту(0)

        self.рекомендация_большая = Label(
            text="", font_name=FONT_BOLD, font_size=sp(32),
            color=цвет_статуса("успех"),
            size_hint_y=None, height=dp(50), halign="center")
        self.рекомендация_большая.bind(
            size=lambda *a: setattr(self.рекомендация_большая, "text_size",
                                    self.рекомендация_большая.size))
        self.карт_результат.add_widget(self.рекомендация_большая)

        self.вероятность = Label(text="", font_name=FONT_MEDIUM, font_size=sp(20),
                                  color=тема["muted"], size_hint_y=None,
                                  height=dp(30), halign="center")
        self.карт_результат.add_widget(self.вероятность)

        self.прогресс = ПрогрессБар(значение=0)
        self.карт_результат.add_widget(self.прогресс)

        self.текст_ставки = Label(text="", font_name=FONT_MEDIUM, font_size=sp(14),
                                   color=тема["text"], size_hint_y=None,
                                   height=dp(28), halign="center", markup=True)
        self.текст_ставки.bind(size=lambda *a: setattr(
            self.текст_ставки, "text_size", self.текст_ставки.size))
        self.карт_результат.add_widget(self.текст_ставки)

        self.кнопка_подробнее = Button(
            text="▼ Подробнее", font_name=FONT_MEDIUM, font_size=sp(12),
            size_hint_y=None, height=dp(32), background_normal="",
            background_color=(0, 0, 0, 0), color=получить_акцент())
        self.кнопка_подробнее.bind(on_press=self._переключить_детали)
        self.карт_результат.add_widget(self.кнопка_подробнее)

        self.детали = Label(text="", font_name=FONT_REGULAR, font_size=sp(12),
                            color=тема["muted"], size_hint_y=None, height=0,
                            halign="left", valign="top", markup=True)
        self.детали.bind(size=lambda *a: setattr(
            self.детали, "text_size", self.детали.size))
        self.карт_результат.add_widget(self.детали)

        self.форма.add_widget(self.карт_результат)
        scroll.add_widget(self.форма)
        root.add_widget(scroll)

        ряд = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        b1 = Кнопка("🎯 Анализ", "основная")
        b1.bind(on_press=self.анализ)
        ряд.add_widget(b1)
        b_auto = Кнопка("⚡ Авто", "успех", size_hint=(None, 1), width=dp(80))
        b_auto.bind(on_press=self.автоанализ)
        ряд.add_widget(b_auto)
        b3 = Кнопка("📤", "вторичная", size_hint=(None, 1), width=dp(52))
        b3.bind(on_press=self.поделиться)
        ряд.add_widget(b3)
        root.add_widget(ряд)

        self._детали_развёрнуты = False
        self._последний_прогноз = ""
        self.add_widget(root)
        self._сменить_спорт(self.sp_спорт, self.sp_спорт.text)

    def _спиннер(self):
        тема = получить_тему()
        команды = ["—"] + [t[0] for t in db.all_teams("шорт-хоккей")]
        sp = Spinner(text="—", values=команды, size_hint_y=None, height=dp(44),
                     background_normal="", background_color=тема["input_bg"],
                     color=тема["text"])
        sp.bind(text=self._выбор_команды)
        return sp

    def _сменить_спорт(self, spinner, спорт):
        db.set_setting("sport_default", спорт)
        команды = ["—"] + [t[0] for t in db.all_teams(спорт)]
        self.sp_к1.values = команды
        self.sp_к2.values = команды
        if спорт in ("шорт-хоккей", "футбол"):
            self.карт_голы.opacity = 1
            self.карт_голы._обновить_высоту()
            self.карт_эло.opacity = 0
            self.карт_эло.установить_высоту(0)
            self.карт_ставка.opacity = 1
            self.карт_ставка._обновить_высоту()
            self.ф_линия.установить("9.5" if спорт == "шорт-хоккей" else "2.5")
        else:
            self.карт_голы.opacity = 0
            self.карт_голы.установить_высоту(0)
            self.карт_эло.opacity = 1
            self.карт_эло._обновить_высоту()
            self.карт_ставка.opacity = 0.4
            self.карт_ставка._обновить_высоту()

    def _выбор_команды(self, spinner, text):
        if not text or text == "—":
            return
        спорт = self.sp_спорт.text
        t = db.get_team(text, спорт)
        if not t:
            return
        if спорт in ("шорт-хоккей", "футбол"):
            if spinner is self.sp_к1:
                self.ф_к1з.установить(f"{t['scored']:.2f}")
                self.ф_к1п.установить(f"{t['conceded']:.2f}")
            elif spinner is self.sp_к2:
                self.ф_к2з.установить(f"{t['scored']:.2f}")
                self.ф_к2п.установить(f"{t['conceded']:.2f}")
        else:
            if spinner is self.sp_к1:
                self.ф_игрок1.установить(text)
                self.ф_эло1.установить(f"{t['elo']:.0f}")
            elif spinner is self.sp_к2:
                self.ф_игрок2.установить(text)
                self.ф_эло2.установить(f"{t['elo']:.0f}")

    def _переключить_детали(self, *a):
        self._детали_развёрнуты = not self._детали_развёрнуты
        if self._детали_развёрнуты:
            Animation(height=dp(220), duration=0.25).start(self.детали)
            self.кнопка_подробнее.text = "▲ Свернуть"
        else:
            Animation(height=0, duration=0.25).start(self.детали)
            self.кнопка_подробнее.text = "▼ Подробнее"
        Clock.schedule_once(lambda dt: self.карт_результат._обновить_высоту(), 0.3)

    def _собрать_значения(self):
        спорт = self.sp_спорт.text
        if спорт in ("шорт-хоккей", "футбол"):
            значения = {"к1з": float(self.ф_к1з.значение),
                        "к1п": float(self.ф_к1п.значение),
                        "к2з": float(self.ф_к2з.значение),
                        "к2п": float(self.ф_к2п.значение),
                        "дом": float(self.ф_дом.значение or 1.0)}
            if спорт == "шорт-хоккей":
                t1 = db.get_team(self.sp_к1.text, спорт) or {"form": "", "elo": 1500}
                t2 = db.get_team(self.sp_к2.text, спорт) or {"form": "", "elo": 1500}
                значения["форма1"] = t1["form"]
                значения["форма2"] = t2["form"]
                значения["elo_boost"] = elo_boost(t1["elo"], t2["elo"])
            return спорт, значения
        else:
            значения = {"elo1": float(self.ф_эло1.значение),
                        "elo2": float(self.ф_эло2.значение)}
            return спорт, значения

    def _собрать_кэфы(self):
        try:
            return {"п1": float(self.ф_кэф_п1.значение or 0),
                    "п2": float(self.ф_кэф_п2.значение or 0),
                    "тб": float(self.ф_кэф_тб.значение or 0),
                    "тм": float(self.ф_кэф_тм.значение or 0)}
        except ValueError:
            return {"п1": 0, "п2": 0, "тб": 0, "тм": 0}