import datetime
import math
import sqlite3

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.utils import rgba

BG = rgba("#121214")
CARD = rgba("#1C1C1F")
ACCENT = rgba("#FFD600")
LIVE_RED = rgba("#FF2E4C")
WHITE = rgba("#FFFFFF")
GREY = rgba("#9E9EA4")
INPUT_BG = (0.15, 0.15, 0.17, 1)
GREEN = rgba("#22C55E")

LIGHT_BG = rgba("#F2F2F7")
LIGHT_CARD = rgba("#FFFFFF")
LIGHT_TEXT = rgba("#1C1C1E")
LIGHT_GREY = rgba("#8E8E93")

MARGIN = dp(16)
R_CARD = dp(16)


def get_db(): return sqlite3.connect("betting.db")


def init_db():
    c = get_db()
    c.executescript("""CREATE TABLE IF NOT EXISTS history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sport TEXT, market TEXT, line REAL, cf REAL,
      prob REAL, stake REAL, payout REAL, result TEXT, created TEXT);""")
    c.commit(); c.close()


def save_bet(sport, market, line, cf, prob, stake, payout):
    c = get_db()
    c.execute("INSERT INTO history (sport,market,line,cf,prob,stake,payout,result,created) "
              "VALUES (?,?,?,?,?,?,?,?,?)",
              (sport, market, line, cf, prob, stake, payout, None,
               datetime.datetime.now().strftime("%d.%m %H:%M")))
    c.commit(); c.close()


def get_history(limit=200):
    c = get_db()
    rows = c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return rows


def set_result(bid, result):
    c = get_db(); c.execute("UPDATE history SET result=? WHERE id=?", (result, bid)); c.commit(); c.close()


def show_error(msg):
    pop = Popup(title="Ошибка ввода", content=Label(text=msg, size_hint=(1, None), height=dp(100)),
                size_hint=(0.8, 0.3))
    pop.open()


class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(padding=[MARGIN, dp(14), MARGIN, dp(14)], spacing=dp(8), **kw)
        self.bg = CARD
        with self.canvas.before:
            Color(*self.bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self.rect.pos = self.pos; self.rect.size = self.size

    def set_card_color(self, color):
        self.bg = color
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)


class BigBtn(Button):
    def __init__(self, text, **kw):
        super().__init__(text=text, size_hint_y=None, height=dp(50), font_size=sp(18),
                         bold=True, color=[0, 0, 0, 1], background_normal="",
                         background_color=ACCENT, **kw)


class IconField(BoxLayout):
    def __init__(self, icon, label, placeholder, on_change=None, split=False, **kw):
        super().__init__(orientation="vertical", spacing=dp(3), size_hint_y=None, **kw)
        self.cap = Label(text=label, font_size=sp(12), halign="left", color=GREY,
                         size_hint_y=None, height=sp(16))
        self.cap.bind(size=lambda *a: setattr(self.cap, "text_size", (self.cap.width, None)))
        row = BoxLayout(spacing=dp(6), size_hint_y=None, height=dp(44))
        self.icon = Label(text=icon, font_size=sp(16), color=ACCENT, size_hint=(None, None), width=dp(26))
        self.txt = TextInput(text="", hint_text=placeholder, multiline=False, font_size=sp(16),
                             padding=[dp(10), dp(10)], height=dp(44), size_hint_y=None, size_hint_x=1,
                             background_color=INPUT_BG, foreground_color=WHITE,
                             hint_text_color=GREY, cursor_color=ACCENT,
                             input_filter=self._split if split else "float")
        if on_change:
            self.txt.bind(text=on_change)
        row.add_widget(self.icon); row.add_widget(self.txt)
        self.add_widget(self.cap); self.add_widget(row)
        self.height = self.cap.height + row.height + dp(3)

    def _split(self, text, from_undo):
        return "".join(ch for ch in text if ch in "0123456789./-")


class MainScreen(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        self.dark = True
        self.nav_btns = {}
        self.current_tab = "anchor"
        self.sport = "Хоккей"
        self.bank = 10000.0
        self.pct_cap = 4.0
        self.bg_color = BG
        self.card_color = CARD
        self.text_color = WHITE
        self.grey_color = GREY

        header = BoxLayout(size_hint_y=None, height=dp(50), padding=[MARGIN, 0, MARGIN, 0], spacing=dp(8))
        self.title = Label(text="Betting PRO", font_size=sp(21), bold=True, color=self.text_color, halign="left", size_hint_x=1)
        self.title.bind(size=lambda *a: setattr(self.title, "text_size", (self.title.width, None)))
        self.balance = Label(text="Банк: 10 000", font_size=sp(15), bold=True, color=ACCENT, size_hint_x=None, width=dp(150))
        header.add_widget(self.title); header.add_widget(self.balance)
        self.add_widget(header)

        crow = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6), padding=[MARGIN, 0, MARGIN, 0])
        self.chip_btns = {}
        for s in ["Все", "Хоккей", "Футбол", "Теннис", "НТТ"]:
            b = Button(text=s, size_hint_x=1, height=dp(34), size_hint_y=None, font_size=sp(12),
                       background_normal="", background_color=CARD, color=GREY)
            b.bind(on_press=lambda x, s=s: self.set_sport(s))
            self.chip_btns[s] = b
            crow.add_widget(b)
        self.add_widget(crow)

        self.content = BoxLayout()
        self.add_widget(self.content)

        nav = BoxLayout(size_hint_y=None, height=dp(50))
        for key, icon, label in (("anchor", "1", "Анализ"), ("history", "2", "История"), ("settings", "3", "Настройки")):
            b = Button(text="{}  {}".format(icon, label), font_size=sp(12), size_hint_x=1, background_normal="", color=GREY)
            b.bind(on_press=lambda x, k=key: self.go_tab(k))
            self.nav_btns[key] = b
            nav.add_widget(b)
        self.add_widget(nav)

        self.apply_theme()
        self.go_tab("anchor")

    def _scroll(self, w):
        sc = ScrollView()
        w.size_hint_y = None
        w.bind(minimum_height=w.setter("height"))
        sc.add_widget(w)
        return sc

    def _sec(self, t):
        l = Label(text=t, font_size=sp(12), bold=True, color=self.grey_color, halign="left", size_hint_y=None, height=sp(16))
        l.bind(size=lambda *a: setattr(l, "text_size", (l.width, None)))
        return l

    def _recalc(self, *a):
        if hasattr(self, "profit_lbl"):
            try:
                self.calculate(None)
            except Exception:
                pass

    def _build_anchor(self):
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=[0, dp(8), 0, dp(14)])

        match = Card(orientation="vertical", size_hint_y=None, height=None)
        match.add_widget(self._sec("Матч (счёт)"))
        r1 = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(44))
        self.f_k1 = IconField("1", "Команда 1", "5.2", on_change=self._recalc)
        self.f_k2 = IconField("2", "Команда 2", "4.8", on_change=self._recalc)
        self.f_k1.size_hint_x = 1; self.f_k2.size_hint_x = 1
        r1.add_widget(self.f_k1); r1.add_widget(self.f_k2)
        match.add_widget(r1)
        self.f_line = IconField("L", "Линия (тотал/фора)", "9.5", on_change=self._recalc)
        match.add_widget(self.f_line)
        match.add_widget(self._sec("Коэффициент (выберите или введите)"))
        krow = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.cf_btns = {}
        for name, k in (("П1", "1.90"), ("X", "3.40"), ("П2", "3.60")):
            b = Button(text="{} {}".format(name, k), font_size=sp(13), size_hint_x=1,
                       background_normal="", background_color=(0.2, 0.2, 0.24, 1), color=WHITE)
            b.bind(on_press=lambda x, k=k: self.set_cf(k))
            self.cf_btns[name] = b
            krow.add_widget(b)
        match.add_widget(krow)
        self.f_cf = IconField("≈", "Мой кэф (вручную)", "введётся из кнопок", on_change=self._recalc)
        self.f_mine = IconField("%", "Моя вероятность, %", "55", on_change=self._recalc)
        self.f_stake = IconField("₽", "Сумма ставки", "500", on_change=self._recalc)
        match.add_widget(self.f_cf)
        match.add_widget(self.f_mine)
        match.add_widget(self.f_stake)
        content.add_widget(match)

        self.big_card = Card(orientation="vertical", size_hint_y=None, height=dp(210))
        self.profit_lbl = Label(text="—", font_size=sp(34), bold=True, color=GREEN,
                                halign="center", valign="middle", size_hint_y=None, height=dp(60))
        self.profit_lbl.bind(size=lambda *a: setattr(self.profit_lbl, "text_size", (self.profit_lbl.width, None)))
        self.kelly_lbl = Label(text="Келли: —", font_size=sp(15), color=WHITE,
                               halign="center", valign="middle", size_hint_y=None, height=dp(34))
        self.kelly_lbl.bind(size=lambda *a: setattr(self.kelly_lbl, "text_size", (self.kelly_lbl.width, None)))
        self.detail_lbl = Label(text="Введите данные — расчёт автоматический", font_size=sp(12), color=self.grey_color,
                                halign="center", valign="middle", size_hint_y=None, height=dp(90))
        self.detail_lbl.bind(size=lambda *a: setattr(self.detail_lbl, "text_size", (self.detail_lbl.width, None)))
        self.big_card.add_widget(self.profit_lbl)
        self.big_card.add_widget(self.kelly_lbl)
        self.big_card.add_widget(self.detail_lbl)
        content.add_widget(self.big_card)

        return self._scroll(content)

    def _build_history(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=2)
        box.bind(minimum_height=box.setter("height"))
        self.hist_list = box
        return self._scroll(box)

    def _build_settings(self):
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=[MARGIN, dp(12), MARGIN, dp(12)])
        self.f_bank = IconField("₽", "Банк", "10000")
        self.f_pct = IconField("%", "Келли кап (% от банка)", "4")
        content.add_widget(self.f_bank)
        content.add_widget(self.f_pct)
        b = BigBtn("Применить")
        b.bind(on_press=self.apply_bank)
        content.add_widget(b)
        trow = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        trow.add_widget(Label(text="Тёмная тема", font_size=sp(16), color=WHITE, size_hint_x=1, halign="left"))
        self.theme_switch = Switch(active=True)
        self.theme_switch.bind(active=self.on_theme)
        trow.add_widget(self.theme_switch)
        content.add_widget(trow)
        return self._scroll(content)

    def go_tab(self, key):
        self.content.clear_widgets()
        if key == "anchor":
            self.content.add_widget(self._build_anchor())
        elif key == "history":
            self.content.add_widget(self._build_history()); self.render_history()
        elif key == "settings":
            self.content.add_widget(self._build_settings())
        self.current_tab = key
        self.apply_theme()

    def _style_nav(self):
        for k, b in self.nav_btns.items():
            if k == self.current_tab:
                # активная вкладка — жёлтая, как кнопка «Рассчитать»
                b.background_color = ACCENT
                b.color = [0, 0, 0, 1]
            else:
                # неактивные — тёмно-серые
                b.background_color = CARD
                b.color = self.grey_color

    def set_cf(self, k):
        if hasattr(self, "f_cf"):
            self.f_cf.txt.text = k
            self._recalc()

    def set_sport(self, s):
        self.sport = s
        for name, b in self.chip_btns.items():
            act = name == s
            b.background_color = ACCENT if act else self.card_color
            b.color = [0, 0, 0, 1] if act else self.grey_color

    def on_theme(self, sw, val):
        self.dark = val; self.apply_theme(); self.render_history()

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
            Color(*self.bg_color); Rectangle(pos=self.pos, size=self.size)
        self.title.color = self.text_color
        if hasattr(self, "big_card"):
            self.big_card.set_card_color(self.card_color)
            self.detail_lbl.color = self.grey_color
        for fname in ("f_k1", "f_k2", "f_line", "f_cf", "f_mine", "f_stake", "f_bank", "f_pct"):
            f = getattr(self, fname, None)
            if f:
                f.cap.color = self.grey_color
                f.icon.color = ACCENT
                f.txt.foreground_color = self.text_color
                f.txt.hint_text_color = self.grey_color
                f.txt.background_color = INPUT_BG if self.dark else LIGHT_CARD
        for name, b in self.chip_btns.items():
            act = name == self.sport
            b.background_color = ACCENT if act else self.card_color
            b.color = [0, 0, 0, 1] if act else self.grey_color
        self._style_nav()

    def _num(self, t):
        try:
            return float((t or "").strip().replace(",", "."))
        except Exception:
            return 0.0

    def model(self, sport, a, b):
        if sport in ("Хоккей", "Футбол"):
            a = max(a, 0.1); b = max(b, 0.1)
            p1 = px = p2 = 0.0
            for g1 in range(16):
                for g2 in range(16):
                    p = poisson(g1, a) * poisson(g2, b)
                    if g1 > g2: p1 += p
                    elif g1 == g2: px += p
                    else: p2 += p
            return p1, px, p2
        else:
            a = max(a, 0.1); b = max(b, 0.1)
            tot = a + b
            p1 = a/tot*0.9; p2 = b/tot*0.9; px = 1-p1-p2
            return p1, px, p2

    def calculate(self, inst):
        try:
            a = self._num(self.f_k1.txt.text)
            b = self._num(self.f_k2.txt.text)
            cf = self._num(self.f_cf.txt.text)
            stake = self._num(self.f_stake.txt.text)
            my_prob_str = self.f_mine.txt.text.strip() or ""
            total = a + b

            p1, px, p2 = self.model(self.sport, a, b)
            if my_prob_str:
                my_pct = float(my_prob_str.replace(",", "."))
                prob = my_pct / 100.0
                rec = "Моя оценка"
            else:
                probs = [p1, px, p2]
                prob = max(probs)
                rec = ["К1", "X", "К2"][probs.index(prob)]

            if cf <= 1 and self.f_cf.txt.text.strip():
                show_error("Коэффициент должен быть > 1.00")
                return
            if stake > self.bank:
                show_error("Сумма ставки больше банка!")
                return

            self.pct_cap = self._num(self.f_pct.txt.text) if hasattr(self, "f_pct") else 4
            if self.pct_cap <= 0: self.pct_cap = 4.0
            b_kelly = (prob*cf - 1)/(cf - 1) if cf > 1 else 0
            kelly_stake = self.bank * min(max(b_kelly, 0.0), self.pct_cap/100.0)

            if stake <= 0:
                stake = kelly_stake
            payout = stake * cf if cf > 1 else 0
            profit = payout - stake

            save_bet(self.sport, rec, a, cf, prob, kelly_stake if kelly_stake > 0 else stake, payout)

            self.profit_lbl.text = "Выигрыш: {:.0f}  |  Чистая {:+.0f}".format(payout, profit)
            self.profit_lbl.color = GREEN if profit >= 0 else LIVE_RED
            self.kelly_lbl.text = "Келли: {:.0f} ({}%)  ·  Вер. {:.0f}%" .format(kelly_stake, self.pct_cap, prob*100)
            self.detail_lbl.text = "{}\nТотал: {:.1f} · EV {:+.3f}".format(rec, total, prob*cf - 1 if cf > 1 else 0)
        except Exception:
            pass

    def render_history(self):
        self.hist_list.clear_widgets()
        rows = get_history()
        if not rows:
            self.hist_list.add_widget(Label(text="История пуста", font_size=sp(15), color=self.grey_color,
                                            halign="center", valign="middle", size_hint_y=None, height=dp(120)))
            return
        for row in rows[:40]:
            hid, sport, market, line, cf, prob, stake, payout, result, created = row
            rtxt = "зашла" if result == "win" else ("не зашла" if result == "lose" else "-")
            card = Card(orientation="horizontal", size_hint_y=None, height=dp(58))
            card.set_card_color(self.card_color)
            lbl = Label(text="{} · {} · Кф {:.2f} · {}\n{} → {:.0f} · {}".format(
                sport, market, cf, created, "ставка {:.0f}".format(stake), payout, rtxt),
                font_size=sp(11), color=self.text_color, halign="left", valign="middle", size_hint_x=1)
            lbl.bind(size=lambda *a: setattr(lbl, "text_size", (lbl.width, None)))
            card.add_widget(lbl)
            if not result:
                bw = Button(text="+", size_hint=(None,None), size=(dp(40),dp(40)), background_normal="", background_color=GREEN, color=[1,1,1,1])
                bl = Button(text="-", size_hint=(None,None), size=(dp(40),dp(40)), background_normal="", background_color=LIVE_RED, color=[1,1,1,1])
                bw.bind(on_press=lambda x, b=hid: (set_result(b, "win"), self.render_history()))
                bl.bind(on_press=lambda x, b=hid: (set_result(b, "lose"), self.render_history()))
                card.add_widget(bw); card.add_widget(bl)
            self.hist_list.add_widget(card)

    def apply_bank(self, inst):
        try:
            v = self._num(self.f_bank.txt.text)
            if v > 0:
                self.bank = v; self.balance.text = "Банк: {:.0f}".format(v); self.f_bank.txt.text = ""
            p = self._num(self.f_pct.txt.text) if hasattr(self, "f_pct") else 0
            if p > 0: self.pct_cap = p
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
