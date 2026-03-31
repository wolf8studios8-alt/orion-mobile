[app]

# (str) Title of your application
title = ORION Mobile

# (str) Package name
package.name = orion.mobile

# (str) Package domain (needed for android/ios-ndk if using package name)
package.domain = com.orion.mobile

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,txt,md

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*, images/*.png

# (list) Source files to exclude
#source.exclude_exts = spec

# (str) Application versioning (method 1 or 2)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.0,pyjnius==1.5.1,plyer,requests

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
# Valid options are: portrait, landscape, reverse-landscape, reverse-portrait
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# Android specific
# (list) Permissions
android.permissions = INTERNET, RECORD_AUDIO, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, CAMERA, SYSTEM_ALERT_WINDOW

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to speed up builds when using CI
android.accept_sdk_license = True

# (str) Python for android support
android.python3 = True

# (str) Android entry point for custom Python code
#android.entrypoint = org.renpy.android.PythonActivity

# (list) Android application meta-data to set (key=value format)
#android.meta_data = 

# (list) Android library project to add (will be added in the project)
#android.add_src = 

# (list) Android Java .jar to add (will be added in the project)
#android.add_jars = 

# (list) Android Java .classpath to add (will be added in the project)
#android.add_classpath = 

# (str) Python for android support
#android.add_activity = 

# (str) Android activity name to add (will be added in the project)
#android.add_activity = 

# (str) Android service name to add (will be added in the project)
#android.add_service = 

# (str) Android service name to add (will be added in the project)
#android.add_uses_permission = 

# (str) Path to manifest.xml template
#android.manifest_src = 

# (list) List of Java .jar files to add to the libs folder
#android.add_libs_armeabi = 
#android.add_libs_armeabi_v7a = 
#android.add_libs_arm64_v8a = 
#android.add_libs_x86 = 
#android.add_libs_x86_64 = 

# (bool) Indicate whether the screen should stay on
#android.wakelock = False

# (bool) Enable AndroidX support
#android.enable_androidx = True

# (bool) Copy libraries instead of creating a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = armeabi-v7a
