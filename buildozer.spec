[app]
title = Betting PRO
package.name = bettingpro
package.domain = com.bettingpro.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc,json,csv
source.include_patterns = static/fonts/*.ttf,static/*.png
version = 18.0
requirements = python3,kivy,pyjnius,plyer,pillow,certifi

# ✅ Убрали p4a.branch = develop. Используем стабильный master по умолчанию.
# ✅ Убрали фиксацию pyjnius, чтобы p4a сам выбрал рабочую версию.

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/static/icon.png
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,RECORD_AUDIO,SCHEDULE_EXACT_ALARM,POST_NOTIFICATIONS
android.api = 33
android.minapi = 21

# ✅ Официально рекомендуемый NDK для текущего p4a [citation:9]
android.ndk = 25b

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
