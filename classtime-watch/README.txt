Class Time for Pixel Watch 3

Files
  ClassTime-watch-v91.apk                 Watch app. Targets SDK 25 so notifications work, and adds two
                                          complication data sources: "Current class" and "Next class".
  ClassTime-WatchFace.apk                 Class Time watch face (Watch Face Format v2, no code).
  ClassTime-phone-resigned.apk            Phone app, unchanged except re-signed with the same key.
  ClassTime-watch-original-unmodified.apk Original watch app (syncs with the ORIGINAL phone app only).
  classtime.jks                           Signing key (store/key password: classtime, alias: classtime).
  watchface-preview.png                   What the face looks like.
  source/                                 Source for the data feed and the watch face.

Install / update (watch connected over adb)
  adb install -r ClassTime-watch-v91.apk      # updates in place; keeps the synced timetable
  adb install ClassTime-WatchFace.apk
  adb shell pm grant eu.nohus.classtime android.permission.POST_NOTIFICATIONS

Then long-press the watch face > Add new > "Class Time".
If the class text is missing: long-press > Edit > tap the middle or bottom area and choose
Class Time > "Current class" (middle) or "Next class" (bottom).

Phone (first time only): export your timetable, uninstall the original Class Time,
install ClassTime-phone-resigned.apk, import the timetable. Edits on the phone sync to the watch.

The face
  - Ring: progress through the current lesson or break (hidden in always-on mode).
  - Middle: lesson name and a live countdown ("32m left"), or "Break", "First class in 1h 5m",
    "Classes over", "No classes".
  - Bottom: next lesson with its start time and room, including the next school day.
  - Accent colour: long-press > Edit > Accent (Teal, Amber, Coral, Lilac).
