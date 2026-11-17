import datetime
import math
import sqlite3

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.utils import rgba

# ---------- Палитра BetBoom (тёмная база) ----------
BG = rgba("#121214")
CARD = rgba("#1C1C1F")
ACCENT = rgba("#FFD600")
LIVE_RED = rgba("#FF2E4C")
WHITE = rgba("#FFFFFF")
GREY = rgba("#9E9EA4")
INPUT_BG = (0.15, 0.15, 0.17, 1)

# Светлая тема (для переключателя)
LIGHT_BG = rgba("#F2F2F7")
LIGHT_CARD = rgba("#FFFFFF")
LIGHT_TEXT = rgba("#1C1C1E")
LIGHT_GREY = rgba("#8E8E93")

MARGIN = dp(16)
R_CARD = dp(16)
TOUCH = dp(48)


def get_db():
    return sqlite3.connect("betting.db")


def init_db():
    c = get_db()
    c.executescript("""CREATE TABLE IF NOT EXISTS history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sport TEXT, market TEXT, line REAL, cf REAL,
      prob REAL, ev REAL, stake REAL, result TEXT, created TEXT);""")
    c.commit(); c.close()


def save_bet(sport, market, line, cf, prob, ev, stake):
    c = get_db()
    c.execute("INSERT INTO history (sport,market,line,cf,prob,ev,stake,result,created) "
              "VALUES (?,?,?,?,?,?,?,?,?,?)",
              (sport, market, line, cf, prob, ev, stake, None,
               datetime.datetime.now().strftime("%d.%m %H:%M")))
    c.commit(); c.close()


def get_history(limit=200):
    c = get_db()
    rows = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return rows


def set_result(bid, result):
    c = get_db(); c.execute("UPDATE history SET result=? WHERE id=?", (result, bid)); c.commit(); c.close()


def clear_history():
    c = get_db(); c.execute("DELETE FROM history"); c.commit(); c.close()


class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(padding=[MARGIN, dp(16), MARGIN, dp(16)], spacing=dp(8), **kw)
        self.bg = CARD
        with self.canvas.before:
            Color(*self.bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self.rect.pos = self.pos; self.rect.size = self.size

    def set_card_color(self, color):
        self.bg = color
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)


class BigBtn(Button):
    def __init__(self, text, **kw):
        super().__init__(text=text, size_hint_y=None, height=TOUCH, font_size=sp(17),
                         bold=True, color=[0, 0, 0, 1], background_normal="",
                         background_color=ACCENT, **kw)


class Field(BoxLayout):
    def __init__(self, label, placeholder, **kw):
        super().__init__(orientation="vertical", spacing=dp(4), size_hint_y=None, **kw)
        self.cap = Label(text=label, font_size=sp(13), halign="left", color=GREY,
                         size_hint_y=None, height=sp(18))
        self.cap.bind(size=lambda *a: setattr(self.cap, "text_size", (self.cap.width, None)))
        self.txt = TextInput(text="", hint_text=placeholder, multiline=False, font_size=sp(16),
                             padding=[dp(12), dp(12)], height=TOUCH, size_hint_y=None,
                             background_color=INPUT_BG, foreground_color=WHITE,
                             hint_text_color=GREY, cursor_color=ACCENT)
        self.add_widget(self.cap)
        self.add_widget(self.txt)
        self.height = self.cap.height + self.txt.height + dp(4)


class MainScreen(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        self.dark = True
        self.nav_btns = {}
        self.current_tab = "anchor"
        self.sport = "Хоккей"
        self.bg_color = BG
        self.card_color = CARD
        self.text_color = WHITE
        self.grey_color = GREY

        # ---- Хедер ----
        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[MARGIN, 0, MARGIN, 0], spacing=dp(8))
        self.title = Label(text="Betting PRO", font_size=sp(22), bold=True, color=self.text_color,
                           halign="left", size_hint_x=1)
        self.title.bind(size=lambda *a: setattr(self.title, "text_size", (self.title.width, None)))
        self.balance = Label(text="💰 10 000", font_size=sp(17), bold=True, color=ACCENT,
                             size_hint_x=None, width=dp(110))
        header.add_widget(self.title)
        header.add_widget(self.balance)
        self.add_widget(header)

        # ---- Горизонтальные категории ----
        cats = ScrollView(size_hint_y=None, height=dp(44), do_scroll_x=True, do_scroll_y=False)
        crow = BoxLayout(size_hint_x=None, spacing=dp(8), padding=[MARGIN, 0, MARGIN, 0])
        crow.bind(minimum_width=crow.setter("width"))
        self.chip_btns = {}
        for s in ["Все", "Хоккей", "Футбол", "Теннис", "НТТ"]:
            b = Button(text=s, size_hint=(None, None), size=(dp(88), dp(36)), font_size=sp(14),
                       background_normal="", background_color=CARD, color=GREY)
            b.bind(on_press=lambda x, s=s: self.set_sport(s))
            self.chip_btns[s] = b
            crow.add_widget(b)
        cats.add_widget(crow)
        self.add_widget(cats)

        # ---- Панели ----
        self.panel_anchor = BoxLayout()
        self.panel_history = BoxLayout(opacity=0, disabled=True)
        self.panel_settings = BoxLayout(opacity=0, disabled=True)
        self._build_anchor()
        self._build_history()
        self._build_settings()
        for p in (self.panel_anchor, self.panel_history, self.panel_settings):
            self.add_widget(p)

        # ---- Нижний таб-бар ----
        nav = BoxLayout(size_hint_y=None, height=dp(54))
        for key, icon, label in (("anchor", "🏠", "Анализ"), ("history", "📊", "История"),
                                 ("settings", "⚙", "Настройки")):
            b = Button(text="{}\n{}".format(icon, label), font_size=sp(10), size_hint_x=1,
                       background_normal="", color=GREY, halign="center", valign="middle")
            b.bind(on_press=lambda x, k=key: self.go_tab(k))
            self.nav_btns[key] = b
            nav.add_widget(b)
        self.tabbar = nav
        self.add_widget(nav)

        self.apply_theme()
        self.go_tab("anchor")

    def _sec(self, t):
        l = Label(text=t, font_size=sp(13), bold=True, color=self.grey_color, halign="left",
                  size_hint_y=None, height=sp(20))
        l.bind(size=lambda *a: setattr(l, "text_size", (l.width, None)))
        return l

    def _build_anchor(self):
        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(16), padding=[0, dp(8), 0, dp(16)])
        content.bind(minimum_height=content.setter("height"))

        match = Card(orientation="vertical", size_hint_y=None, height=dp(240))
        match.add_widget(self._sec("Матч"))
        r1 = BoxLayout(spacing=dp(12), size_hint_y=None, height=TOUCH)
        self.f_k1 = Field("Команда 1: очки", "5.2")
        self.f_k2 = Field("Команда 2: очки", "4.8")
        self.f_k1.size_hint_x = 1
        self.f_k2.size_hint_x = 1
        r1.add_widget(self.f_k1); r1.add_widget(self.f_k2)
        match.add_widget(r1)
        self.f_line = Field("Линия / гандикап", "9.5")
        self.f_cf = Field("Коэффициент", "1.90")
        match.add_widget(self.f_line); match.add_widget(self.f_cf)
        content.add_widget(match)

        self.big_card = Card(orientation="vertical", size_hint_y=None, height=dp(180))
        self.big_num = Label(text="—", font_size=sp(70), bold=True, color=ACCENT,
                             halign="center", valign="middle", size_hint_y=None, height=dp(100))
        self.big_num.bind(size=lambda *a: setattr(self.big_num, "text_size", (self.big_num.width, None)))
        self.big_detail = Label(text="Выберите параметры", font_size=sp(14), color=self.grey_color,
                                halign="center", valign="middle", size_hint_y=None, height=dp(50))
        self.big_detail.bind(size=lambda *a: setattr(self.big_detail, "text_size", (self.big_detail.width, None)))
        self.big_card.add_widget(self.big_num)
        self.big_card.add_widget(self.big_detail)
        content.add_widget(self.big_card)

        self.analyze_btn = BigBtn("Анализировать")
        self.analyze_btn.bind(on_press=self.calculate)
        content.add_widget(self.analyze_btn)

        scroll.add_widget(content)
        self.panel_anchor.add_widget(scroll)

    def _build_history(self):
        sc = ScrollView()
        self.hist_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        self.hist_list.bind(minimum_height=self.hist_list.setter("height"))
        sc.add_widget(self.hist_list)
        self.panel_history.add_widget(sc)

    def _build_settings(self):
        self.panel_settings.add_widget(self._sec("Настройки"))
        self.f_bank = Field("Банк", "10000")
        self.panel_settings.add_widget(self.f_bank)
        b = BigBtn("Применить банк")
        b.bind(on_press=self.apply_bank)
        self.panel_settings.add_widget(b)
        # Переключатель темы
        trow = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        trow.add_widget(Label(text="Тёмная тема", font_size=sp(16), color=WHITE, size_hint_x=1, halign="left"))
        self.theme_switch = Switch(active=True)
        self.theme_switch.bind(active=self.on_theme)
        trow.add_widget(self.theme_switch)
        self.panel_settings.add_widget(trow)

    def go_tab(self, key):
        order = {"anchor": self.panel_anchor, "history": self.panel_history, "settings": self.panel_settings}
        for k, p in order.items():
            p.opacity = 1 if k == key else 0
            p.disabled = k != key
        self.current_tab = key
        if key == "history":
            self.render_history()
        self._style_nav()

    def _style_nav(self):
        for k, b in self.nav_btns.items():
            b.color = ACCENT if k == self.current_tab else self.grey_color

    def set_sport(self, s):
        self.sport = s
        for name, b in self.chip_btns.items():
            act = name == s
            b.background_color = ACCENT if act else self.card_color
            b.color = [0, 0, 0, 1] if act else self.grey_color

    def on_theme(self, sw, val):
        self.dark = val
        self.apply_theme()
        self.render_history()

    def apply_theme(self):
        if self.dark:
            self.bg_color, self.card_color = BG, CARD
            self.text_color, self.grey_color = WHITE, GREY
        else:
            self.bg_color, self.card_color = LIGHT_BG, LIGHT_CARD
            self.text_color, self.grey_color = LIGHT_TEXT, LIGHT_GREY
        Window.clearcolor = self.bg_color
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            Rectangle(pos=self.pos, size=self.size)
        self.title.color = self.text_color
        self.big_card.set_card_color(self.card_color)
        self.big_num.color = ACCENT
        self.big_detail.color = self.grey_color
        for f in (self.f_k1, self.f_k2, self.f_line, self.f_cf, self.f_bank):
            f.cap.color = self.grey_color
            f.txt.foreground_color = self.text_color
            f.txt.hint_text_color = self.grey_color
            f.txt.background_color = {(False): LIGHT_CARD, (True): INPUT_BG}.get((self.dark,), INPUT_BG)
            f.txt.background_color = INPUT_BG if self.dark else LIGHT_CARD
        # категории
        for name, b in self.chip_btns.items():
            act = name == self.sport
            b.background_color = ACCENT if act else self.card_color
            b.color = [0, 0, 0, 1] if act else self.grey_color
        # таб-бар
        for k, b in self.nav_btns.items():
            b.color = ACCENT if k == self.current_tab else self.grey_color
        self._style_nav()

    def _num(self, t):
        try:
            return float((t or "0").strip().replace(",", "."))
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
            return {"p1": p1, "px": px, "p2": p2, "total": total}
        else:
            a = max(a, 0.1); b = max(b, 0.1)
            tot = a + b
            p1 = a/tot*0.9; p2 = b/tot*0.9; px = 1-p1-p2
            return {"p1": p1, "px": px, "p2": p2, "total": a+b}

    def calculate(self, inst):
        try:
            a = self._num(self.f_k1.txt.text)
            b = self._num(self.f_k2.txt.text)
            line = self._num(self.f_line.txt.text)
            cf = self._num(self.f_cf.txt.text)
            m = self.model(self.sport, a, b, line)
            p1, px, p2 = m["p1"], m["px"], m["p2"]
            probs = [p1, px, p2]
            best = max(probs)
            rec = ["К1", "X", "К2"][probs.index(best)]
            prob = best
            ev = prob*cf - 1
            implied = 1/cf if cf > 1 else 0
            verdict = "✅ Value" if prob > implied+0.03 else ("❌ Нет value" if prob < implied-0.03 else "⚠️ На границе")
            save_bet(self.sport, "Исход", line, cf, prob, ev, 0)
            self.big_num.text = "{:.0f}%".format(prob*100)
            self.big_num.color = ACCENT if "✅" in verdict else (LIVE_RED if "❌" in verdict else self.grey_color)
            self.big_detail.text = "{} · EV {:+.3f}\nП1 {:.0f}% X {:.0f}% П2 {:.0f}%".format(verdict, ev, p1*100, px*100, p2*100)
        except Exception:
            self.big_num.text = "Ошибка"
            self.big_num.color = LIVE_RED
            self.big_detail.text = "Проверьте ввод"

    def render_history(self):
        self.hist_list.clear_widgets()
        rows = get_history()
        if not rows:
            self.hist_list.add_widget(Label(text="История пуста", font_size=sp(16), color=self.grey_color,
                                            halign="center", valign="middle", size_hint_y=None, height=dp(120)))
            return
        for row in rows[:50]:
            hid, sport, market, line, cf, prob, ev, stake, result, created = row
            rtxt = "✅ зашла" if result == "win" else ("❌ не зашла" if result == "lose" else "—")
            card = Card(orientation="horizontal", size_hint_y=None, height=dp(54))
            card.set_card_color(self.card_color)
            lbl = Label(text="{} · {:.0f}% · {}\nКф {:.2f} · {}".format(sport, prob*100, created, cf, rtxt),
                        font_size=sp(13), color=self.text_color, halign="left", valign="middle", size_hint_x=1)
            lbl.bind(size=lambda *a: setattr(lbl, "text_size", (lbl.width, None)))
            card.add_widget(lbl)
            if not result:
                bw = Button(text="✔", size_hint=(None,None), size=(dp(40),dp(40)), background_normal="",
                            background_color=rgba("#22C55E"), color=[1,1,1,1])
                bl = Button(text="✘", size_hint=(None,None), size=(dp(40),dp(40)), background_normal="",
                            background_color=LIVE_RED, color=[1,1,1,1])
                bw.bind(on_press=lambda x, b=hid: (set_result(b, "win"), self.render_history()))
                bl.bind(on_press=lambda x, b=hid: (set_result(b, "lose"), self.render_history()))
                card.add_widget(bw); card.add_widget(bl)
            self.hist_list.add_widget(card)

    def apply_bank(self, inst):
        try:
            v = self._num(self.f_bank.txt.text)
            if v > 0:
                self.balance.text = "💰 {:.0f}".format(v)
                self.f_bank.txt.text = ""
        except Exception:
            pass


def poisson(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


class BettingApp(App):
    def build(self):
        init_db()
        Window.clearcolor = BG
        return MainScreen()


if __name__ == "__main__":
    BettingApp().run()
