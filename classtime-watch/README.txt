Class Time for Pixel Watch 3

ClassTime-watch-PixelWatch3.apk        Patched watch app (targetSdk 29 -> 25 so notifications/background alerts work). Re-signed.
ClassTime-phone-resigned.apk           Phone app, unchanged except re-signed with the same key (needed for phone<->watch sync).
ClassTime-watch-original-unmodified.apk  Untouched watch app; syncs with the original phone app, but notifications likely won't show.
classtime.jks                          Signing key (store/key password: classtime, alias: classtime).

Install
1. Phone: export your timetable, uninstall original Class Time, install ClassTime-phone-resigned.apk, re-import.
2. Watch: Settings > System > About > tap build number 7x; Developer options > ADB + Wireless debugging.
   adb pair <ip>:<pair-port>
   adb connect <ip>:<port>
   adb install ClassTime-watch-PixelWatch3.apk
   adb shell pm grant eu.nohus.classtime android.permission.POST_NOTIFICATIONS
