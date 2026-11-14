import random
from statistics import mean, median


def собрать_статистику(db):
    результат = {"по_спортам": {}, "общая": {}, "последние_10": []}
    rows = db.conn.execute(
        """SELECT sport,team1,team2,line,rec,exact_score,actual_score,created
           FROM history WHERE actual_score IS NOT NULL ORDER BY id"""
    ).fetchall()
    по_спортам = {}
    for row in rows:
        по_спортам.setdefault(row[0], []).append(row)
    for спорт, матчи in по_спортам.items():
        результат["по_спортам"][спорт] = _посчитать_метрики(матчи, спорт)
    all_rows = [r for m in по_спортам.values() for r in m]
    результат["общая"] = _посчитать_метрики(all_rows, "all")
    результат["последние_10"] = rows[-10:]
    return результат


def _посчитать_метрики(матчи, спорт):
    всего = побед = 0
    профит = 0.0
    ставка = 100.0
    for row in матчи:
        спорт_м, t1, t2, line, rec, exact, actual, dt = row
        if not actual or ":" not in actual:
            continue
        try:
            g1, g2 = map(int, actual.split(":"))
        except ValueError:
            continue
        всего += 1
        if "ТБ" in rec: угадал = (g1 + g2) > line
        elif "ТМ" in rec: угадал = (g1 + g2) < line
        elif "П1" in rec: угадал = g1 > g2
        elif "П2" in rec: угадал = g2 > g1
        elif "X" in rec: угадал = g1 == g2
        else: continue
        if угадал:
            побед += 1
            профит += ставка * 0.85
        else:
            профит -= ставка
    винрейт = (побед / всего * 100) if всего else 0
    roi = (профит / (всего * ставка) * 100) if всего else 0
    return {"всего": всего, "побед": побед, "винрейт": round(винрейт, 1),
            "профит": round(профит, 1), "roi": round(roi, 1)}


def монте_карло(винрейт_pct, кэф, банк, доля_келли=0.25,
                ставок=100, симуляций=1000, макс_pct=0.05):
    winrate = винрейт_pct / 100
    if winrate <= 0 or кэф <= 1:
        return {"error": "Некорректные параметры"}
    b = кэф - 1
    f = max(0, min((winrate * b - (1 - winrate)) / b * доля_келли, макс_pct))
    финалы = []
    for _ in range(симуляций):
        текущий = банк
        for _ in range(ставок):
            if текущий <= 0:
                break
            ставка = текущий * f
            if random.random() < winrate:
                текущий += ставка * b
            else:
                текущий -= ставка
        финалы.append((текущий - банк) / банк * 100)
    финалы.sort()
    n = len(финалы)
    return {"медиана_pct": round(median(финалы), 1),
            "среднее_pct": round(mean(финалы), 1),
            "худшие_5_pct": round(финалы[int(n * 0.05)], 1),
            "лучшие_5_pct": round(финалы[int(n * 0.95)], 1),
            "шанс_плюс": round(sum(1 for p in финалы if p > 0) / n * 100, 1),
            "шанс_минус_50": round(sum(1 for p in финалы if p < -50) / n * 100, 1),
            "шанс_плюс_50": round(sum(1 for p in финалы if p > 50) / n * 100, 1),
            "келли_pct": round(f * 100, 2),
            "ставок": ставок, "симуляций": симуляций}


def статистика_по_стратегиям(db):
    from strategies import имена_стратегий
    rows = db.history_with_strategies()
    статистика = {}
    for rec, line, actual, strategies, divergence in rows:
        if not actual or ":" not in actual or not strategies:
            continue
        try:
            g1, g2 = map(int, actual.split(":"))
        except ValueError:
            continue
        угадал = False
        if "ТБ" in rec: угадал = (g1 + g2) > line
        elif "ТМ" in rec: угадал = (g1 + g2) < line
        elif "П1" in rec: угадал = g1 > g2
        elif "П2" in rec: угадал = g2 > g1
        elif "X" in rec: угадал = g1 == g2
        else: continue

        for s in strategies.split(","):
            s = s.strip()
            if not s:
                continue
            # Нормализация: читаемое имя → имя функции
            if not s.startswith("с_"):
                for имя_ф, читаемое in имена_стратегий():
                    if читаемое == s:
                        s = имя_ф
                        break
            if s not in статистика:
                статистика[s] = {"всего": 0, "побед": 0}
            статистика[s]["всего"] += 1
            if угадал:
                статистика[s]["побед"] += 1

    for s, data in статистика.items():
        data["винрейт"] = round(data["побед"] / data["всего"] * 100, 1) if data["всего"] else 0
    return статистика


def статистика_по_расхождению(db):
    rows = db.history_with_strategies()
    диапазоны = {
        ">8%": {"всего": 0, "побед": 0},
        "5-8%": {"всего": 0, "побед": 0},
        "2-5%": {"всего": 0, "побед": 0},
        "<2%": {"всего": 0, "побед": 0},
    }
    for rec, line, actual, strategies, divergence in rows:
        if not actual or ":" not in actual:
            continue
        try:
            g1, g2 = map(int, actual.split(":"))
        except ValueError:
            continue
        угадал = False
        if "ТБ" in rec: угадал = (g1 + g2) > line
        elif "ТМ" in rec: угадал = (g1 + g2) < line
        elif "П1" in rec: угадал = g1 > g2
        elif "П2" in rec: угадал = g2 > g1
        elif "X" in rec: угадал = g1 == g2
        else: continue
        div = divergence or 0
        if div > 0.08: кат = ">8%"
        elif div > 0.05: кат = "5-8%"
        elif div > 0.02: кат = "2-5%"
        else: кат = "<2%"
        диапазоны[кат]["всего"] += 1
        if угадал:
            диапазоны[кат]["побед"] += 1
    for кат, d in диапазоны.items():
        d["винрейт"] = round(d["побед"] / d["всего"] * 100, 1) if d["всего"] else 0
    return диапазоны