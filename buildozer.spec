[app]
title = Betting PRO
package.name = bettingpro
package.domain = com.bettingpro.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc,json,csv
source.include_patterns = static/fonts/*.ttf,static/*.png
version = 18.0

# ✅ Защита от ошибки Py_REFCNT
requirements = python3,kivy,jnius>=1.4.0,plyer,pillow,certifi

# ✅ КЛЮЧЕВОЕ: Ветка develop обходит баги master с libffi
p4a.branch = develop

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/static/icon.png
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,RECORD_AUDIO,SCHEDULE_EXACT_ALARM,POST_NOTIFICATIONS
android.api = 33
android.minapi = 21
android.ndk = 25b

# ✅ Понижаем API для совместимости старых C-библиотек
android.ndk_api = 21

android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
