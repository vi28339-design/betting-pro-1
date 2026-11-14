from math import comb
from model import poisson_pmf, poisson_over, predict_hockey


def dixon_coles_tau(x, y, lam, mu, rho=-0.1):
    if x == 0 and y == 0: return 1 - lam * mu * rho
    elif x == 0 and y == 1: return 1 + lam * rho
    elif x == 1 and y == 0: return 1 + mu * rho
    elif x == 1 and y == 1: return 1 - rho
    return 1.0


def predict_football(exp1, exp2, home_boost=1.0, max_goals=8):
    exp1 *= home_boost
    p1 = px = p2 = 0.0
    total_exp = exp1 + exp2
    best_score, best_prob = (0, 0), 0.0
    for g1 in range(max_goals + 1):
        for g2 in range(max_goals + 1):
            p = dixon_coles_tau(g1, g2, exp1, exp2) * poisson_pmf(g1, exp1) * poisson_pmf(g2, exp2)
            if p > best_prob:
                best_prob, best_score = p, (g1, g2)
            if g1 > g2: p1 += p
            elif g1 == g2: px += p
            else: p2 += p
    return {"p1": p1, "px": px, "p2": p2, "total_exp": total_exp,
            "exact_score": best_score, "exact_prob": best_prob,
            "exp1": exp1, "exp2": exp2}


def predict_tennis(elo1, elo2, best_of=3):
    diff = (elo1 - elo2) / 400
    p_set = 1 / (1 + 10 ** (-diff))
    sets_to_win = (best_of // 2) + 1
    p_match = sum(comb(best_of, s) * (p_set ** s) * ((1 - p_set) ** (best_of - s))
                  for s in range(sets_to_win, best_of + 1))
    return {"p1": p_match, "p2": 1 - p_match, "p_set": p_set,
            "elo_diff": elo1 - elo2, "total_exp": 0,
            "exact_score": (0, 0), "exact_prob": 0}


def predict_table_tennis(elo1, elo2, best_of=5):
    return predict_tennis(elo1, elo2, best_of)


СПОРТЫ = {
    "шорт-хоккей": {"тотал": True, "исход": True, "линия_по_умолчанию": 9.5},
    "футбол": {"тотал": True, "исход": True, "линия_по_умолчанию": 2.5},
    "теннис": {"тотал": False, "исход": True, "best_of": 3},
    "настольный теннис": {"тотал": False, "исход": True, "best_of": 5},
}


def универсальный_прогноз(спорт, значения):
    if спорт == "шорт-хоккей":
        exp1 = (значения["к1з"] + значения["к2п"]) / 2
        exp2 = (значения["к2з"] + значения["к1п"]) / 2
        return predict_hockey(exp1, exp2, значения.get("дом", 1.0),
                              значения.get("форма1", ""), значения.get("форма2", ""),
                              значения.get("elo_boost", 1.0))
    elif спорт == "футбол":
        exp1 = (значения["к1з"] + значения["к2п"]) / 2
        exp2 = (значения["к2з"] + значения["к1п"]) / 2
        return predict_football(exp1, exp2, значения.get("дом", 1.0))
    elif спорт == "теннис":
        return predict_tennis(значения["elo1"], значения["elo2"], 3)
    elif спорт == "настольный теннис":
        return predict_table_tennis(значения["elo1"], значения["elo2"], 5)
    return None