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
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.utils import rgba

MARGIN = dp(16)
# G_4 добавлен — без него был NameError при запуске
G_4, G_8, G_12, G_16 = dp(4), dp(8), dp(12), dp(16)
R_CARD = dp(16)
TOUCH = dp(48)

FONT_REG = "Roboto"
FONT_BOLD = "Roboto"

THEMES = {
    "light": {
        "bg": rgba("#F2F2F7"), "card": rgba("#FFFFFF"), "field": rgba("#FFFFFF"),
        "sep": rgba(0.78, 0.78, 0.80, 1), "accent": rgba("#007AFF"),
        "label": rgba("#1C1C1E"), "secondary": rgba("#8E8E93"),
        "tabtext": rgba("#8E8E93"), "tabactive": rgba("#007AFF"),
        "green": rgba("#34C759"), "red": rgba("#FF3B30"),
        "big": rgba("#1C1C1E"),
    },
    "dark": {
        "bg": rgba("#000000"), "card": rgba("#1C1C1E"), "field": rgba("#2C2C2E"),
        "sep": rgba("#38383A"), "accent": rgba("#0A84FF"),
        "label": rgba("#FFFFFF"), "secondary": rgba("#8E8E93"),
        "tabtext": rgba("#8E8E93"), "tabactive": rgba("#0A84FF"),
        "green": rgba("#30D158"), "red": rgba("#FF453A"),
        "big": rgba("#FFFFFF"),
    },
}

SPORTS = ["Хоккей", "Футбол", "Теннис", "Настольный теннис"]
MARKETS = ["Исход", "Тотал", "Комби"]

DB_PATH = "betting.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    c = get_db()
    c.executescript("""CREATE TABLE IF NOT EXISTS history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sport TEXT, market TEXT, strategy TEXT, line REAL, cf REAL,
      prob REAL, ev REAL, stake REAL, result TEXT, created TEXT);""")
    c.commit(); c.close()


def save_bet(sport, market, strategy, line, cf, prob, ev, stake):
    c = get_db()
    c.execute("INSERT INTO history (sport,market,strategy,line,cf,prob,ev,stake,result,created) "
              "VALUES (?,?,?,?,?,?,?,?,?,?)",
              (sport, market, strategy, line, cf, prob, ev, stake, None,
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
        super().__init__(padding=[MARGIN, G_16, MARGIN, G_16], spacing=G_8, **kw)
        self.theme = "light"
        with self.canvas.before:
            Color(*THEMES[self.theme]["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self.rect.pos = self.pos; self.rect.size = self.size

    def set_theme(self, name):
        self.theme = name
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*THEMES[name]["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[R_CARD]*4)


class Field(BoxLayout):
    def __init__(self, label, placeholder, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        self.cap = Label(text=label, font_size=sp(14), halign="left", size_hint_y=None, height=sp(18),
                         color=THEMES["light"]["secondary"])
        self.cap.bind(size=lambda *a: setattr(self.cap, "text_size", (self.cap.width, None)))
        self.txt = TextInput(text="", hint_text=placeholder, multiline=False, font_size=sp(16),
                             padding=[G_12, G_12], height=TOUCH, size_hint_y=None,
                             background_color=(1, 1, 1, 1), background_normal="")
        self.add_widget(self.cap)
        self.add_widget(self.txt)

    def set_theme(self, name):
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
        self.current_tab = "anchor"

        # ---- Шапка: имя + баланс + настройки ----
        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[MARGIN, 0, G_16, 0], spacing=G_8)
        self.title = Label(text="Betting PRO", font_size=sp(24), bold=True, halign="left", size_hint_x=1)
        self.title.bind(size=lambda *a: setattr(self.title, "text_size", (self.title.width, None)))
        self.balance_lbl = Label(text="💰 10 000", font_size=sp(18), bold=True, halign="right",
                                 size_hint_x=None, width=dp(120))
        self.settings_btn = Button(text="⚙", font_size=sp(20), size_hint=(None, None),
                                   size=(TOUCH, TOUCH), background_normal="")
        self.settings_btn.bind(on_press=lambda x: self.go_settings())
        header.add_widget(self.title)
        header.add_widget(self.balance_lbl)
        header.add_widget(self.settings_btn)
        self.add_widget(header)

        # ---- Сегменты рынков ----
        seg = BoxLayout(size_hint_y=None, height=dp(44), padding=[MARGIN, 0, MARGIN, 0], spacing=G_8)
        self.market_btns = {}
        for m in MARKETS:
            b = Button(text=m, font_size=sp(15), size_hint_x=1, background_normal="")
            b.bind(on_press=self.on_market)
            self.market_btns[m] = b
            seg.add_widget(b)
        self.add_widget(seg)

        # ---- Панели ----
        self.panel_anchor = BoxLayout()
        self.panel_history = BoxLayout(opacity=0, disabled=True)
        self.panel_stats = BoxLayout(opacity=0, disabled=True)
        self.panel_settings = BoxLayout(opacity=0, disabled=True)

        self._build_anchor()
        self._build_history()
        self._build_stats()
        self._build_settings()

        for p in (self.panel_anchor, self.panel_history, self.panel_stats, self.panel_settings):
            self.add_widget(p)

        # ---- Нижняя навигация ----
        nav = BoxLayout(size_hint_y=None, height=dp(54), spacing=G_4)
        self.nav_btns = {}
        for key, icon, label in (("anchor", "🏠", "Анализ"), ("history", "📊", "История"),
                                 ("stats", "🕐", "Статы"), ("settings", "👤", "Настройки")):
            b = Button(text="{}\n{}".format(icon, label), font_size=sp(10),
                       size_hint_x=1, background_normal="", halign="center", valign="middle")
            b.bind(on_press=lambda x, k=key: self.go_tab(k))
            self.nav_btns[key] = b
            nav.add_widget(b)
        self.tabbar = nav
        self.add_widget(nav)

        self.set_theme("dark")
        self.go_tab("anchor")

    # ---------- Построение ----------
    def _sec(self, t):
        l = Label(text=t, font_size=sp(13), bold=True, halign="left", size_hint_y=None, height=sp(18))
        l.bind(size=lambda *a: setattr(l, "text_size", (l.width, None)))
        return l

    def _build_anchor(self):
        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=G_16, padding=[0, G_8, 0, G_16])
        content.bind(minimum_height=content.setter("height"))

        # Карточка матча
        match = Card(orientation="vertical")
        match.add_widget(self._sec("Матч"))
        r1 = BoxLayout(spacing=G_12, size_hint_y=None, height=TOUCH)
        self.f_k1 = Field("Команда 1: очки", "5.2")
        self.f_k2 = Field("Команда 2: очки", "4.8")
        self.f_k1.size_hint_x = 1
        self.f_k2.size_hint_x = 1
        r1.add_widget(self.f_k1)
        r1.add_widget(self.f_k2)
        match.add_widget(r1)
        self.f_line = Field("Линия / гандикап", "9.5")
        self.f_cf = Field("Коэффициент", "1.90")
        match.add_widget(self.f_line)
        match.add_widget(self.f_cf)
        content.add_widget(match)

        # Чипы спорта
        chip_card = Card(orientation="vertical")
        chip_card.add_widget(self._sec("Вид спорта"))
        crows = BoxLayout(size_hint_y=None, height=dp(48), spacing=G_8)
        self.chips = {}
        for s in SPORTS:
            b = Button(text=s, font_size=sp(14), size_hint_x=1, background_normal="")
            b.bind(on_press=lambda x, s=s: self.set_sport(s))
            self.chips[s] = b
            crows.add_widget(b)
        chip_card.add_widget(crows)
        content.add_widget(chip_card)

        # Большой прогноз
        self.big_card = Card(orientation="vertical")
        self.big_num = Label(text="—", font_size=sp(72), bold=True, halign="center",
                             valign="middle", size_hint_y=None, height=dp(110))
        self.big_detail = Label(text="Выберите параметры и нажмите Анализировать", font_size=sp(15),
                                halign="center", valign="middle", size_hint_y=None, height=dp(60))
        self.big_detail.bind(size=lambda *a: setattr(self.big_detail, "text_size", (self.big_detail.width, None)))
        self.big_card.add_widget(self.big_num)
        self.big_card.add_widget(self.big_detail)
        content.add_widget(self.big_card)

        # Кнопка
        self.analyze_btn = Button(text="Анализировать", font_size=sp(17), bold=True,
                                  size_hint_y=None, height=TOUCH, background_normal="",
                                  background_color=THEMES["dark"]["accent"], color=(1, 1, 1, 1))
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

    def _build_stats(self):
        sc = ScrollView()
        self.stats_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=G_8,
                                    padding=[MARGIN, G_8, MARGIN, G_8])
        self.stats_list.bind(minimum_height=self.stats_list.setter("height"))
        self.clear_btn = Button(text="Очистить историю", font_size=sp(15), bold=True,
                                size_hint_y=None, height=dp(44), background_normal="",
                                background_color=THEMES["dark"]["red"], color=(1, 1, 1, 1))
        self.clear_btn.bind(on_press=self.clear_all)
        self.stats_list.add_widget(self.clear_btn)
        self.stats_sum = Label(text="", font_size=sp(16), halign="center", valign="middle",
                               size_hint_y=None, height=dp(120))
        self.stats_sum.bind(size=lambda *a: setattr(self.stats_sum, "text_size", (self.stats_sum.width, None)))
        self.stats_list.add_widget(self.stats_sum)
        sc.add_widget(self.stats_list)
        self.panel_stats.add_widget(sc)

    def _build_settings(self):
        self.panel_settings.add_widget(self._sec("Настройки"))
        self.f_bank = Field("Банк", "10000")
        self.panel_settings.add_widget(self.f_bank)
        b = Button(text="Применить банк", font_size=sp(16), size_hint_y=None, height=dp(48), background_normal="")
        b.bind(on_press=self.apply_bank)
        self.panel_settings.add_widget(b)

    # ---------- Навигация ----------
    def go_tab(self, key):
        order = {"anchor": self.panel_anchor, "history": self.panel_history,
                 "stats": self.panel_stats, "settings": self.panel_settings}
        for k, p in order.items():
            p.opacity = 1 if k == key else 0
            p.disabled = k != key
        self.current_tab = key
        if key == "history":
            self.render_history()
        elif key == "stats":
            self.render_stats()
        self._style_nav()

    def go_settings(self):
        self.go_tab("settings")

    def on_market(self, btn):
        pass

    def set_sport(self, s):
        self.sport = s
        self._style_chips()

    # ---------- Стили ----------
    def set_theme(self, name):
        self.theme = name
        c = THEMES[name]
        Window.clearcolor = c["bg"]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*c["bg"])
            Rectangle(pos=self.pos, size=self.size)
        self.title.color = c["label"]
        self.balance_lbl.color = c["green"]
        self.settings_btn.color = c["accent"]
        self.big_card.set_theme(name)
        self.big_num.color = c["big"]
        self.big_detail.color = c["secondary"]
        for f in (self.f_k1, self.f_k2, self.f_line, self.f_cf, self.f_bank):
            f.set_theme(name)
        self.analyze_btn.background_color = c["accent"]
        self.clear_btn.background_color = c["red"]
        self._style_markets()
        self._style_chips()
        self._style_nav()

    def _style_markets(self):
        c = THEMES[self.theme]
        for m in self.market_btns.values():
            m.background_color = c["card"]
            m.color = c["label"]

    def _style_chips(self):
        c = THEMES[self.theme]
        if getattr(self, "sport", None):
            for s, b in self.chips.items():
                act = s == self.sport
                b.background_color = c["accent"] if act else c["card"]
                b.color = [1, 1, 1, 1] if act else c["label"]

    def _style_nav(self):
        c = THEMES[self.theme]
        self.tabbar.canvas.before.clear()
        with self.tabbar.canvas.before:
            Color(*c["card"])
            Rectangle(pos=self.tabbar.pos, size=self.tabbar.size)
            Color(*c["sep"])
            Line(points=[self.tabbar.x, self.tabbar.y + self.tabbar.height,
                         self.tabbar.right, self.tabbar.y + self.tabbar.height], width=dp(0.7))
        for k, b in self.nav_btns.items():
            b.color = c["tabactive"] if k == self.current_tab else c["tabtext"]

    # ---------- Логика ----------
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
            return {"p1": p1, "px": px, "p2": p2, "over": p_over, "under": 1 - p_over, "total": total}
        else:
            a = max(a, 0.1); b = max(b, 0.1)
            tot = a + b
            p1 = a / tot * 0.9; p2 = b / tot * 0.9; px = 1 - p1 - p2
            return {"p1": p1, "px": px, "p2": p2, "over": 0, "under": 0, "total": a + b}

    def calculate(self, inst):
        try:
            sport = getattr(self, "sport", "Хоккей")
            a = self._num(self.f_k1.txt.text)
            b = self._num(self.f_k2.txt.text)
            line = self._num(self.f_line.txt.text)
            cf = self._num(self.f_cf.txt.text)
            m = self.model(sport, a, b, line)
            p1, px, p2 = m["p1"], m["px"], m["p2"]
            probs = [p1, px, p2]
            best = max(probs)
            rec = ["К1", "X", "К2"][probs.index(best)]
            prob = best
            ev = prob * cf - 1
            implied = 1 / cf if cf > 1 else 0
            stake = 0.0
            if prob > implied + 0.03:
                verdict = "✅ Value — ставить"
                vcolor = self.palette_green()
            elif prob < implied - 0.03:
                verdict = "❌ Нет value"
                vcolor = self.palette_red()
            else:
                verdict = "⚠️ На границе"
                vcolor = self.palette_secondary()
            save_bet(sport, getattr(self, "market", "Исход"), rec, line, cf, prob, ev, stake)
            self.big_num.text = "{:.0f}%".format(prob * 100)
            self.big_num.color = vcolor
            self.big_detail.text = "{} · EV {:+.3f}\n{} · П1 {:.0f}% X {:.0f}% П2 {:.0f}%".format(
                rec, ev, verdict, p1 * 100, px * 100, p2 * 100)
        except Exception:
            self.big_num.text = "Ошибка"
            self.big_num.color = self.palette_red()
            self.big_detail.text = "Проверьте ввод"

    def palette_green(self):
        return THEMES[self.theme]["green"]
    def palette_red(self):
        return THEMES[self.theme]["red"]
    def palette_secondary(self):
        return THEMES[self.theme]["secondary"]

    def render_history(self):
        self.hist_list.clear_widgets()
        rows = get_history()
        if not rows:
            self.hist_list.add_widget(Label(text="История пуста.\nСделайте анализ.", font_size=sp(16),
                                            halign="center", valign="middle",
                                            color=THEMES[self.theme]["secondary"], size_hint_y=None, height=dp(120)))
            return
        for row in rows[:60]:
            hid, sport, market, strat, line, cf, prob, ev, stake, result, created = row
            rtxt = "—"
            if result:
                rtxt = "✅ зашла" if result == "win" else "❌ не зашла"
            box = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6))
            info = "{} · {} · {:.0f}% · Кф {:.2f}\n{} · {}".format(sport, strat, prob * 100, cf, created, rtxt)
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
            self.hist_list.add_widget(box)

    def mark(self, bid, result):
        set_result(bid, result)
        self.render_history()

    def render_stats(self):
        self.stats_list.clear_widgets()
        self.stats_list.add_widget(self.clear_btn)
        self.stats_list.add_widget(self.stats_sum)
        rows = get_history()
        decided = [r for r in rows if r[8]]
        if not decided:
            self.stats_sum.text = "Нет данных"
            return
        wins = sum(1 for r in decided if r[8] == "win")
        losses = sum(1 for r in decided if r[8] == "lose")
        total = wins + losses
        acc = (wins / total * 100) if total else 0
        profit = 0.0
        for r in decided:
            stake = r[7] or 0.0
            if r[8] == "win":
                profit += stake * (r[5] - 1) if r[5] > 1 else 0.0
            else:
                profit -= stake
        self.stats_sum.text = "Итого: {} из {} · {:.0f}%\nПрибыль: {:+.0f}".format(wins, total, acc, profit)

    def apply_bank(self, inst):
        try:
            v = self._num(self.f_bank.txt.text)
            if v > 0:
                self.balance_lbl.text = "💰 {:.0f}".format(v)
                self.f_bank.txt.text = ""
        except Exception:
            pass

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
        Window.clearcolor = THEMES["dark"]["bg"]
        return MainScreen()


if __name__ == "__main__":
    StartApp().run()
