import os
from kivy.app import App
from kivy.network.urlrequest import UrlRequest


class Загрузчик:
    def __init__(self):
        self._app = App.get_running_app()

    def скачать(self, url, имя_файла, on_успех=None, on_прогресс=None, on_ошибка=None):
        if not self._app:
            if on_ошибка:
                on_ошибка("Приложение не запущено")
            return None
        if имя_файла.endswith((".ttf", ".ttc")):
            папка = os.path.join(self._app.user_data_dir, "fonts")
        else:
            папка = os.path.join(self._app.user_data_dir, "data")
        os.makedirs(папка, exist_ok=True)
        путь = os.path.join(папка, имя_файла)

        def _успех(req, result):
            if on_успех:
                on_успех(путь)

        def _неудача(req, result):
            if on_ошибка:
                on_ошибка(f"HTTP {req.resp_status}")

        def _прогресс(req, current, total):
            if on_прогресс and total > 0:
                on_прогресс(current / total * 100)

        def _ошибка(req, error):
            if on_ошибка:
                on_ошибка(str(error))

        ca_file = None
        try:
            import certifi
            ca_file = certifi.where()
        except ImportError:
            pass

        return UrlRequest(url, on_success=_успех, on_failure=_неудача,
                          on_error=_ошибка, on_progress=_прогресс,
                          file_path=путь, timeout=30, ca_file=ca_file)


загрузчик = None


def инициализировать():
    global загрузчик
    загрузчик = Загрузчик()