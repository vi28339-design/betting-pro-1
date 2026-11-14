import os

try:
    from PIL import Image
    import pytesseract
    OCR_OK = True
except ImportError:
    OCR_OK = False


def распознать_скриншот(путь):
    if not OCR_OK or not os.path.exists(путь):
        return None
    try:
        img = Image.open(путь)
        return pytesseract.image_to_string(img, lang="rus+eng")
    except Exception as e:
        print(f"[OCR] {e}")
        return None