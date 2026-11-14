class ЭкранДашборда(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="Статистика", font_name=FONT_BOLD, font_size=sp(24),
                              color=тема["text"], size_hint_y=None, height=dp(40),
                              halign="left"))
        scroll = ScrollView()
        self.контент = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        self.контент.bind(minimum_height=self.контент.setter("height"))
        scroll.add_widget(self.контент)
        root.add_widget(scroll)
        self.add_widget(root)
        self.bind(on_enter=lambda *a: self.обновить())

    def обновить(self, *a):
        self.контент.clear_widgets()
        тема = получить_тему()
        try:
            стата = собрать_статистику(db)
        except Exception:
            стата = {"общая": {"всего": 0}, "по_спортам": {}}
        общ = стата.get("общая", {})
        if общ.get("всего", 0) == 0:
            self.контент.add_widget(ПустоеСостояние(
                иконка_текст="📊", заголовок="Нет данных",
                подзаголовок="Введи реальные счёта в «Истории»"))
        else:
            карт = Карточка("Общая статистика", иконка("\ue85b", "📊"))
            цвет = цвет_статуса("успех") if общ["roi"] > 0 else цвет_статуса("опасность")
            метрики = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(4))
            метрики.add_widget(Метрика(str(общ["всего"]), "прогнозов"))
            метрики.add_widget(Метрика(f"{общ['винрейт']}%", "винрейт"))
            метрики.add_widget(Метрика(f"{общ['roi']:+.1f}%", "ROI", цвет=цвет))
            карт.add_widget(метрики)
            self.контент.add_widget(карт)
            for спорт, м in стата.get("по_спортам", {}).items():
                карт_с = Карточка(спорт, "")
                цвет_с = цвет_статуса("успех") if м["roi"] > 0 else цвет_статуса("опасность")
                m_row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(4))
                m_row.add_widget(Метрика(str(м["всего"]), "прогнозов"))
                m_row.add_widget(Метрика(f"{м['винрейт']}%", "винрейт"))
                m_row.add_widget(Метрика(f"{м['roi']:+.1f}%", "ROI", цвет=цвет_с))
                карт_с.add_widget(m_row)
                self.контент.add_widget(карт_с)
        try:
            стата_стр = статистика_по_стратегиям(db)
        except Exception:
            стата_стр = {}
        if стата_стр:
            карт_стр = Карточка("Стратегии", иконка("\ue85b", "🎯"))
            for s, data in sorted(стата_стр.items(), key=lambda x: -x[1]["винрейт"]):
                if data["всего"] >= 3:
                    цвет_с = "#22c55e" if data["винрейт"] > 55 else (
                        "#facc15" if data["винрейт"] > 45 else "#ef4444")
                    lbl = Label(text=f"[color={цвет_с}]{s}: {data['винрейт']}% "
                                     f"({data['побед']}/{data['всего']})[/color]",
                                font_name=FONT_REGULAR, font_size=sp(11),
                                color=тема["text"], halign="left",
                                size_hint_y=None, height=dp(26), markup=True)
                    lbl.bind(size=lambda *a, l=lbl: setattr(l, "text_size", l.size))
                    карт_стр.add_widget(lbl)
            if len(карт_стр.children) > 1:
                self.контент.add_widget(карт_стр)
        try:
            стата_див = статистика_по_расхождению(db)
        except Exception:
            стата_див = {}
        if стата_див and any(d["всего"] >= 3 for d in стата_див.values()):
            карт_див = Карточка("Расхождение с рынком", иконка("\ue85b", "📈"))
            for кат, d in стата_див.items():
                if d["всего"] >= 3:
                    цвет_д = "#22c55e" if d["винрейт"] > 55 else (
                        "#facc15" if d["винрейт"] > 45 else "#ef4444")
                    lbl = Label(text=f"[color={цвет_д}]{кат}: {d['винрейт']}% "
                                     f"({d['побед']}/{d['всего']})[/color]",
                                font_name=FONT_REGULAR, font_size=sp(11),
                                color=тема["text"], halign="left",
                                size_hint_y=None, height=dp(26), markup=True)
                    lbl.bind(size=lambda *a, l=lbl: setattr(l, "text_size", l.size))
                    карт_див.add_widget(lbl)
            self.контент.add_widget(карт_див)


class ЭкранМонтеКарло(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="Риск (Монте-Карло)", font_name=FONT_BOLD,
                              font_size=sp(24), color=тема["text"],
                              size_hint_y=None, height=dp(40), halign="left"))
        scroll = ScrollView()
        контент = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        контент.bind(minimum_height=контент.setter("height"))
        карт = Карточка("Параметры", иконка("\ue8b8", "⚙️"))
        self.ф_винрейт = Поле("Винрейт, %", "55")
        self.ф_кэф = Поле("Коэффициент", "1.85")
        self.ф_банк = Поле("Банк", "10000")
        self.ф_келли = Поле("Доля Келли", "0.25")
        for f in (self.ф_винрейт, self.ф_кэф, self.ф_банк, self.ф_келли):
            карт.add_widget(f)
        b = Кнопка("Симулировать", "основная")
        b.bind(on_press=self.запустить)
        карт.add_widget(b)
        контент.add_widget(карт)
        self.результат_карт = Карточка("Результат", "")
        self.результат_карт.opacity = 0
        self.результат_карт.установить_высоту(0)
        self.результат_label = Label(text="", font_name=FONT_REGULAR,
                                      font_size=sp(12), color=тема["text"],
                                      size_hint_y=None, height=dp(280),
                                      halign="left", valign="top", markup=True)
        self.результат_label.bind(size=lambda *a: setattr(
            self.результат_label, "text_size", self.результат_label.size))
        self.результат_карт.add_widget(self.результат_label)
        контент.add_widget(self.результат_карт)
        scroll.add_widget(контент)
        root.add_widget(scroll)
        self.add_widget(root)

    def запустить(self, *a):
        try:
            винрейт = float(self.ф_винрейт.значение)
            кэф = float(self.ф_кэф.значение)
            банк = float(self.ф_банк.значение)
            келли = float(self.ф_келли.значение)
        except ValueError:
            Тосты.показать("Проверь числа", "опасность")
            return
        r = монте_карло(винрейт, кэф, банк, келли)
        if "error" in r:
            Тосты.показать(r["error"], "опасность")
            return
        цвет_мед = "#22c55e" if r["медиана_pct"] > 0 else "#ef4444"
        цвет_риск = "#ef4444" if r["шанс_минус_50"] > 10 else "#22c55e"
        self.результат_label.text = (
            f"[b]Келли: {r['келли_pct']}% банка[/b]\n\n"
            f"[b]Через {r['ставок']} ставок:[/b]\n"
            f"Медиана: [color={цвет_мед}][b]{r['медиана_pct']:+.1f}%[/b][/color]\n"
            f"Худшие 5%: {r['худшие_5_pct']:+.1f}%\n"
            f"Лучшие 5%: {r['лучшие_5_pct']:+.1f}%\n\n"
            f"[b]Вероятности:[/b]\n"
            f"В плюс: [b]{r['шанс_плюс']}%[/b]\n"
            f"Потерять >50%: [color={цвет_риск}][b]{r['шанс_минус_50']}%[/b][/color]\n"
            f"Удвоить: {r['шанс_плюс_50']}%\n")
        self.результат_карт.opacity = 1
        self.результат_карт._обновить_высоту()


class ЭкранНастроек(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="Настройки", font_name=FONT_BOLD, font_size=sp(24),
                              color=тема["text"], size_hint_y=None, height=dp(40),
                              halign="left"))
        scroll = ScrollView()
        контент = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        контент.bind(minimum_height=контент.setter("height"))
        карт = Карточка("Параметры", иконка("\ue8b8", "⚙️"))
        self.ф_банк = Поле("Банк", db.get_setting("bank", "10000"))
        self.ф_келли = Поле("Келли", db.get_setting("kelly", "0.25"))
        self.ф_edge = Поле("Мин. edge", db.get_setting("edge", "0.12"))
        self.ф_тема = Поле("Тема (тёмная/светлая/авто)", db.get_setting("theme", "тёмная"))
        self.ф_акцент = Поле("Акцент (синий/зелёный/фиолетовый)", db.get_setting("accent", "синий"))
        for f in (self.ф_банк, self.ф_келли, self.ф_edge, self.ф_тема, self.ф_акцент):
            карт.add_widget(f)
        b = Кнопка("Сохранить", "основная")
        b.bind(on_press=self.сохранить)
        карт.add_widget(b)
        контент.add_widget(карт)
        карт_о = Карточка("О приложении", "")
        карт_о.add_widget(Label(
            text="Betting PRO v18.0\n"
                 "4 вида спорта • 9 стратегий • Автоанализ\n"
                 "Работает офлайн • Аналитика, не гарантия",
            font_name=FONT_REGULAR, font_size=sp(11),
            color=тема["muted"], size_hint_y=None, height=dp(70), halign="center"))
        контент.add_widget(карт_о)
        scroll.add_widget(контент)
        root.add_widget(scroll)
        self.add_widget(root)

    def сохранить(self, *a):
        try:
            db.set_setting("bank", float(self.ф_банк.значение))
            db.set_setting("kelly", float(self.ф_келли.значение))
            db.set_setting("edge", float(self.ф_edge.значение))
            db.set_setting("theme", self.ф_тема.значение)
            db.set_setting("accent", self.ф_акцент.значение)
            Тосты.показать("Сохранено. Перезапусти", "успех")
        except ValueError:
            Тосты.показать("Проверь числа", "опасность")


class BettingProApp(App):
    def build(self):
        self.title = "Betting PRO v18.0"
        if db.get_setting("onboarding", "0") != "1":
            return Онбординг(on_finish=self._после_онбординга)
        return self._создать_основное()

    def _после_онбординга(self):
        db.set_setting("onboarding", "1")
        Clock.schedule_once(lambda dt: self._заменить_root(), 0.1)

    def _заменить_root(self):
        try:
            новый = self._создать_основное()
            if self.root:
                self.root.clear_widgets()
            self.root = новый
        except Exception as e:
            print(f"Ошибка перехода: {e}")
            try:
                db.set_setting("onboarding", "1")
            except Exception:
                pass

    def _создать_основное(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(ЭкранПрогноза(name="прогноз"))
        sm.add_widget(ЭкранКоманд(name="команды"))
        sm.add_widget(ЭкранДашборда(name="дашборд"))
        sm.add_widget(ЭкранСтратегий(name="стратегии"))
        sm.add_widget(ЭкранМонтеКарло(name="монтекарло"))
        sm.add_widget(ЭкранИстории(name="история"))
        sm.add_widget(ЭкранНастроек(name="настройки"))

        тема = получить_тему()
        root = BoxLayout(orientation="vertical")
        root.add_widget(sm)

        nav = BoxLayout(size_hint_y=None, height=dp(58))
        with nav.canvas.before:
            Color(*тема["card"])
            nav_bg = Rectangle(pos=nav.pos, size=nav.size)
        nav.bind(pos=lambda *a: setattr(nav_bg, "pos", nav.pos),
                 size=lambda *a: setattr(nav_bg, "size", nav.size))

        вкладки = [
            ("прогноз", "🎯", "Прогноз"),
            ("команды", "👥", "Команды"),
            ("дашборд", "📊", "Стата"),
            ("стратегии", "⚙️", "Страт."),
            ("монтекарло", "🎲", "Риск"),
            ("история", "📜", "История"),
        ]

        for ключ, эмодзи, текст in вкладки:
            b = BoxLayout(orientation="vertical")
            btn = Button(text=эмодзи, font_size=sp(20),
                         background_normal="", background_color=(0, 0, 0, 0),
                         color=получить_акцент() if ключ == "прогноз" else тема["muted"])
            btn.bind(on_press=lambda x, k=ключ: setattr(sm, "current", k))
            b.add_widget(btn)
            lbl = Label(text=текст, font_name=FONT_REGULAR, font_size=sp(9),
                        color=тема["muted"])
            b.add_widget(lbl)
            nav.add_widget(b)

        root.add_widget(nav)
        return root


if __name__ == "__main__":
    BettingProApp().run()