import os
try:
    import gspread
    SHEETS_OK = True
except ImportError:
    SHEETS_OK = False

from database import db

CREDS_PATH = "credentials.json"
SHEET_NAME = "Betting PRO"


def выгрузить():
    if not SHEETS_OK:
        return False, "gspread не установлен"
    if not os.path.exists(CREDS_PATH):
        return False, "credentials.json не найден"
    return False, "Функция в разработке"


def загрузить():
    return False, "Функция в разработке"