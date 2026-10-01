Class Time for Pixel Watch 3

Files
  ClassTime-watch-v93.apk                 Watch app. Targets SDK 25 so notifications work, and adds two
                                          complication data sources: "Current class" and "Next class".
  heine.watch.classtime.apk               "Class Time" watch face (Watch Face Format v2, no code).
  heine.watch.cluster.apk                 "Class Time Cluster": bubble layout. Separate face; installs
                                          alongside the first one.
  ClassTime-phone-resigned.apk            Phone app, unchanged except re-signed with the same key.
  ClassTime-watch-original-unmodified.apk Original watch app (syncs with the ORIGINAL phone app only).
  classtime.jks                           Signing key (store/key password: classtime, alias: classtime).
  heine.watch.classtime-preview.png       What the face looks like (awake).
  heine.watch.classtime-preview-ambient.png  Always-on mode.
  heine.watch.classtime-options.png       A few of the customization combinations.
  heine.watch.cluster-preview.png, heine.watch.cluster-options.png   The Cluster face.
  source/                                 Source for the data feed and the watch face.

Naming
  Homemade watch faces use the package name heine.watch.{name}. The Class Time watch app keeps
  eu.nohus.classtime: phone-watch sync only works when it matches the phone app.
  The faces were renamed from eu.nohus.classtime.watchface(.cluster); a renamed package is a new
  app, so remove the old copies once:
    adb uninstall eu.nohus.classtime.watchface
    adb uninstall eu.nohus.classtime.watchface.cluster

Install / update (watch connected over adb)
  adb install -r ClassTime-watch-v93.apk      # updates in place; keeps the synced timetable
  adb install heine.watch.classtime.apk
  adb install heine.watch.cluster.apk         # optional second face
  adb shell pm grant eu.nohus.classtime android.permission.POST_NOTIFICATIONS

Then long-press the watch face > Add new > "Class Time".
If the class text is missing: long-press > Edit > tap the middle or bottom area and choose
Class Time > "Current class" (middle) or "Next class" (bottom).

Phone (first time only): export your timetable, uninstall the original Class Time,
install ClassTime-phone-resigned.apk, import the timetable. Edits on the phone sync to the watch.

The face
  - Big countdown: M:SS while awake (ticks every second), whole minutes ("13m") in always-on.
  - Label: "left in Per 3" during a class, "until Per 4" between classes, "until Homeroom"
    in the hour before the first class, "Off the clock!" (with "--") otherwise.
  - Ring: progress through the current class, passing period or pre-school hour (awake only).
  - Time and full date at the top; next class with start time and room below the label.
  - Three extra complication slots: left and right of the countdown, and a chip at the bottom.

Customizing
  On the phone: Pixel Watch app > Watch faces > Class Time > Customize.
  On the watch: long-press the face > Edit.
    Colour           Amber, Teal, Coral, Indigo, Lime, Sky, Pink, White
    Layout           Countdown first, Clock first, Countdown only
    Countdown        Minutes and seconds, Minutes only
    Progress ring    Bold, Thin, Off
    Background       Black, Tinted
    Date             on or off

Complication slots (long-press > Edit > tap the area)
  Middle   Class Time "Current class" by default. Any other ranged or text complication also
           works there (steps, battery, weather...): its text goes where the countdown is and
           its progress drives the ring.
  Next     Class Time "Next class" by default. Accepts text, ranged, icon and image
           complications. To hide it, choose "Empty".
  Left     Round slot, watch battery by default.
  Right    Round slot, step count by default.
  Bottom   Chip, unread notifications by default.
           Left/Right take ranged (drawn as a ring), text, icon and image complications;
           Bottom takes text, ranged (fills the chip) and icon complications.
           Choose "Empty" to hide any of them. All three hide in always-on mode.
  Class Time's two feeds also work in other watch faces (with icons), including Pixel faces.
  The Class Time app's own "Watch face" settings screen only affected the old face and does
  nothing here; Wear OS gives other apps no way to change a watch face's settings.

  To change the design, edit source/heine.watch.classtime/gen_face.py and regenerate res/raw/watchface.xml.

Class Time Cluster (second face)
  Time in a pill on the left, everything else in bubbles:
    Big bubble (right)   Current class: countdown, label, class-progress ring round the edge.
    Bottom bubble        Next class: start time and class name (Class Time "Next class").
    Top bubble           Step count by default.
    Top-left bubble      Battery (with ring) by default.
    Bottom-left bubble   Day and date by default.
  Every bubble takes text, ranged (ring), icon and image complications; choose "Empty" to leave
  just an outline. Settings: Colour (Lime, Amber, Teal, Sky, Indigo, Pink, Coral, White; each
  tints the bubbles) and Countdown (minutes and seconds, or minutes only).
  Always-on shows the time, the countdown in minutes, and the next class.
  Source: source/heine.watch.cluster/gen_cluster.py (reuses source/heine.watch.classtime/gen_face.py).
