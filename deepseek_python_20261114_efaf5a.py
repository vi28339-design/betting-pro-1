from kivy.utils import platform
from kivy.clock import Clock


def выбрать_картинку(колбэк):
    if platform != "android":
        колбэк(_выбрать_на_пк())
        return
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android import activity
        Intent = autoclass("android.content.Intent")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        class Слушатель(PythonJavaClass):
            __javainterfaces__ = ["org/kivy/android/PythonActivity$ActivityResultListener"]
            __javacontext__ = "app"

            def __init__(self, callback):
                super().__init__()
                self.callback = callback
                self._вызван = False

            @java_method("(IILandroid/content/Intent;)V")
            def onActivityResult(self, requestCode, resultCode, data):
                if requestCode != 202 or self._вызван:
                    return
                self._вызван = True
                try:
                    activity.unbind(on_activity_result=self.onActivityResult)
                except Exception:
                    pass
                if resultCode != -1 or data is None:
                    Clock.schedule_once(lambda dt: self.callback(None), 0)
                    return
                try:
                    uri = data.getData()
                    путь = _uri_в_путь(uri)
                    Clock.schedule_once(lambda dt: self.callback(путь), 0)
                except Exception:
                    Clock.schedule_once(lambda dt: self.callback(None), 0)

        слушатель = Слушатель(колбэк)
        activity.bind(on_activity_result=слушатель.onActivityResult)
        intent = Intent()
        intent.setAction(Intent.ACTION_GET_CONTENT)
        intent.setType("image/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        PythonActivity.mActivity.startActivityForResult(intent, 202)
    except Exception as e:
        print(f"[Picker] {e}")
        колбэк(None)


def _uri_в_путь(uri):
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        File = autoclass("java.io.File")
        FileOutputStream = autoclass("java.io.FileOutputStream")
        BufferedInputStream = autoclass("java.io.BufferedInputStream")
        context = PythonActivity.mActivity
        входной = context.getContentResolver().openInputStream(uri)
        if входной is None:
            return None
        кэш = context.getCacheDir()
        временный = File(кэш, "bk_screenshot.png")
        поток = BufferedInputStream(входной)
        выход = FileOutputStream(временный)
        буфер = bytearray(8192)
        while True:
            n = поток.read(буфер)
            if n <= 0:
                break
            выход.write(буфер, 0, n)
        выход.close()
        поток.close()
        return временный.getAbsolutePath()
    except Exception as e:
        print(f"[URI→path] {e}")
        return None


def _выбрать_на_пк():
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        путь = filedialog.askopenfilename(
            title="Выбери скриншот",
            filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")])
        root.destroy()
        return путь if путь else None
    except Exception:
        return None