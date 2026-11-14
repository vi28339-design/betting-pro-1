from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.metrics import dp


class ГрафикБанка(Widget):
    def __init__(self, данные=None, **kw):
        super().__init__(**kw)
        self.данные = данные or []
        self.bind(pos=self.перерисовать, size=self.перерисовать)

    def установить(self, данные):
        self.данные = данные
        self.перерисовать()

    def перерисовать(self, *a):
        self.canvas.clear()
        if len(self.данные) < 2:
            return
        мин = min(self.данные)
        макс = max(self.данные)
        диапазон = (макс - мин) or 1
        отступ = dp(20)
        ширина = self.width - отступ * 2
        высота = self.height - отступ * 2
        if ширина <= 0 or высота <= 0:
            return
        шаг = ширина / (len(self.данные) - 1)
        точки = []
        for i, v in enumerate(self.данные):
            x = self.x + отступ + i * шаг
            y = self.y + отступ + (v - мин) / диапазон * высота
            точки.extend([x, y])
        with self.canvas:
            Color(0.12, 0.16, 0.25, 1)
            Rectangle(pos=(self.x + отступ, self.y + отступ),
                      size=(ширина, высота))
            if мин < 0 < макс:
                Color(0.94, 0.27, 0.27, 0.5)
                y0 = self.y + отступ + (0 - мин) / диапазон * высота
                Line(points=[self.x + отступ, y0,
                             self.x + отступ + ширина, y0],
                     width=1, dash=[4, 4])
            Color(0.23, 0.51, 0.96, 1)
            Line(points=точки, width=dp(2))
            for i in range(0, len(точки), 2):
                if i // 2 == len(self.данные) - 1:
                    Color(0.13, 0.77, 0.37, 1)
                    r = dp(5)
                else:
                    Color(0.6, 0.75, 1, 1)
                    r = dp(3)
                Ellipse(pos=(точки[i] - r / 2, точки[i + 1] - r / 2), size=(r, r))