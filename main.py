from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import rgba
import math

LIGHT = {
    "bg": rgba("#F2F2F7"), "card": rgba("#FFFFFF"),
    "accent": rgba("#007AFF"), "text": rgba("#1C1C1E"),
    "subtext": rgba("#8E8E93"), "card_text": rgba("#1C1C1E"),
}
DARK = {
    "bg": rgba("#000000"), "card": rgba("#1C1C1E"),
    "accent": rgba("#0A84FF"), "text": rgba("#FFFFFF"),
    "subtext": rgba("#8E8E93"), "card_text": rgba("#FFFFFF"),
}

SPORTS = ["Хоккей", "Футбол", "Теннис", "Настольный теннис"]
STRATEGIES = [
    "Тотал больше (ТБ)", "Тотал меньше (ТМ)", "Двойной шанс (1X)",
    "Двойной шанс (X2)", "Победа фаворита", "Value-ставка (EV)",
    "Келли-критерий", "Обе забьют (Футбол)", "Тотал ТБ с запасом"
]


class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(padding=[16, 16, 16, 16], spacing=12, **kwargs)
        self.palette = LIGHT
        with self.canvas.before:
            Color(*self.palette["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[16, 16, 16, 16])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def apply_theme(self, palette):
        self.palette = palette
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*palette["card"])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[16, 16, 16, 16])


class Field(BoxLayout):
    def __init__(self, label, hint, **kwargs):
        super().__init__(orientation="vertical", spacing=6, **kwargs)
        self.lbl = Label(text=label, font_size=13, halign="left", size_hint_y=None, height=18)
        self.lbl.bind(size=lambda *a: setattr(self.lbl, "text_size", (self.lbl.width, None)))
        self.txt = TextInput(
            hint_text=hint, multiline=False, background_color=[1, 1, 1, 1],
            background_normal="", padding=[12, 10, 12, 10], font_size=17
        )
        self.add_widget(self.lbl)
        self.add_widget(self.txt)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[20, 40, 20, 20], spacing=14)
        self.dark = False
        self.palette = LIGHT
        self.bind(size=self._update_bg, pos=self._update_bg)

        top = BoxLayout(size_hint_y=None, height=50, spacing=12)
        self.title = Label(text="Аналитика ставок", font_size=28, bold=True)
        self.theme_btn = ToggleButton(text="🌙", size_hint_x=None, width=56,
                                      background_normal="", font_size=20)
        self.theme_btn.bind(on_press=self.toggle_theme)
        top.add_widget(self.title)
        top.add_widget(self.theme_btn)
        self.add_widget(top)

        sel = BoxLayout(size_hint_y=None, height=110, spacing=10)
        self.sport = Spinner(text="Хоккей", values=SPORTS, size_hint=(1, None), height=46)
        self.strategy = Spinner(text=STRATEGIES[0], values=STRATEGIES, size_hint=(1, None), height=46)
        self.sport.bind(text=self.on_sport_change)
        sel.add_widget(BoxLayout(orientation="vertical", children=[Label(text="Вид спорта", font_size=12, size_hint_y=None, height=20), self.sport], spacing=4))
        sel.add_widget(BoxLayout(orientation="vertical", children=[Label(text="Стратегия", font_size=12, size_hint_y=None, height=20), self.strategy], spacing=4))
        self.add_widget(sel)

        self.card = Card(orientation="vertical", size_hint_y=None, height=330)
        self.f_k1 = Field("Забитые / очки К1", "5.2")
        self.f_k2 = Field("Забитые / очки К2", "4.8")
        self.f_line = Field("Линия / гандикап", "9.5")
        self.f_cf = Field("Коэффициент БК", "1.90")
        self.f_bank = Field("Банк (для Келли)", "10000")
        for f in [self.f_k1, self.f_k2, self.f_line, self.f_cf, self.f_bank]:
            self.card.add_widget(f)
        self.add_widget(self.card)

        self.btn = Button(text="Рассчитать", size_hint_y=None, height=52, bold=True, font_size=18,
                          background_normal="")
        self.btn.bind(on_press=self.calculate)
        self.add_widget(self.btn)

        self.result_card = Card(orientation="vertical", size_hint_y=None, height=230)
        self.result = Label(text="Ожидание данных...", font_size=16, halign="center", valign="middle")
        self.result.bind(size=self._fit_result)
        self.result_card.add_widget(self.result)
        self.add_widget(self.result_card)

        self._apply_theme()

    def _fit_result(self, *a):
        self.result.text_size = (self.result.width, None)

    def _update_bg(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.palette["bg"])
            Rectangle(pos=self.pos, size=self.size)

    def on_sport_change(self, spinner, text):
        if text in ("Теннис", "Настольный теннис"):
            self.f_line.txt.hint_text = "Тотал сетов (2.5)"
        else:
            self.f_line.txt.hint_text = "Линия тотала (9.5)"

    def toggle_theme(self, inst):
        self.dark = not self.dark
        self.palette = DARK if self.dark else LIGHT
        self._apply_theme()
        self._update_bg()

    def _apply_theme(self):
        p = self.palette
        self.title.color = p["text"]
        self.btn.background_color = p["accent"]
        self.btn.color = [1, 1, 1, 1]
        self.theme_btn.background_color = p["accent"]
        self.theme_btn.color = [1, 1, 1, 1]
        for w in [self.card, self.result_card]:
            w.apply_theme(p)
        self.result.color = p["card_text"]
        self.sport.color = p["text"]
        self.strategy.color = p["text"]
        for f in [self.f_k1, self.f_k2, self.f_line, self.f_cf, self.f_bank]:
            f.lbl.color = p["subtext"]
            f.txt.color = p["card_text"]
            f.txt.hint_text_color = p["subtext"]
            f.txt.background_color = [0.15, 0.15, 0.15, 1] if self.dark else [1, 1, 1, 1]
            f.txt.background_normal = ""

    def _num(self, txt):
        return float((txt or "0").replace(",", "."))

    def probability_model(self, sport, a, b, line):
        if sport in ("Хоккей", "Футбол"):
            a = a or 0.1
            b = b or 0.1
            p1 = px = p2 = 0.0
            for g1 in range(16):
                for g2 in range(16):
                    p = poisson(g1, a) * poisson(g2, b)
                    if g1 > g2: p1 += p
                    elif g1 == g2: px += p
                    else: p2 += p
            return p1, px, p2
        else:
            a = max(a, 0.1)
            b = max(b, 0.1)
            tot = a + b
            p1 = a / tot
            p2 = b / tot
            px = 1 - (p1 + p2)
            return p1, px, p2

    def calculate(self, inst):
        try:
            sport = self.sport.text
            strategy = self.strategy.text
            a = self._num(self.f_k1.txt.text)
            b = self._num(self.f_k2.txt.text)
            line = self._num(self.f_line.txt.text)
            cf = self._num(self.f_cf.txt.text)
            bank = self._num(self.f_bank.txt.text)

            p1, px, p2 = self.probability_model(sport, a, b, line)

            if strategy == "Тотал больше (ТБ)" or strategy == "Тотал ТБ с запасом":
                total = a + b
                th = int(math.ceil(line))
                p = 1 - sum(poisson(k, total) for k in range(max(th, 1)))
                rec = "Ставка ТБ {}".format(line)
                prob = p
            elif strategy == "Тотал меньше (ТМ)":
                total = a + b
                th = int(math.ceil(line))
                p_over = 1 - sum(poisson(k, total) for k in range(max(th, 1)))
                rec = "Ставка ТМ {}".format(line)
                prob = 1 - p_over
            elif strategy == "Двойной шанс (1X)":
                rec, prob = "Двойной шанс 1X", p1 + px
            elif strategy == "Двойной шанс (X2)":
                rec, prob = "Двойной шанс X2", px + p2
            elif strategy == "Победа фаворита":
                rec = "Победа фаворита (К1)" if p1 >= p2 else "Победа фаворита (К2)"
                prob = max(p1, p2)
            elif strategy == "Обе забьют (Футбол)":
                p_btts = 1 - (poisson(0, a or 0.1) * poisson(0, b or 0.1))
                rec, prob = "Обе забьют (BTTS)", p_btts
            elif strategy in ("Value-ставка (EV)", "Келли-критерий"):
                probs = [p1, px, p2]
                best = max(probs)
                label = ["К1", "X", "К2"][probs.index(best)]
                ev = best * cf - 1
                if strategy == "Келли-критерий" and bank > 0:
                    b_kelly = (best * cf - 1) / (cf - 1) if cf > 1 else 0
                    stake = max(0.0, bank * min(b_kelly * 0.25, 0.05))
                    rec = "Ставка на {} (Келли)".format(label)
                    prob = best
                    extra = "\nРазмер ставки: {:.0f} руб".format(stake)
                else:
                    rec = "Ставка на {} (Value)".format(label)
                    prob = best
                    extra = ""
                self.result.text = "{}\nВероятность: {:.0f}%\nEV: {:.3f}{}\nП1 {:.0f}%  X {:.0f}%  П2 {:.0f}%".format(
                    rec, prob * 100, ev, extra, p1 * 100, px * 100, p2 * 100)
                return
            else:
                rec, prob = "Нет стратегии", 0

            self.result.text = "{}\nВероятность: {:.0f}%\nКоэффициент {} → EV {:.3f}\nП1 {:.0f}%  X {:.0f}%  П2 {:.0f}%\nТотал: {:.2f}".format(
                rec, prob * 100, cf, prob * cf - 1, p1 * 100, px * 100, p2 * 100, a + b)
        except Exception:
            self.result.text = "Ошибка ввода! Проверьте числа."


def poisson(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


class BettingApp(App):
    def build(self):
        Window.clearcolor = LIGHT["bg"]
        return MainLayout()


if __name__ == "__main__":
    BettingApp().run()
