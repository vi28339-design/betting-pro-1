import os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


def улучшить_скриншот(путь_входа, путь_выхода=None):
    if путь_выхода is None:
        основа, расширение = os.path.splitext(путь_входа)
        путь_выхода = f"{основа}_upd{расширение}"
    try:
        img = Image.open(путь_входа).convert("L")
        пиксели = list(img.getdata())
        if пиксели and sum(пиксели) / len(пиксели) < 128:
            img = ImageOps.invert(img)
        w, h = img.size
        img = img.resize((w * 3, h * 3), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = img.point(lambda x: 0 if x < 150 else 255, "1")
        img.save(путь_выхода)
        return путь_выхода
    except Exception as e:
        print(f"[Image utils] {e}")
        return путь_входа