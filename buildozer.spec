[app]
title = Betting PRO
package.name = bettingpro
package.domain = com.bettingpro.app
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0
requirements = python3,kivy
p4a.branch = master
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 28
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
# ✅ ОБЯЗАТЕЛЬНО: отключает ошибку "Buildozer is running as root!"
warn_on_root = 0
