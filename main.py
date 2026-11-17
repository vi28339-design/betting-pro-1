import datetime
import json
import math
import os
import sqlite3

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.utils import rgba

# --- Шрифт: Inter (SF Pro-подобный) если лежит в fonts/, иначе Roboto ---
_font_base = "fonts/"
if os.path.exists(os.path.join(_font_base, "Inter-Regular.ttf")):
    FONT_REG = os.path.join(_font_base, "Inter-Regular.ttf")
    FONT_BOLD = os.path.join(_font_base, "Inter-SemiBold.ttf")
else:
    FONT_REG = "Roboto"
    FONT_BOLD = "Roboto"

# Размеры в духе iOS
S = {  # scale
    "h1": 34, "h2": 28, "body": 17, "body2": 15,
    "caption": 13, "small": 11, "tab": 16,
}

LIGHT = {"bg": rgba("#F2F2F7"), "card": rgba("#FFFFFF"), "accent": rgba("#007AFF"),
         "text": rgba("#1C1C1E"), "subtext": rgba("#8E8E93"), "card_text": rgba("#1C1C1E"),
         "green": rgba("#34C759"), "red": rgba("#FF3B30"), "line": rgba("#E5E5EA")}
DARK = {"bg": rgba("#000000"), "card": rgba("#1C1C1E"), "accent": rgba("#0A84FF"),
        "text": rgba("#FFFFFF"), "subtext": rgba("#8E8E93"), "card_text": rgba("#FFFFFF"),
        "green": rgba("#30D158"), "red": rgba("#FF453A"), "line": rgba("#38383A")}

SPORTS = ["Хоккей", "Футбол", "Теннис", "Настольный теннис"]
STRATEGIES = ["Тотал ТБ", "Тотал ТМ", "Двойной шанс 1X", "Двойной шанс X2",
              "Победа фаворита", "Value (EV)", "Келли-критерий", "Обе забьют"]

DB_PATH = "betting.db"
SETTINGS_PATH = "settings.json"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    c = get_db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sport TEXT, strategy TEXT, line REAL, cf REAL,
      prob REAL, ev REAL, stake REAL, bank REAL,
      result TEXT, created TEXT
    );""")
    c.commit(); c.close()


def save_bet(sport, strategy, line, cf, prob, ev, stake, bank, result=None):
    c = get_db()
    c.execute("INSERT INTO history (sport,strategy,line,cf,prob,ev,stake,bank,result,created) "
              "VALUES (?,?,?,?,?,?,?,?,?,?)",
              (sport, strategy, line, cf, prob, ev, stake, bank, result,
               datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
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


def load_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"dark": False, "bank": 10000}


def save_settings(s):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(s, f)
    except Exception:
        pass


class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(padding=[16, 14, 16, 14], spacing=10, **kw)
        self.palette = LIGHT
        with self.canvas.before:
            Color(*self.palette["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 18, 18])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def apply_theme(self, palette):
        self.palette = palette
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*palette["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 18, 18])


class Field(BoxLayout):
    def __init__(self, label, hint, **kw):
        super().__init__(orientation="vertical", spacing=4, **kw)
        self.lbl = Label(text=label, font_name=FONT_REG, font_size=S["caption"], halign="left",
                         size_hint_y=None, height=16, color=LIGHT["subtext"])
        self.lbl.bind(size=lambda *a: setattr(self.lbl, "text_size", (self.lbl.width, None)))
        self.txt = TextInput(hint_text=hint, font_name=FONT_REG, font_size=S["body"],
                             multiline=False, background_color=[1, 1, 1, 1], background_normal="",
                             padding=[12, 10, 12, 10])
        self.add_widget(self.lbl)
        self.add_widget(self.txt)


class MainLayout(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=[16, 30, 16, 12], spacing=10, **kw)
        self.settings = load_settings()
        self.dark = self.settings.get("dark", False)
        self.palette = DARK if self.dark else LIGHT
        self.bank = float(self.settings.get("bank", 10000))
        self.bind(size=self._update_bg, pos=self._update_bg)
        self._build_header()
        self._build_tabs()
        self._build_analysis_tab()
        self._build_history_tab()
        self._build_stats_tab()
        self.show_tab("analyze")
        self._apply_theme()

    def _build_header(self):
        h = BoxLayout(size_hint_y=None, height=48, spacing=10)
        self.title = Label(text="Ставки PRO", font_name=FONT_BOLD, font_size=S["h1"], halign="left")
        self.title.bind(size=lambda *a: setattr(self.title, "text_size", (self.title.width, None)))
        self.bank_lbl = Label(text="Банк {:.0f}".format(self.bank), font_name=FONT_REG, font_size=S["body2"],
                              halign="right")
        self.bank_lbl.bind(size=lambda *a: setattr(self.bank_lbl, "text_size", (self.bank_lbl.width, None)))
        self.theme_switch = Switch(active=self.dark, size_hint_x=None, width=54)
        self.theme_switch.bind(active=self.toggle_theme)
        h.add_widget(self.title)
        h.add_widget(self.bank_lbl)
        h.add_widget(self.theme_switch)
        self.add_widget(h)

    def _build_tabs(self):
        t = BoxLayout(size_hint_y=None, height=44, spacing=6)
        self.tab_analyze = Button(text="Анализ", font_name=FONT_BOLD, font_size=S["tab"], background_normal="")
        self.tab_history = Button(text="История", font_name=FONT_REG, font_size=S["tab"], background_normal="")
        self.tab_stats = Button(text="Статистика", font_name=FONT_REG, font_size=S["tab"], background_normal="")
        self.tab_analyze.bind(on_press=lambda x: self.show_tab("analyze"))
        self.tab_history.bind(on_press=lambda x: self.show_tab("history"))
        self.tab_stats.bind(on_press=lambda x: self.show_tab("stats"))
        for b in (self.tab_analyze, self.tab_history, self.tab_stats):
            b.size_hint_x = 1
            t.add_widget(b)
        self.add_widget(t)

    def _build_analysis_tab(self):
        self.tab_analyze_box = BoxLayout(orientation="vertical", spacing=10)
        sel = BoxLayout(size_hint_y=None, height=46, spacing=8)
        self.sport = Spinner(text=SPORTS[0], font_name=FONT_REG, font_size=S["body"], values=SPORTS,
                             size_hint=(1, None), height=46, background_color=[1, 1, 1, 1])
        self.strategy = Spinner(text=STRATEGIES[0], font_name=FONT_REG, font_size=S["body"], values=STRATEGIES,
                                size_hint=(1, None), height=46, background_color=[1, 1, 1, 1])
        self.sport.bind(text=self.on_sport_change)
        sel.add_widget(self.sport)
        sel.add_widget(self.strategy)
        self.tab_analyze_box.add_widget(sel)

        card = Card(orientation="vertical", size_hint_y=None, height=250)
        self.f_k1 = Field("Команда 1: очки/забитые", "5.2")
        self.f_k2 = Field("Команда 2: очки/забитые", "4.8")
        self.f_line = Field("Линия/гандикап", "9.5")
        self.f_cf = Field("Коэффициент БК", "1.90")
        for f in (self.f_k1, self.f_k2, self.f_line, self.f_cf):
            card.add_widget(f)
        self.tab_analyze_box.add_widget(card)

        self.btn = Button(text="Анализировать и сохранить", font_name=FONT_BOLD, font_size=S["body"],
                          size_hint_y=None, height=52, background_normal="")
        self.btn.bind(on_press=self.calculate)
        self.tab_analyze_box.add_widget(self.btn)

        self.result_card = Card(orientation="vertical", size_hint_y=None, height=180)
        self.result = Label(text="Готов к анализу.", font_name=FONT_REG, font_size=S["body2"],
                            halign="center", valign="middle")
        self.result.bind(size=lambda *a: setattr(self.result, "text_size", (self.result.width, None)))
        self.result_card.add_widget(self.result)
        self.tab_analyze_box.add_widget(self.result_card)
        self.add_widget(self.tab_analyze_box)

    def _build_history_tab(self):
        self.tab_history_box = BoxLayout(orientation="vertical", spacing=8)
        self.hist_list = Card(orientation="vertical")
        sc = ScrollView()
        sc.add_widget(self.hist_list)
        self.tab_history_box.add_widget(sc)
        self.add_widget(self.tab_history_box)

    def _build_stats_tab(self):
        self.tab_stats_box = BoxLayout(orientation="vertical", spacing=10)
        self.stats_card = Card(orientation="vertical", size_hint_y=None, height=260)
        self.stats_lbl = Label(text="Пока нет данных.", font_name=FONT_REG, font_size=S["body"],
                               halign="center", valign="middle")
        self.stats_lbl.bind(size=lambda *a: setattr(self.stats_lbl, "text_size", (self.stats_lbl.width, None)))
        self.stats_card.add_widget(self.stats_lbl)
        self.tab_stats_box.add_widget(self.stats_card)
        self.f_bank = Field("Установить банк", "10000")
        self.tab_stats_box.add_widget(self.f_bank)
        b = Button(text="Применить банк", font_name=FONT_BOLD, font_size=S["body"],
                   size_hint_y=None, height=44, background_normal="")
        b.bind(on_press=self.apply_bank)
        self.tab_stats_box.add_widget(b)
        self.manage_btns = BoxLayout(size_hint_y=None, height=80, spacing=8)
        self.tab_stats_box.add_widget(self.manage_btns)
        self.add_widget(self.tab_stats_box)

    def show_tab(self, name):
        for box, btn in [(self.tab_analyze_box, self.tab_analyze),
                         (self.tab_history_box, self.tab_history),
                         (self.tab_stats_box, self.tab_stats)]:
            active = box is getattr(self, "tab_%s_box" % name)
            box.opacity = 1 if active else 0
            box.disabled = not active
        if name == "history":
            self.render_history()
        elif name == "stats":
            self.render_stats()
        self._apply_theme()

    def toggle_theme(self, sw, value):
        self.dark = value
        self.palette = DARK if value else LIGHT
        self.settings["dark"] = value
        save_settings(self.settings)
        self._apply_theme()
        self._update_bg()

    def _apply_theme(self):
        p = self.palette
        self.title.color = p["text"]
        self.bank_lbl.color = p["subtext"]
        self.btn.background_color = p["accent"]
        self.btn.color = [1, 1, 1, 1]
        for card in (self.result_card, self.hist_list, self.stats_card):
            card.apply_theme(p)
        self.result.color = p["card_text"]
        self.stats_lbl.color = p["card_text"]
        self.sport.color = p["text"]
        self.strategy.color = p["text"]
        self.sport.background_color = [0.16, 0.16, 0.16, 1] if self.dark else [1, 1, 1, 1]
        self.strategy.background_color = self.sport.background_color
        for f in (self.f_k1, self.f_k2, self.f_line, self.f_cf, self.f_bank):
            f.lbl.color = p["subtext"]
            f.txt.color = p["card_text"]
            f.txt.background_color = [0.18, 0.18, 0.18, 1] if self.dark else [1, 1, 1, 1]
            f.txt.background_normal = ""
        states = [("analyze", self.tab_analyze_box), ("history", self.tab_history_box), ("stats", self.tab_stats_box)]
        for name, box in states:
            btn = getattr(self, "tab_" + name)
            on = box.opacity > 0
            btn.background_color = p["accent"] if on else p["card"]
            btn.color = [1, 1, 1, 1] if on else p["text"]

    def _update_bg(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.palette["bg"])
            Rectangle(pos=self.pos, size=self.size)

    def on_sport_change(self, sp, text):
        self.f_line.txt.hint_text = "Тотал партий (2.5)" if text in ("Теннис", "Настольный теннис") else "Линия тотала (9.5)"

    def _num(self, txt):
        return float((txt or "0").strip().replace(",", "."))

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
                rec = "К1" if p1 >= p2 else "К2"; prob = max(p1, p2)
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
            stake = self.stake_for(prob, cf, self.bank) if strategy == "Келли-критерий" else 0.0
            implied = 1 / cf if cf > 1 else 0
            if prob > implied + 0.05:
                verdict = "✅ Value — ставить"
            elif prob < implied - 0.05:
                verdict = "❌ Нет value"
            else:
                verdict = "⚠️ На границе"

            save_bet(sport, strategy, line, cf, prob, ev, stake, self.bank)
            self.bank -= stake
            self.settings["bank"] = self.bank
            save_settings(self.settings)
            self.bank_lbl.text = "Банк {:.0f}".format(self.bank)

            lines = ["🎯 {} — {}".format(rec, strategy),
                     "Вероятность прохода: {:.0f}%".format(prob * 100),
                     "Коэффициент {:.2f} (БК: {:.0f}%)".format(cf, implied * 100),
                     "EV: {:.3f}".format(ev),
                     verdict]
            if stake > 0:
                lines.append("Ставка: {:.0f} руб".format(stake))
            lines.append("П1 {:.0f}%  X {:.0f}%  П2 {:.0f}%".format(p1 * 100, px * 100, p2 * 100))
            self.result.text = "\n".join(lines)
            self.result.color = self.palette["green"] if "✅" in verdict else (self.palette["red"] if "❌" in verdict else self.palette["card_text"])
        except Exception:
            self.result.text = "Ошибка ввода! Проверьте числа."
            self.result.color = self.palette["red"]

    def stake_for(self, prob, cf, bank):
        if cf <= 1 or bank <= 0:
            return 0.0
        f = (prob * cf - 1) / (cf - 1)
        return max(0.0, bank * min(f * 0.25, 0.05))

    def render_history(self):
        self.hist_list.clear_widgets()
        rows = get_history()
        if not rows:
            self.hist_list.add_widget(Label(text="История пуста.", font_name=FONT_REG, font_size=S["body"], halign="center"))
            return
        for row in rows[:60]:
            hid, sport, strat, line, cf, prob, ev, stake, bank, result, created = row
            r = "—"
            if result:
                r = "✔ зашла" if result == "win" else "✘ не зашла"
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=56, spacing=6)
            info = "{} | {} | {:.0f}% | Кф {:.2f}\n{} · {}".format(sport, strat, prob * 100, cf, r, created)
            lbl = Label(text=info, font_name=FONT_REG, font_size=S["small"], halign="left", valign="middle", size_hint_x=0.72)
            lbl.bind(size=lambda *a: setattr(lbl, "text_size", (lbl.width, None)))
            box.add_widget(lbl)
            if not result:
                bw = Button(text="✔", size_hint_x=None, width=44, font_size=18, background_color=self.palette["green"], color=[1, 1, 1, 1])
                bl = Button(text="✘", size_hint_x=None, width=44, font_size=18, background_color=self.palette["red"], color=[1, 1, 1, 1])
                bw.bind(on_press=lambda x, bid=hid: self.mark(bid, "win"))
                bl.bind(on_press=lambda x, bid=hid: self.mark(bid, "lose"))
                box.add_widget(bw)
                box.add_widget(bl)
            self.hist_list.add_widget(box)

    def mark(self, bid, result):
        set_result(bid, result)
        self.render_history()
        self.render_stats()

    def render_stats(self):
        rows = get_history()
        decided = [r for r in rows if r[9]]
        wins = sum(1 for r in decided if r[9] == "win")
        losses = sum(1 for r in decided if r[9] == "lose")
        total = wins + losses
        acc = (wins / total * 100) if total else 0
        profit = sum(r[7] for r in decided if r[9] == "win") - sum(r[7] for r in decided if r[9] == "lose")
        self.stats_lbl.text = ("Всего ставок: {}\nВыигрыш: {}\nПроигрыш: {}\nТочность: {:.0f}%\n"
                               "Прибыль (подтв.): {:.0f}\nБанк: {:.0f}".format(
                                   len(decided), wins, losses, acc, profit, self.bank))
        self.manage_btns.clear_widgets()
        if rows:
            b = Button(text="Очистить историю", font_size=S["body"], bold=True,
                       background_color=self.palette["red"], color=[1, 1, 1, 1])
            b.bind(on_press=self.clear_all)
            self.manage_btns.add_widget(b)

    def apply_bank(self, inst):
        try:
            v = self._num(self.f_bank.txt.text)
            if v > 0:
                self.bank = v
                self.settings["bank"] = v
                save_settings(self.settings)
                self.bank_lbl.text = "Банк {:.0f}".format(self.bank)
                self.f_bank.txt.text = ""
        except Exception:
            pass

    def clear_all(self, inst):
        clear_history()
        self.bank = float(self.settings.get("bank", 10000))
        self.bank_lbl.text = "Банк {:.0f}".format(self.bank)
        self.render_history()
        self.render_stats()


def poisson(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


class BettingApp(App):
    def build(self):
        init_db()
        Window.clearcolor = LIGHT["bg"]
        return MainLayout()


if __name__ == "__main__":
    BettingApp().run()
