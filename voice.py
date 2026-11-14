from kivy.utils import platform


def слушать_голос(колбэк):
    if platform != "android":
        колбэк(None)
        return
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        from android import activity
        Intent = autoclass("android.content.Intent")
        RecognizerIntent = autoclass("android.speech.RecognizerIntent")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        String = autoclass("java.lang.String")

        class Слушатель(PythonJavaClass):
            __javainterfaces__ = ["org/kivy/android/PythonActivity$ActivityResultListener"]
            __javacontext__ = "app"

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method("(IILandroid/content/Intent;)V")
            def onActivityResult(self, requestCode, resultCode, data):
                if requestCode != 101:
                    return
                if resultCode == -1:
                    try:
                        results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                        if results and results.size() > 0:
                            self.callback(str(results.get(0)))
                        else:
                            self.callback(None)
                    except Exception:
                        self.callback(None)
                else:
                    self.callback(None)

        слушатель = Слушатель(колбэк)
        activity.bind(on_activity_result=слушатель.onActivityResult)
        intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ru-RU")
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT,
                        cast("java.lang.CharSequence", String("Продиктуйте данные")))
        PythonActivity.mActivity.startActivityForResult(intent, 101)
    except Exception as e:
        print(f"Ошибка голоса: {e}")
        колбэк(None)