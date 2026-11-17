import datetime
import math
import os
import sqlite3

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.utils import rgba

MARGIN = dp(16)
G_8, G_12, G_16 = dp(8), dp(12), dp(16)
R_CARD = dp(16)
TOUCH = dp(48)

FONT_REG = "Roboto"
FONT_BOLD = "Roboto"

THEMES = {
    "light": {
        "bg": rgba("#F2F2F7"), "card": rgba("#FFFFFF"), "field": rgba("#FFFFFF"),
        "separator": rgba(0.78, 0.78, 0.80, 1), "accent": rgba("#007AFF"),
        "label": rgba("#1C1C1E"), "secondary": rgba("#8E8E93"),
        "tabtext": rgba("#8E8E93"), "tabactive": rgba("#007AFF"),
        "green": rgba("#34C759"), "red": rgba("#FF3B30"),
    },
    "dark": {
        "bg": rgba("#000000"), "card": rgba("#1C1C1E"), "field": rgba("#2C2C2E"),
        "separator": rgba("#38383A"), "accent": rgba("#0A84FF"),
        "label": rgba("#FFFFFF"), "secondary": rgba("#8E8E93"),
        "tabtext": rgba("#8E8E93"), "tabactive": rgba("#0A84FF"),
        "green": rgba("#30D158"), "red": rgba("#FF453A"),
    },
}

SPORTS = ["Хоккей", "Футбол", "Теннис", "Настольный теннис"]
STRATEGIES = ["Тотал ТБ", "Тотал ТМ", "Двойной шанс 1X", "Двойной шанс X2",
              "Победа фаворита", "Value (EV)", "Келли-критерий", "Обе забьют"]

DB_PATH = "betting.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    c = get_db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sport TEXT, strategy TEXT, line REAL, cf REAL,
      prob REAL, ev REAL, stake REAL,
      result TEXT, created TEXT
    );""")
    c.commit(); c.close()


def save_bet(sport, strategy, line, cf, prob, ev, stake):
    c = get_db()
    c.execute("INSERT INTO history (sport,strategy,line,cf,prob,ev,stake,result,created) "
              "VALUES (?,?,?,?,?,?,?,?,?)",
              (sport, strategy, line, cf, prob, ev, stake, None,
               datetime.datetime.now().strftime("%d.%m %H:%M")))
    c.commit(); c.close()


def get_history(limit=200):
    c = get_db()
    rows = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return rows


def set_result(bid, result):
    c = get_db()
    c.execute("UPDATE history SET result=? WHERE id=?", (result, bid))
    c.commit(); c.close()


def clear_history():
    c = get_db()
    c.execute("DELETE FROM history")
    c.commit(); c.close()


class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(padding=[MARGIN, G_16, MARGIN, G_16], spacing=G_8, **kw)
        self.theme = "light"
        with self.canvas.before:
            Color(*THEMES[self.theme]["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_theme(self, name):
        self.theme = name
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEMES[name]["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)


class Field(BoxLayout):
    def __init__(self, label, placeholder, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        self.theme = "light"
        self.cap = Label(text=label, font_size=sp(14), halign="left", size_hint_y=None, height=sp(18))
        self.cap.bind(size=lambda *a: setattr(self.cap, "text_size", (self.cap.width, None)))
        self.txt = TextInput(text="", hint_text=placeholder, multiline=False, font_size=sp(16),
                             padding=[G_12, G_12], height=TOUCH, size_hint_y=None,
                             background_color=(1, 1, 1, 1), background_normal="")
        self.add_widget(self.cap)
        self.add_widget(self.txt)
        self.set_theme("light")

    def set_theme(self, name):
        self.theme = name
        c = THEMES[name]
        self.cap.color = c["secondary"]
        self.txt.color = c["label"]
        self.txt.hint_text_color = c["secondary"]
        self.txt.background_color = [v for v in c["field"]][:3] + [1]


class MainScreen(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        self.theme = "light"
        self.tabs = {}

        header = BoxLayout(size_hint_y=None, height=dp(52), padding=[MARGIN, 0, G_16, 0])
        self.large_title = Label(text="Ставки", font_size=sp(32), bold=True, halign="left", size_hint_x=1)
        self.large_title.bind(size=lambda *a: setattr(self.large_title, "text_size", (self.large_title.width, None)))
        self.theme_switch = Switch(active=False, size_hint=(None, None), size=(dp(51), dp(31)))
        self.theme_switch.bind(active=self.on_theme)
        header.add_widget(self.large_title)
        header.add_widget(self.theme_switch)
        self.add_widget(header)

        self.panel_analyze = BoxLayout(orientation="vertical", padding=[0, 0, 0, 0])
        self.panel_history = BoxLayout(orientation="vertical", padding=[0, 0, 0, 0], opacity=0, disabled=True)
        self.panel_stats = BoxLayout(orientation="vertical", padding=[0, 0, 0, 0], opacity=0, disabled=True)

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=G_16, padding=[0, 0, 0, G_16])
        content.bind(minimum_height=content.setter("height"))

        card_sel = Card(orientation="vertical")
        card_sel.add_widget(self._sec("Настройки"))
        row = BoxLayout(size_hint_y=None, height=TOUCH, spacing=G_12)
        self.sport = self._spin(SPORTS)
        self.strategy = self._spin(STRATEGIES)
        self.sport.bind(text=self.on_sport_change)
        row.add_widget(self.sport)
        row.add_widget(self.strategy)
        card_sel.add_widget(row)
        content.add_widget(card_sel)

        card_f = Card(orientation="vertical")
        card_f.add_widget(self._sec("Параметры"))
        self.f_k1 = Field("Команда 1: очки/забитые", "5.2")
        self.f_k2 = Field("Команда 2: очки/забитые", "4.8")
        self.f_line = Field("Линия / гандикап", "9.5")
        self.f_cf = Field("Коэффициент БК", "1.90")
        for f in (self.f_k1, self.f_k2, self.f_line, self.f_cf):
            card_f.add_widget(f)
        content.add_widget(card_f)

        self.analyze_btn = Button(text="Анализировать и сохранить", font_size=sp(16), bold=True,
                                  size_hint_y=None, height=TOUCH, background_normal="",
                                  background_color=THEMES[self.theme]["accent"], color=(1, 1, 1, 1))
        self.analyze_btn.bind(on_press=self.calculate)
        content.add_widget(self.analyze_btn)

        self.result_card = Card(orientation="vertical")
        self.result = Label(text="Готов к анализу.", font_size=sp(16), halign="center",
                            valign="middle", size_hint_y=None, height=dp(140))
        self.result.bind(size=lambda *a: setattr(self.result, "text_size", (self.result.width, None)))
        self.result_card.add_widget(self.result)
        content.add_widget(self.result_card)

        scroll.add_widget(content)
        self.panel_analyze.add_widget(scroll)

        self.hist_scroll = ScrollView(size_hint=(1, 1))
        self.hist_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self.hist_list.bind(minimum_height=self.hist_list.setter("height"))
        self.hist_scroll.add_widget(self.hist_list)
        self.panel_history.add_widget(self.hist_scroll)

        self.stats_scroll = ScrollView(size_hint=(1, 1))
        self.stats_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=G_8, padding=[MARGIN, G_8, MARGIN, G_8])
        self.stats_list.bind(minimum_height=self.stats_list.setter("height"))
        self.clear_btn = Button(text="Очистить историю", font_size=sp(15), bold=True,
                                size_hint_y=None, height=TOUCH*0.9, background_normal="",
                                background_color=THEMES[self.theme]["red"], color=(1, 1, 1, 1))
        self.clear_btn.bind(on_press=self.clear_all)
        self.stats_list.add_widget(self.clear_btn)
        self.stats_scroll.add_widget(self.stats_list)
        self.panel_stats.add_widget(self.stats_scroll)

        for p in (self.panel_analyze, self.panel_history, self.panel_stats):
            self.add_widget(p)

        bar = BoxLayout(size_hint_y=None, height=dp(52))
        self.tabbar = bar
        for n in ("Анализ", "История", "Статистика"):
            b = Button(text=n, font_size=sp(11), size_hint_x=1, background_normal="")
            b.bind(on_press=self.on_tab)
            self.tabs[n] = b
            bar.add_widget(b)
        self.add_widget(bar)

        self.set_theme("light")
        self.on_tab(self.tabs["Анализ"])

    def _sec(self, text):
        l = Label(text=text, font_size=sp(13), bold=True, halign="left", size_hint_y=None, height=sp(18))
        l.bind(size=lambda *a: setattr(l, "text_size", (l.width, None)))
        return l

    def _spin(self, values):
        return Spinner(text=values[0], values=values, font_size=sp(16), size_hint_x=1,
                       size_hint_y=None, height=TOUCH, background_color=(1, 1, 1, 1))

    def on_tab(self, btn):
        name = btn.text
        order = {"Анализ": self.panel_analyze, "История": self.panel_history, "Статистика": self.panel_stats}
        for n, p in order.items():
            p.opacity = 1 if n == name else 0
            p.disabled = n != name
        if name == "История":
            self.render_history()
        elif name == "Статистика":
            self.render_stats()
        self._style_tabbar(self.theme, name)

    def on_theme(self, sw, val):
        self.set_theme("dark" if val else "light")

    def set_theme(self, name):
        self.theme = name
        c = THEMES[name]
        Window.clearcolor = c["bg"]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*c["bg"])
            Rectangle(pos=self.pos, size=self.size)
        self.large_title.color = c["label"]
        for f in (self.f_k1, self.f_k2, self.f_line, self.f_cf):
            f.set_theme(name)
        self.result_card.set_theme(name)
        self.result.color = c["label"]
        self.analyze_btn.background_color = c["accent"]
        self.clear_btn.background_color = c["red"]
        for sp_ in (self.sport, self.strategy):
            sp_.color = c["label"]
            sp_.background_color = [v for v in c["field"]][:3] + [1]
        self._style_tabbar(name, "Анализ")

    def _style_tabbar(self, name, active):
        c = THEMES[name]
        self.tabbar.canvas.before.clear()
        with self.tabbar.canvas.before:
            Color(*c["card"])
            Rectangle(pos=self.tabbar.pos, size=self.tabbar.size)
            Color(*c["separator"])
            Line(points=[self.tabbar.x, self.tabbar.y + self.tabbar.height,
                         self.tabbar.right, self.tabbar.y + self.tabbar.height], width=dp(0.7))
        for tn, b in self.tabs.items():
            b.color = c["tabactive"] if tn == active else c["tabtext"]

    def on_sport_change(self, sp_, val):
        self.f_line.txt.hint_text = "Тотал партий (2.5)" if val in ("Теннис", "Настольный теннис") else "Линия тотала (9.5)"

    def _num(self, txt):
        try:
            return float((txt or "0").strip().replace(",", "."))
        except Exception:
            return 0.0

    def model(self, sport, a, b, line):
        if sport in ("Хоккей", "Футбол"):
            a = max(a, 0.1); b = max(b, 0.1)
            p1 = px = p2 = 0.0
            for g1 in range(16):
                for g2 in range(16):
                    p = poisson(g1, a) * poisson(g2, b)
                    if g1 > g2: p1 += p
                    elif g1 == g2: px += p
                    else: p2 += p
            total = a + b
            th = int(math.ceil(line))
            p_over = 1 - sum(poisson(k, total) for k in range(max(th, 1)))
            return {"p1": p1, "px": px, "p2": p2, "over": p_over, "under": 1 - p_over, "total": total}
        else:
            a = max(a, 0.1); b = max(b, 0.1)
            tot = a + b
            p1 = a / tot * 0.9; p2 = b / tot * 0.9; px = 1 - p1 - p2
            return {"p1": p1, "px": px, "p2": p2, "over": 0, "under": 0, "total": a + b}

    def calculate(self, inst):
        try:
            sport = self.sport.text
            strategy = self.strategy.text
            a = self._num(self.f_k1.txt.text)
            b = self._num(self.f_k2.txt.text)
            line = self._num(self.f_line.txt.text)
            cf = self._num(self.f_cf.txt.text)
            m = self.model(sport, a, b, line)
            p1, px, p2 = m["p1"], m["px"], m["p2"]

            if strategy in ("Тотал ТБ", "Тотал ТМ"):
                th = int(math.ceil(line))
                p_over = 1 - sum(poisson(k, m["total"]) for k in range(max(th, 1)))
                rec = "ТБ {}".format(line)
                prob = p_over if strategy == "Тотал ТБ" else 1 - p_over
            elif strategy == "Двойной шанс 1X":
                rec, prob = "1X", p1 + px
            elif strategy == "Двойной шанс X2":
                rec, prob = "X2", px + p2
            elif strategy == "Победа фаворита":
                rec = "К1" if p1 >= p2 else "К2"
                prob = max(p1, p2)
            elif strategy == "Обе забьют":
                prob = 1 - (poisson(0, max(a, 0.1)) * poisson(0, max(b, 0.1)))
                rec = "Обе забьют"
            elif strategy in ("Value (EV)", "Келли-критерий"):
                probs = [p1, px, p2]
                best = max(probs)
                rec = ["К1", "X", "К2"][probs.index(best)]
                prob = best
            else:
                rec, prob = "К1", p1

            ev = prob * cf - 1
            implied = 1 / cf if cf > 1 else 0
            stake = self.stake_for(prob, cf) if strategy == "Келли-критерий" else 0.0

            if prob > implied + 0.03:
                verdict = "🔥 Value — ставить"
                vcolor = THEMES[self.theme]["green"]
            elif prob < implied - 0.03:
                verdict = "❌ Нет value — пропустить"
                vcolor = THEMES[self.theme]["red"]
            else:
                verdict = "⚠️ На границе"
                vcolor = THEMES[self.theme]["secondary"]

            save_bet(sport, strategy, line, cf, prob, ev, stake)

            lines = ["🎯 {} — {}".format(rec, strategy),
                     "Вероятность прохода: {:.0f}%".format(prob * 100),
                     "Коэффициент {:.2f} (БК: {:.0f}%)".format(cf, implied * 100),
                     "EV: {:.3f}".format(ev),
                     verdict]
            if stake > 0:
                lines.append("Ставка: {:.0f} руб".format(stake))
            lines.append("П1 {:.0f}%  X {:.0f}%  П2 {:.0f}%".format(p1 * 100, px * 100, p2 * 100))
            self.result.text = "\n".join(lines)
            self.result.color = vcolor
        except Exception:
            self.result.text = "Ошибка ввода! Проверьте числа."
            self.result.color = THEMES[self.theme]["red"]

    def stake_for(self, prob, cf):
        if cf <= 1:
            return 0.0
        f = (prob * cf - 1) / (cf - 1)
        return max(0.0, 10000.0 * min(f * 0.25, 0.05))

    def render_history(self):
        self.hist_list.clear_widgets()
        rows = get_history()
        if not rows:
            self.hist_list.add_widget(Label(text="История пуста.\nСделайте первый анализ.",
                                            font_size=sp(16), halign="center", valign="middle",
                                            color=THEMES[self.theme]["secondary"], size_hint_y=None, height=dp(120)))
            return
        for row in rows[:80]:
            hid, sport, strat, line, cf, prob, ev, stake, result, created = row
            rtxt = "—"
            if result:
                rtxt = "✅ зашла" if result == "win" else "❌ не зашла"
            box = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6))
            info = "{} · {} · Кф {:.2f}\n{:>0.0f}% · {} · {}".format(
                sport, strat, cf, prob * 100, created, rtxt)
            lbl = Label(text=info, font_size=sp(13), halign="left", valign="middle", size_hint_x=1)
            lbl.bind(size=lambda *a: setattr(lbl, "text_size", (lbl.width, None)))
            box.add_widget(lbl)
            if not result:
                bw = Button(text="✔", size_hint_x=None, width=dp(44), font_size=sp(17),
                            background_color=THEMES[self.theme]["green"], color=(1, 1, 1, 1))
                bl = Button(text="✘", size_hint_x=None, width=dp(44), font_size=sp(17),
                            background_color=THEMES[self.theme]["red"], color=(1, 1, 1, 1))
                bw.bind(on_press=lambda x, b=hid: self.mark(b, "win"))
                bl.bind(on_press=lambda x, b=hid: self.mark(b, "lose"))
                box.add_widget(bw); box.add_widget(bl)
            box.canvas.after.clear()
            with box.canvas.after:
                Color(*THEMES[self.theme]["separator"])
                Line(points=[box.x + dp(16), box.y, box.right, box.y], width=dp(0.7))
            self.hist_list.add_widget(box)

    def mark(self, bid, result):
        set_result(bid, result)
        self.render_history()

    def render_stats(self):
        self.stats_list.clear_widgets()
        self.stats_list.add_widget(self.clear_btn)
        rows = get_history()
        decided = [r for r in rows if r[8]]
        if not decided:
            self.stats_list.add_widget(Label(text="Нет данных для статистики.", font_size=sp(16),
                                             halign="center", valign="middle",
                                             color=THEMES[self.theme]["secondary"], size_hint_y=None, height=dp(80)))
            return

        per = {}
        for r in decided:
            strat = r[2]
            d = per.setdefault(strat, {"w": 0, "l": 0, "profit": 0.0})
            stake = r[6] if r[6] else 0.0
            if r[8] == "win":
                d["w"] += 1
                d["profit"] += stake * (r[4] - 1) if r[4] > 1 else 0.0
            else:
                d["l"] += 1
                d["profit"] -= stake

        for strat, d in sorted(per.items(), key=lambda x: -(x[1]["profit"])):
            total = d["w"] + d["l"]
            acc = (d["w"] / total * 100) if total else 0
            card = Card(orientation="vertical", size_hint_y=None, height=dp(104))
            card.add_widget(Label(text=strat, font_size=sp(16), bold=True, halign="left",
                                  color=THEMES[self.theme]["label"], size_hint_y=None, height=sp(22)))
            l2 = Label(text="Зашло {}/{} · Точность {:.0f}% · Пр {:.0f}".format(
                d["w"], total, acc, d["profit"]), font_size=sp(14),
                halign="left", color=THEMES[self.theme]["secondary"], size_hint_y=None, height=sp(20))
            l2.bind(size=lambda *a: setattr(l2, "text_size", (l2.width, None)))
            card.add_widget(l2)
            profit_txt = Label(text="{:+.0f} руб".format(d["profit"]), font_size=sp(15), bold=True,
                               halign="right", color=(THEMES[self.theme]["green"] if d["profit"] >= 0 else THEMES[self.theme]["red"]),
                               size_hint_y=None, height=sp(22))
            card.add_widget(profit_txt)
            self.stats_list.add_widget(card)

        wins = sum(1 for r in decided if r[8] == "win")
        losses = sum(1 for r in decided if r[8] == "lose")
        total = wins + losses
        acc_all = (wins / total * 100) if total else 0
        total_card = Card(orientation="vertical", size_hint_y=None, height=dp(90))
        total_card.add_widget(Label(text="Итого: {} зашло из {} · {:.0f}%".format(wins, total, acc_all),
                                    font_size=sp(16), bold=True, halign="center",
                                    color=THEMES[self.theme]["label"]))
        self.stats_list.add_widget(total_card)

    def clear_all(self, inst):
        clear_history()
        self.render_history()
        self.render_stats()


def poisson(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


class StartApp(App):
    def build(self):
        init_db()
        Window.clearcolor = THEMES["light"]["bg"]
        return MainScreen()


if __name__ == "__main__":
    StartApp().run()
