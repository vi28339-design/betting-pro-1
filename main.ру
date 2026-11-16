from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
import math

Window.clearcolor = (0.06, 0.09, 0.16, 1)


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_over(expected, line):
    threshold = math.ceil(line)
    p_less = sum(poisson_pmf(k, expected) for k in range(threshold))
    return 1 - p_less


def predict_hockey(exp1, exp2):
    if exp1 <= 0:
        exp1 = 0.1
    if exp2 <= 0:
        exp2 = 0.1
    p1 = px = p2 = 0.0
    for g1 in range(16):
        pg1 = poisson_pmf(g1, exp1)
        for g2 in range(16):
            p = pg1 * poisson_pmf(g2, exp2)
            if g1 > g2:
                p1 += p
            elif g1 == g2:
                px += p
            else:
                p2 += p
    return {"p1": p1, "px": px, "p2": p2, "total_exp": exp1 + exp2}


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=30, spacing=15, **kwargs)
        self.add_widget(Label(text="Betting PRO", font_size=32, color=(1, 1, 1, 1), size_hint_y=None, height=50))
        self.t1 = TextInput(hint_text="Забитые К1 (напр. 5.2)", multiline=False, size_hint_y=None, height=50)
        self.t2 = TextInput(hint_text="Забитые К2 (напр. 4.8)", multiline=False, size_hint_y=None, height=50)
        self.line = TextInput(hint_text="Линия (напр. 9.5)", multiline=False, size_hint_y=None, height=50)
        self.add_widget(self.t1)
        self.add_widget(self.t2)
        self.add_widget(self.line)
        btn = Button(text="РАССЧИТАТЬ", size_hint_y=None, height=60, background_color=(0.2, 0.5, 0.9, 1), bold=True)
        btn.bind(on_press=self.calculate)
        self.add_widget(btn)
        self.result = Label(text="Ожидание данных...", font_size=18, color=(1, 1, 1, 1), halign="center", valign="middle")
        self.result.bind(size=self.result.setter("text_size"))
        self.add_widget(self.result)

    def calculate(self, instance):
        try:
            v1 = self.t1.text.strip() or "0"
            v2 = self.t2.text.strip() or "0"
            vl = self.line.text.strip() or "0"
            t1 = float(v1)
            t2 = float(v2)
            line = float(vl)
            if line <= 0:
                self.result.text = "Ошибка: линия должна быть больше 0!"
                return
            r = predict_hockey(t1, t2)
            p_over = poisson_over(r["total_exp"], line)
            p_under = 1 - p_over
            if p_over > 0.55:
                rec = "СТАВКА: ТБ {}\nВероятность: {:.1f}%".format(line, p_over * 100)
            elif p_under > 0.55:
                rec = "СТАВКА: ТМ {}\nВероятность: {:.1f}%".format(line, p_under * 100)
            else:
                rec = "НЕТ СИГНАЛА (Пропустить)"
            self.result.text = "{}\n\nОжидаемый тотал: {:.2f}".format(rec, r["total_exp"])
        except ValueError:
            self.result.text = "Ошибка: введите числа!"


class BettingApp(App):
    def build(self):
        return MainScreen()


if __name__ == "__main__":
    BettingApp().run()
