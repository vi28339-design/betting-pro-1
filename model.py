import math


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_over(expected, line):
    threshold = math.ceil(line)
    p_less = sum(poisson_pmf(k, expected) for k in range(threshold))
    return 1 - p_less


def form_weight(form_str):
    if not form_str:
        return 1.0
    weights = {"В": 1.15, "П": 0.85, "Н": 1.0}
    total, wsum = 0.0, 0.0
    chars = list(form_str.upper())[-5:]
    for i, ch in enumerate(chars):
        w = i + 1
        if ch in weights:
            total += weights[ch] * w
            wsum += w
    return total / wsum if wsum else 1.0


def elo_update(rating_a, rating_b, score_a, k=24):
    exp_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    return (rating_a + k * (score_a - exp_a), rating_b - k * (score_a - exp_a))


def elo_boost(rating_a, rating_b):
    diff = (rating_a - rating_b) / 400
    factor = 1 + 0.15 * (1 / (1 + 10 ** (-diff)) - 0.5)
    return max(0.7, min(1.3, factor))


def predict_hockey(exp1, exp2, home_boost=1.0, form1="", form2="", elo_boost_val=1.0, max_goals=15):
    exp1 *= home_boost * elo_boost_val * form_weight(form1)
    exp2 *= form_weight(form2)
    p1 = px = p2 = 0.0
    best_score, best_prob = (0, 0), 0.0
    for g1 in range(max_goals + 1):
        pg1 = poisson_pmf(g1, exp1)
        for g2 in range(max_goals + 1):
            p = pg1 * poisson_pmf(g2, exp2)
            if p > best_prob:
                best_prob, best_score = p, (g1, g2)
            if g1 > g2:
                p1 += p
            elif g1 == g2:
                px += p
            else:
                p2 += p
    p_ot_win1 = px * 0.5
    p_ot_win2 = px * 0.5
    return {"p1": p1, "px": px, "p2": p2, "p1_ot": p1 + p_ot_win1,
            "p2_ot": p2 + p_ot_win2, "exact_score": best_score,
            "exact_prob": best_prob, "total_exp": exp1 + exp2,
            "exp1": exp1, "exp2": exp2}


def kelly_stake(bank, prob, odds, fraction=0.25, max_pct=0.05):
    b = odds - 1
    if b <= 0:
        return 0
    f = (prob * b - (1 - prob)) / b
    if f <= 0:
        return 0
    return round(bank * min(f * fraction, max_pct), 2)


def edge(prob, odds):
    return prob * odds - 1


def validate_input(scored, conceded, line, sport="футбол"):
    if sport == "шорт-хоккей":
        if not (0 <= scored <= 20): return False, "Заброшенных 0–20"
        if not (0 <= conceded <= 20): return False, "Пропущенных 0–20"
        if not (3 <= line <= 30): return False, "Линия 3–30"
    else:
        if not (0 <= scored <= 10): return False, "Забитых 0–10"
        if not (0 <= conceded <= 10): return False, "Пропущенных 0–10"
        if not (0 <= line <= 15): return False, "Линия 0–15"
    return True, ""


def calibrate_probability(raw_prob, slope=0.85):
    if raw_prob <= 0: return 0.01
    if raw_prob >= 1: return 0.99
    logit = math.log(raw_prob / (1 - raw_prob))
    return 1 / (1 + math.exp(-logit * slope))


def remove_margin(odds_over, odds_under):
    if odds_over <= 1.01 or odds_under <= 1.01:
        return 0.5, 0.5
    imp_over = 1 / odds_over
    imp_under = 1 / odds_under
    total = imp_over + imp_under
    if total <= 0: return 0.5, 0.5
    return imp_over / total, imp_under / total


def odds_divergence(model_prob, bookmaker_odds_pair, outcome="over"):
    if outcome in ("over", "п1"):
        odds_own, odds_other = bookmaker_odds_pair
    else:
        odds_other, odds_own = bookmaker_odds_pair
    if odds_own <= 1.01 or odds_other <= 1.01:
        return 0.0, 0.5
    imp_own = 1 / odds_own
    imp_other = 1 / odds_other
    total = imp_own + imp_other
    if total <= 0: return 0.0, 0.5
    fair_prob = imp_own / total
    return model_prob - fair_prob, fair_prob


def интерпретация_расхождения(div):
    if div > 0.08: return f"🔥 Модель сильно выше рынка ({div*100:+.1f}%)", "успех"
    elif div > 0.05: return f"✅ Модель выше рынка ({div*100:+.1f}%)", "успех"
    elif div > 0.02: return f"⚖️ Небольшой перевес ({div*100:+.1f}%)", "предупреждение"
    elif div > -0.02: return f"➖ Модель и рынок согласны ({div*100:+.1f}%)", "нейтральный"
    elif div > -0.05: return f"⚠️ Модель ниже рынка ({div*100:+.1f}%)", "предупреждение"
    else: return f"🔴 Модель сильно ниже рынка ({div*100:+.1f}%)", "опасность"


def backtest(history_rows, line_default=9.5):
    total = wins = 0
    profit = 0.0
    stake = 100.0
    for t1, t2, actual in history_rows:
        if not actual or ":" not in actual:
            continue
        try:
            g1, g2 = map(int, actual.split(":"))
        except ValueError:
            continue
        total += 1
        if (g1 + g2) > line_default:
            profit += stake * 0.85
            wins += 1
        else:
            profit -= stake
    roi = (profit / (total * stake) * 100) if total else 0
    winrate = (wins / total * 100) if total else 0
    return {"всего_ставок": total, "побед": wins,
            "винрейт": round(winrate, 1), "профит": round(profit, 2),
            "ROI": round(roi, 1)}