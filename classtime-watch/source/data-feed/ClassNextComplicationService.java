package eu.nohus.classtime;

import android.graphics.drawable.Icon;
import android.support.wearable.complications.ComplicationData;
import android.support.wearable.complications.ComplicationManager;
import android.support.wearable.complications.ComplicationProviderService;
import android.support.wearable.complications.ComplicationText;

/**
 * "Next class": name, room and start time of the next lesson, today or on the next school day.
 * LONG_TEXT: "Next · 10:28" / "Per 4 · B12". SHORT_TEXT: "10:28" titled "Per 4".
 * RANGED_VALUE: the same short text, with progress through the wait until that class starts
 * (for faces whose slots only offer ranged values).
 */
public class ClassNextComplicationService extends ComplicationProviderService {

    @Override
    public void onComplicationActivated(int id, int type, ComplicationManager manager) {
        ComplicationTickReceiver.schedule(this);
    }

    @Override
    public void onComplicationUpdate(int id, int type, ComplicationManager manager) {
        long now = System.currentTimeMillis();
        ClassSchedule s = ClassSchedule.compute(this, now);

        String clock = s.hasNext ? s.formatClock(this, s.nextStart) : "";
        String when;
        String what;
        if (s.hasNext) {
            when = s.nextIsToday ? "Next · " + clock : s.nextDayLabel + " · " + clock;
            what = s.nextName.length() > 0 ? s.nextName : "Class";
            if (s.nextRoom.length() > 0) what = what + " · " + s.nextRoom;
        } else if (s.state == ClassSchedule.NO_DATA) {
            when = "Next";
            what = "No timetable yet";
        } else {
            when = "Next";
            what = "Nothing this week";
        }
        // Short forms: time as the text, class name as the title.
        String shortText = s.hasNext ? (s.nextIsToday ? clock : shortDay(s.nextDayLabel) + " " + clock) : "--";
        String shortTitle = s.hasNext && s.nextName.length() > 0 ? s.nextName : "Next";

        ComplicationData.Builder b;
        if (type == ComplicationData.TYPE_SHORT_TEXT) {
            b = new ComplicationData.Builder(ComplicationData.TYPE_SHORT_TEXT)
                    .setShortTitle(ComplicationText.plainText(shortTitle))
                    .setShortText(ComplicationText.plainText(shortText));
        } else if (type == ComplicationData.TYPE_RANGED_VALUE) {
            float max = 1f;
            float value = 0f;
            if (s.hasNext && s.nextIsToday && s.resolveBlock(now) && s.nextStart > s.blockStart) {
                max = (s.nextStart - s.blockStart) / 60000f;
                value = Math.max(0f, Math.min(max, (now - s.blockStart) / 60000f));
            }
            b = new ComplicationData.Builder(ComplicationData.TYPE_RANGED_VALUE)
                    .setMinValue(0f)
                    .setMaxValue(max)
                    .setValue(value)
                    .setShortTitle(ComplicationText.plainText(shortTitle))
                    .setShortText(ComplicationText.plainText(shortText));
        } else {
            b = new ComplicationData.Builder(ComplicationData.TYPE_LONG_TEXT)
                    .setLongTitle(ComplicationText.plainText(when))
                    .setLongText(ComplicationText.plainText(what));
        }
        Icon icon = ComplicationTickReceiver.icon(this, "ic_complication_next");
        if (icon != null) b.setIcon(icon);
        b.setContentDescription(ComplicationText.plainText(when + ": " + what));
        b.setTapAction(ComplicationTickReceiver.openApp(this));
        manager.updateComplicationData(id, b.build());
        ComplicationTickReceiver.schedule(this);
    }

    /** "Tomorrow" is too long for a short slot. */
    private static String shortDay(String label) {
        return "Tomorrow".equals(label) ? "Tmrw" : label;
    }
}
