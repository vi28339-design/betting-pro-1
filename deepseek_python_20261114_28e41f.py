import os
import shutil
import threading
from kivy.utils import platform
from kivy.clock import Clock


def распознать_async(путь_к_картинке, колбэк):
    def работа():
        текст = _tesseract_sync(путь_к_картинке)
        Clock.schedule_once(lambda dt: колбэк(текст), 0)
    threading.Thread(target=работа, daemon=True).start()


def _tesseract_sync(путь):
    if platform != "android":
        return _fallback(путь)
    try:
        from jnius import autoclass
        TessBaseAPI = autoclass("cz.adaptech.tesseract4android.TessBaseAPI")
        BitmapFactory = autoclass("android.graphics.BitmapFactory")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        data_path = os.path.join(context.getFilesDir().getAbsolutePath(), "tesseract")
        tessdata_path = os.path.join(data_path, "tessdata")
        os.makedirs(tessdata_path, exist_ok=True)
        rus_file = os.path.join(tessdata_path, "rus.traineddata")
        if not os.path.exists(rus_file):
            src = os.path.join("static", "tessdata", "rus.traineddata")
            if os.path.exists(src):
                shutil.copy(src, rus_file)
            else:
                return None
        api = TessBaseAPI()
        if not api.init(data_path, "rus"):
            api.recycle()
            return None
        bitmap = BitmapFactory.decodeFile(путь)
        if bitmap is None:
            api.recycle()
            return None
        api.setImage(bitmap)
        текст = api.getUTF8Text()
        api.recycle()
        return текст
    except Exception as e:
        print(f"[Tesseract Android] {e}")
        return _fallback(путь)


def _fallback(путь):
    try:
        from PIL import Image
        import pytesseract
        return pytesseract.image_to_string(Image.open(путь), lang="rus+eng")
    except Exception:
        return None