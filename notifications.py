from kivy.utils import platform


def send_notification(title, message):
    try:
        from plyer import notification
        notification.notify(title=title, message=message,
                            app_name="Betting PRO", timeout=5)
    except Exception as e:
        print(f"Ошибка уведомления: {e}")


def share_text(text):
    # Без pyjnius. Возвращаем False, чтобы main.py открыл диалог с текстом
    return False
