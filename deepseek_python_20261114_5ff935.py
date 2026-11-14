    def анализ(self, *a):
        спорт = self.sp_спорт.text
        try:
            банк = float(self.ф_банк.значение or 0)
        except ValueError:
            Тосты.показать("Проверь банк", "опасность")
            return
        try:
            спорт, значения = self._собрать_значения()
            кэфы = self._собрать_кэфы()
            if спорт in ("шорт-хоккей", "футбол"):
                линия = float(self.ф_линия.значение)
                for имя, val in [("К1 заброшенных", значения["к1з"]),
                                  ("К1 пропущенных", значения["к1п"]),
                                  ("К2 заброшенных", значения["к2з"]),
                                  ("К2 пропущенных", значения["к2п"])]:
                    ок, ошибка = validate_input(val, val, 9.5, спорт)
                    if not ок:
                        Тосты.показать(f"{имя}: {ошибка}", "опасность")
                        return
                r = универсальный_прогноз(спорт, значения)
                p_тб_сырая = poisson_over(r["total_exp"], линия)
                p_тб = calibrate_probability(p_тб_сырая, slope=0.85)
                p_тм = 1 - p_тб
                исходы = {"П1": r["p1"], "X": r["px"], "П2": r["p2"]}
                лучший = max(исходы, key=исходы.get)
                лучшая_p = исходы[лучший]
                if p_тб > 0.55:
                    текст, p_показ, цвет = f"📈 ТБ {линия}", p_тб, цвет_статуса("успех")
                elif p_тм > 0.55:
                    текст, p_показ, цвет = f"📉 ТМ {линия}", p_тм, цвет_статуса("успех")
                else:
                    текст, p_показ, цвет = f"⚖️ {лучший}", лучшая_p, цвет_статуса("предупреждение")
                расхождение_текст = ""
                div_тб = 0.0
                try:
                    к_тб_val = кэфы.get("тб", 0)
                    к_тм_val = кэфы.get("тм", 0)
                    if к_тб_val > 1.01 and к_тм_val > 1.01:
                        div_тб, fair_тб = odds_divergence(p_тб, (к_тб_val, к_тм_val), "over")
                        div_тм, fair_тм = odds_divergence(p_тм, (к_тб_val, к_тм_val), "under")
                        текст_тб, _ = интерпретация_расхождения(div_тб)
                        текст_тм, _ = интерпретация_расхождения(div_тм)
                        расхождение_текст = (
                            f"\n[b]📊 Расхождение с рынком:[/b]\n"
                            f"ТБ: модель {p_тб*100:.1f}% vs рынок {fair_тб*100:.1f}%\n"
                            f"  {текст_тб}\n"
                            f"ТМ: модель {p_тм*100:.1f}% vs рынок {fair_тм*100:.1f}%\n"
                            f"  {текст_тм}\n")
                except (ValueError, ZeroDivisionError):
                    pass
                келли_текст = ""
                try:
                    if банк > 0 and кэфы["тб"] > 1.01 and кэфы["тм"] > 1.01:
                        e_тб = p_тб - (1/кэфы["тб"]) / (1/кэфы["тб"] + 1/кэфы["тм"])
                        e_тм = p_тм - (1/кэфы["тм"]) / (1/кэфы["тб"] + 1/кэфы["тм"])
                        ст_тб = kelly_stake(банк, p_тб, кэфы["тб"])
                        ст_тм = kelly_stake(банк, p_тм, кэфы["тм"])
                        келли_текст = (
                            f"\n[b]💰 Расчёт ставки:[/b]\n"
                            f"ТБ: edge {e_тб*100:+.1f}% → ставка {ст_тб:.0f}\n"
                            f"ТМ: edge {e_тм*100:+.1f}% → ставка {ст_тм:.0f}\n")
                        if e_тб > 0.12 and ст_тб > 0:
                            келли_текст += "[color=#22c55e]→ ТБ выгоден[/color]\n"
                        if e_тм > 0.12 and ст_тм > 0:
                            келли_текст += "[color=#22c55e]→ ТМ выгоден[/color]\n"
                except (ValueError, ZeroDivisionError):
                    pass
                ex = r.get("exact_score", (0, 0))
                детали = (f"[b]Сырая P(ТБ):[/b] {p_тб_сырая*100:.1f}% → "
                          f"[b]калиброванная:[/b] {p_тб*100:.1f}%\n"
                          f"П1 {r['p1']*100:.1f}% | X {r['px']*100:.1f}% | П2 {r['p2']*100:.1f}%\n")
                if спорт == "шорт-хоккей":
                    детали += f"С ОТ: П1 {r['p1_ot']*100:.1f}% | П2 {r['p2_ot']*100:.1f}%\n"
                детали += (f"Ожид. тотал: {r['total_exp']:.2f}\n"
                           f"Счёт: {ex[0]}:{ex[1]}\n")
                детали += расхождение_текст + келли_текст
                self.детали.text = детали
                решение = f"{лучший}/{'ТБ' if p_тб > 0.55 else 'ТМ' if p_тм > 0.55 else '—'}"
                db.save_prediction(спорт, self.sp_к1.text, self.sp_к2.text,
                                   линия, r, решение, self.ф_заметка.значение,
                                   strategies="", divergence=div_тб)
                эмодзи = "🏒" if спорт == "шорт-хоккей" else "⚽"
                self._последний_прогноз = f"{эмодзи} {self.sp_к1.text} vs {self.sp_к2.text}\n{текст}"
            else:
                r = универсальный_прогноз(спорт, значения)
                p1 = calibrate_probability(r["p1"], slope=0.85)
                p2 = 1 - p1
                лучший = "П1" if p1 > p2 else "П2"
                лучшая_p = max(p1, p2)
                p_показ = лучшая_p
                эмодзи = "🎾" if спорт == "теннис" else "🏓"
                текст = f"{эмодзи} {лучший}"
                цвет = цвет_статуса("успех") if лучшая_p > 0.6 else цвет_статуса("предупреждение")
                self.детали.text = (f"П1: {p1*100:.1f}% | П2: {p2*100:.1f}%\n"
                                    f"Elo: {r['elo_diff']:+.0f}\n"
                                    f"Сет: {r['p_set']*100:.1f}%\n")
                db.save_prediction(спорт, self.ф_игрок1.значение or "Игрок 1",
                                   self.ф_игрок2.значение or "Игрок 2",
                                   0, r, лучший, self.ф_заметка.значение,
                                   strategies="", divergence=0)
                self._последний_прогноз = f"{эмодзи} {self.ф_игрок1.значение} vs {self.ф_игрок2.значение}"
        except ValueError as e:
            Тосты.показать(f"Проверь числа: {e}", "опасность")
            return
        except Exception as e:
            Тосты.показать(f"Ошибка: {e}", "опасность")
            return
        self.рекомендация_большая.text = текст
        self.рекомендация_большая.color = цвет
        self.вероятность.text = f"{p_показ*100:.1f}%"
        self.прогресс._цвет = цвет
        self.прогресс.установить(p_показ * 100, animate=True)
        self.карт_результат.opacity = 1
        self.карт_результат._обновить_высоту()
        появление(self.карт_результат)
        if p_показ > 0.6:
            пульсировать(self.рекомендация_большая)
        else:
            остановить_пульсацию(self.рекомендация_большая)
        Тосты.показать("Прогноз готов", "успех")

    def автоанализ(self, *a):
        try:
            банк = float(self.ф_банк.значение or 0)
        except ValueError:
            банк = 0
        try:
            спорт, значения = self._собрать_значения()
            кэфы = self._собрать_кэфы()
            if спорт in ("шорт-хоккей", "футбол"):
                линия = float(self.ф_линия.значение)
            else:
                линия = 999
            r = универсальный_прогноз(спорт, значения)
            включённые = db.all_strategy_settings()
            результат = автоматический_анализ(значения, r, линия, кэфы, включённые)
            сработали = результат["сработали"]
            сила = результат["сила"]
            лучшая = результат["лучшая"]

            if not сработали or сила < 3:
                self.рекомендация_большая.text = "🚫 Пропусти"
                self.рекомендация_большая.color = цвет_статуса("опасность")
                self.вероятность.text = f"Слабый сигнал (сила {сила})"
                self.текст_ставки.text = "Лучше не ставить"
                детали = "[b]🚫 Матч не подходит для ставки[/b]\n\n"
                if not сработали:
                    детали += "Ни одна стратегия не сработала.\n"
                else:
                    детали += f"Сила сигнала слишком мала ({сила} < 3).\n\n[b]Что сработало:[/b]\n"
                    for s in сработали:
                        детали += f"• {s['текст']} (вес {s['вес']})\n"
                детали += "\n[i]Пропусти матч, дождись явного сигнала.[/i]"
                self.детали.text = детали
                self._детали_развёрнуты = True
                self.кнопка_подробнее.text = "▲ Свернуть"
                Animation(height=dp(220), duration=0.25).start(self.детали)
                self.карт_результат.opacity = 1
                self.карт_результат._обновить_высоту()
                остановить_пульсацию(self.рекомендация_большая)
                Тосты.показать("🚫 Лучше пропустить", "предупреждение")
                return

            if сила >= 5:
                сигнал_текст = "🔥 Сильный сигнал"
                цвет = цвет_статуса("успех")
            else:
                сигнал_текст = "✅ Умеренный сигнал"
                цвет = цвет_статуса("предупреждение")
            self.рекомендация_большая.text = f"→ {лучшая}" if лучшая else "Нет рекомендации"
            self.рекомендация_большая.color = цвет
            self.вероятность.text = f"Сила: {сила}"
            self.прогресс._цвет = цвет
            self.прогресс.установить(min(100, сила * 20), animate=True)
            текст_ставки = ""
            if лучшая == "П1" and кэфы["п1"] > 1.01:
                ст = kelly_stake(банк, r["p1"], кэфы["п1"])
                текст_ставки = f"💰 Ставка: {ст:.0f}"
            elif лучшая == "П2" and кэфы["п2"] > 1.01:
                ст = kelly_stake(банк, r["p2"], кэфы["п2"])
                текст_ставки = f"💰 Ставка: {ст:.0f}"
            elif лучшая and "ТБ" in лучшая and кэфы["тб"] > 1.01:
                p_тб = calibrate_probability(poisson_over(r["total_exp"], линия))
                ст = kelly_stake(банк, p_тб, кэфы["тб"])
                текст_ставки = f"💰 Ставка: {ст:.0f}"
            elif лучшая and "ТМ" in лучшая and кэфы["тм"] > 1.01:
                p_тм = 1 - calibrate_probability(poisson_over(r["total_exp"], линия))
                ст = kelly_stake(банк, p_тм, кэфы["тм"])
                текст_ставки = f"💰 Ставка: {ст:.0f}"
            self.текст_ставки.text = текст_ставки
            детали = f"[b]{сигнал_текст}[/b]\n\n[b]Сработали стратегии:[/b]\n"
            for s in сработали:
                детали += f"• {s['текст']} (вес {s['вес']}) → {s.get('рекомендация', '—')}\n"
            if результат["рекомендации"]:
                детали += "\n[b]Рекомендации по силе:[/b]\n"
                for рек, сила_рек in sorted(результат["рекомендации"].items(), key=lambda x: -x[1]):
                    детали += f"→ {рек}: сила {сила_рек}\n"
            self.детали.text = детали
            self._детали_развёрнуты = True
            self.кнопка_подробнее.text = "▲ Свернуть"
            Animation(height=dp(220), duration=0.25).start(self.детали)
            self.карт_результат.opacity = 1
            self.карт_результат._обновить_высоту()
            появление(self.карт_результат)
            if сила >= 5:
                пульсировать(self.рекомендация_большая)
            else:
                остановить_пульсацию(self.рекомендация_большая)
            стратегии_строка = ",".join(s.get("имя", s["текст"]) for s in сработали)
            линия_сохр = линия if спорт in ("шорт-хоккей", "футбол") else 0
            db.save_prediction(спорт, self.sp_к1.text or "Игрок 1",
                               self.sp_к2.text or "Игрок 2",
                               линия_сохр, r, лучшая or "—",
                               self.ф_заметка.значение,
                               strategies=стратегии_строка, divergence=0)
            Тосты.показать(f"Автоанализ: {сигнал_текст}",
                           "успех" if сила >= 5 else "предупреждение")
        except ValueError as e:
            Тосты.показать(f"Проверь числа: {e}", "опасность")
        except Exception as e:
            Тосты.показать(f"Ошибка: {e}", "опасность")

    def поделиться(self, *a):
        if not self._последний_прогноз:
            Тосты.показать("Сначала сделай прогноз", "предупреждение")
            return
        if not share_text(self._последний_прогноз):
            диалог("Прогноз", self._последний_прогноз)


class ЭкранКоманд(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="Команды", font_name=FONT_BOLD, font_size=sp(24),
                              color=тема["text"], size_hint_y=None, height=dp(40),
                              halign="left"))
        scroll = ScrollView()
        контент = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        контент.bind(minimum_height=контент.setter("height"))
        self.sp_спорт = Spinner(text="шорт-хоккей",
            values=["шорт-хоккей", "футбол", "теннис", "настольный теннис"],
            size_hint_y=None, height=dp(44), background_normal="",
            background_color=тема["input_bg"], color=тема["text"])
        self.sp_спорт.bind(text=lambda *a: self.обновить())
        карт1 = Карточка("Новая команда", иконка("\ue7fb", "👥"))
        карт1.add_widget(self.sp_спорт)
        self.ф_имя = Поле("Название", "")
        self.ф_з = Поле("Заброшенных", "4.5")
        self.ф_п = Поле("Пропущенных", "4.5")
        self.ф_форма = Поле("Форма (ВВПНВ)", "")
        self.ф_эло = Поле("Elo", "1500")
        for f in (self.ф_имя, self.ф_з, self.ф_п, self.ф_форма, self.ф_эло):
            карт1.add_widget(f)
        b = Кнопка("Сохранить", "основная")
        b.bind(on_press=self.сохранить)
        карт1.add_widget(b)
        контент.add_widget(карт1)
        self.список = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.список.bind(minimum_height=self.список.setter("height"))
        контент.add_widget(self.список)
        scroll.add_widget(контент)
        root.add_widget(scroll)
        self.add_widget(root)
        self.bind(on_enter=lambda *a: self.обновить())
        self.обновить()

    def сохранить(self, *a):
        try:
            имя = self.ф_имя.значение
            if not имя:
                Тосты.показать("Введи название", "предупреждение")
                return
            з = float(self.ф_з.значение or 0)
            п = float(self.ф_п.значение or 0)
            эло = float(self.ф_эло.значение or 1500)
            db.save_team(имя, з, п, self.ф_форма.значение, эло, self.sp_спорт.text)
            self.обновить()
            Тосты.показать(f"{имя} сохранён", "успех")
        except ValueError:
            Тосты.показать("Проверь числа", "опасность")

    def обновить(self):
        self.список.clear_widgets()
        спорт = self.sp_спорт.text
        тема = получить_тему()
        for row in db.all_teams(спорт):
            имя, з, п, форма, эло = row
            row_ui = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(6))
            info = Label(text=f"[b]{имя}[/b]\n{з:.1f}/{п:.1f} • Elo {эло:.0f}",
                         font_name=FONT_REGULAR, font_size=sp(12),
                         color=тема["text"], halign="left", valign="middle", markup=True)
            info.bind(size=lambda *a, l=info: setattr(l, "text_size", l.size))
            row_ui.add_widget(info)
            btn = Button(text="🗑", size_hint=(None, 1), width=dp(50),
                         background_normal="", background_color=цвет_статуса("опасность"),
                         color=(1, 1, 1, 1), font_size=sp(14))
            btn.bind(on_press=lambda x, n=имя, s=спорт: (db.delete_team(n, s), self.обновить()))
            row_ui.add_widget(btn)
            self.список.add_widget(row_ui)


class ЭкранИстории(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="История", font_name=FONT_BOLD, font_size=sp(24),
                              color=тема["text"], size_hint_y=None, height=dp(40),
                              halign="left"))
        scroll = ScrollView()
        self.список = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.список.bind(minimum_height=self.список.setter("height"))
        scroll.add_widget(self.список)
        root.add_widget(scroll)
        self.add_widget(root)
        self.bind(on_enter=lambda *a: self.обновить())
        self.обновить()

    def обновить(self):
        self.список.clear_widgets()
        история = db.history(50)
        тема = получить_тему()
        if not история:
            self.список.add_widget(ПустоеСостояние(
                иконка_текст="📭", заголовок="Пока нет прогнозов",
                подзаголовок="Сделай первый прогноз во вкладке «Прогноз»"))
            return
        for h in история:
            hid, спорт, t1, t2, line, rec, ex, actual, note, dt = h
            карт = BoxLayout(orientation="vertical", size_hint_y=None,
                              height=dp(80), spacing=dp(4), padding=dp(10))
            with карт.canvas.before:
                Color(*тема["card"])
                bg = RoundedRectangle(pos=карт.pos, size=карт.size, radius=[dp(10)])
            карт.bind(pos=lambda *a, b=bg, c=карт: (setattr(b, "pos", c.pos), setattr(b, "size", c.size)),
                      size=lambda *a, b=bg, c=карт: (setattr(b, "pos", c.pos), setattr(b, "size", c.size)))
            текст = f"[b]{t1} vs {t2}[/b] ({спорт})\n"
            текст += f"Прогноз: {rec} | Счёт: {ex}"
            if actual:
                текст += f" | [b]Факт: {actual}[/b]"
            lbl = Label(text=текст, font_name=FONT_REGULAR, font_size=sp(11),
                        color=тема["text"], halign="left", valign="middle", markup=True)
            lbl.bind(size=lambda *a, l=lbl: setattr(l, "text_size", l.size))
            карт.add_widget(lbl)
            row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(6))
            inp = TextInput(hint_text="напр. 6:4", multiline=False,
                            font_size=sp(11), background_normal="",
                            background_color=тема["input_bg"],
                            foreground_color=тема["text"],
                            padding=[dp(8), dp(6)])
            row.add_widget(inp)
            btn = Button(text="✓", size_hint=(None, 1), width=dp(50),
                         background_normal="", background_color=цвет_статуса("успех"),
                         color=(1, 1, 1, 1), font_size=sp(14))
            btn.bind(on_press=lambda x, i=hid, f=inp: self._сохранить(i, f))
            row.add_widget(btn)
            карт.add_widget(row)
            self.список.add_widget(карт)

    def _сохранить(self, hid, field):
        score = field.text.strip()
        if not score or ":" not in score:
            return
        try:
            int(score.split(":")[0])
            int(score.split(":")[1])
        except (ValueError, IndexError):
            Тосты.показать("Формат: 6:4", "опасность")
            return
        db.set_actual_score(hid, score)
        Тосты.показать("Сохранено", "успех")
        self.обновить()


class ЭкранСтратегий(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        тема = получить_тему()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(Label(text="Стратегии", font_name=FONT_BOLD, font_size=sp(24),
                              color=тема["text"], size_hint_y=None, height=dp(40),
                              halign="left"))
        подпись = Label(text="Отключи стратегии с винрейтом < 50%",
                        font_name=FONT_REGULAR, font_size=sp(12),
                        color=тема["muted"], size_hint_y=None, height=dp(40),
                        halign="left", valign="top")
        подпись.bind(size=lambda *a: setattr(подпись, "text_size", подпись.size))
        root.add_widget(подпись)
        scroll = ScrollView()
        self.список = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.список.bind(minimum_height=self.список.setter("height"))
        scroll.add_widget(self.список)
        root.add_widget(scroll)
        self.add_widget(root)
        self.bind(on_enter=lambda *a: self.обновить())
        self.обновить()

    def обновить(self):
        from strategies import имена_стратегий
        from analytics import статистика_по_стратегиям
        self.список.clear_widgets()
        тема = получить_тему()
        настройки = db.all_strategy_settings()
        стата = статистика_по_стратегиям(db)
        for имя_функции, читаемое in имена_стратегий():
            включена = настройки.get(имя_функции, True)
            карт = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=dp(64), spacing=dp(8), padding=dp(8))
            with карт.canvas.before:
                Color(*тема["card"])
                bg = RoundedRectangle(pos=карт.pos, size=карт.size, radius=[dp(10)])
            карт.bind(pos=lambda *a, b=bg, c=карт: (setattr(b, "pos", c.pos), setattr(b, "size", c.size)),
                      size=lambda *a, b=bg, c=карт: (setattr(b, "pos", c.pos), setattr(b, "size", c.size)))
            чекбокс = Button(text="✓" if включена else "○",
                             size_hint=(None, 1), width=dp(50),
                             background_normal="", background_color=тема["input_bg"],
                             color=цвет_статуса("успех") if включена else тема["muted"],
                             font_size=sp(20), font_name=FONT_BOLD)
            чекбокс.bind(on_press=lambda x, н=имя_функции, в=включена: self._переключить(н, not в))
            карт.add_widget(чекбокс)
            инфа = ""
            данные = стата.get(имя_функции) or стата.get(читаемое)
            if данные and данные["всего"] >= 3:
                цвет_с = "#22c55e" if данные["винрейт"] > 55 else (
                    "#facc15" if данные["винрейт"] > 45 else "#ef4444")
                инфа = f"\n[color={цвет_с}]{данные['винрейт']}% ({данные['побед']}/{данные['всего']})[/color]"
            lbl = Label(text=f"[b]{читаемое}[/b]{инфа}",
                        font_name=FONT_REGULAR, font_size=sp(13),
                        color=тема["text"], halign="left", valign="middle", markup=True)
            lbl.bind(size=lambda *a, l=lbl: setattr(l, "text_size", l.size))
            карт.add_widget(lbl)
            self.список.add_widget(карт)
        b_сброс = Кнопка("🔄 Включить все", "вторичная")
        b_сброс.bind(on_press=self._включить_все)
        self.список.add_widget(b_сброс)

    def _переключить(self, имя, значение):
        db.set_strategy_enabled(имя, значение)
        self.обновить()
        Тосты.показать(f"{'✅ Включена' if значение else '⏸ Отключена'}",
                       "успех" if значение else "предупреждение")

    def _включить_все(self, *a):
        from strategies import имена_стратегий
        for имя, _ in имена_стратегий():
            db.set_strategy_enabled(имя, True)
        self.обновить()
        Тосты.показать("Все стратегии включены", "успех")