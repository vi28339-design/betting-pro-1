import threading
from datetime import datetime, timedelta
from kivy.utils import platform

_таймеры = {}


def запланировать(имя_матча, время_матча, текст_прогноза, за_минут_до=(30, 5)):
    ids = []
    for минут in за_минут_до:
        момент = время_матча - timedelta(minutes=минут)
        if момент <= datetime.now():
            continue

        def сработать(имя=имя_матча, текст=текст_прогноза, м=минут):
            try:
                from notifications import send_notification
                send_notification(f"🏒 Матч через {м} мин",
                                  f"{имя}\nПрогноз: {текст}")
            except Exception:
                pass

        t = threading.Timer((момент - datetime.now()).total_seconds(), сработать)
        t.daemon = True
        t.start()
        ids.append(id(t))
        _таймеры[id(t)] = t
    return ids


def отменить(ids):
    for i in ids:
        if i in _таймеры:
            _таймеры[i].cancel()
            del _таймеры[i]