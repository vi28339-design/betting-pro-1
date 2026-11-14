from kivy.utils import platform


def send_notification(title, message):
    try:
        if platform == "android":
            from plyer import notification
            notification.notify(title=title, message=message,
                                app_name="Betting PRO", timeout=5)
        else:
            print(f"[Уведомление] {title}: {message}")
    except Exception as e:
        print(f"Ошибка уведомления: {e}")


def share_text(text):
    try:
        if platform == "android":
            from jnius import autoclass, cast
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            String = autoclass("java.lang.String")
            intent = Intent()
            intent.setAction(Intent.ACTION_SEND)
            intent.putExtra(Intent.EXTRA_TEXT, String(text))
            intent.setType("text/plain")
            chooser = Intent.createChooser(
                intent, cast("java.lang.CharSequence", String("Поделиться прогнозом")))
            PythonActivity.mActivity.startActivity(chooser)
            return True
        else:
            print(f"[Поделиться]\n{text}")
            return True
    except Exception as e:
        print(f"Ошибка share: {e}")
        return False