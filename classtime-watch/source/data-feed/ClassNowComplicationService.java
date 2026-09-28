package eu.nohus.classtime;

import android.support.wearable.complications.ComplicationData;
import android.support.wearable.complications.ComplicationManager;
import android.support.wearable.complications.ComplicationProviderService;
import android.support.wearable.complications.ComplicationText;
import java.util.concurrent.TimeUnit;

/**
 * "Current class": lesson (or break) name, a live countdown and progress through it.
 * RANGED_VALUE drives the watch face's progress ring.
 */
public class ClassNowComplicationService extends ComplicationProviderService {

    @Override
    public void onComplicationActivated(int id, int type, ComplicationManager manager) {
        ComplicationTickReceiver.schedule(this);
    }

    @Override
    public void onComplicationUpdate(int id, int type, ComplicationManager manager) {
        long now = System.currentTimeMillis();
        ClassSchedule s = ClassSchedule.compute(this, now);
        manager.updateComplicationData(id, build(s, type, now));
        ComplicationTickReceiver.schedule(this);
    }

    private ComplicationData build(ClassSchedule s, int type, long now) {
        String title;
        ComplicationText text;
        switch (s.state) {
            case ClassSchedule.LESSON:
                title = s.lessonName.length() > 0 ? s.lessonName : "Class";
                text = countdown(s.periodEnd, "^1 left");
                break;
            case ClassSchedule.BREAK:
                title = "Break";
                text = countdown(s.periodEnd, "^1 left");
                break;
            case ClassSchedule.BEFORE:
                title = "First class";
                text = countdown(s.periodEnd, "in ^1");
                break;
            case ClassSchedule.AFTER:
                title = "Classes over";
                text = ComplicationText.plainText("Done for today");
                break;
            case ClassSchedule.FREE_DAY:
                title = "No classes";
                text = ComplicationText.plainText("Free day");
                break;
            default:
                title = "Class Time";
                text = ComplicationText.plainText("Open the phone app");
                break;
        }

        float max = 1f;
        float value = 0f;
        boolean timed = s.state == ClassSchedule.LESSON || s.state == ClassSchedule.BREAK;
        if (timed && s.periodEnd > s.periodStart) {
            max = (s.periodEnd - s.periodStart) / 60000f;
            value = Math.max(0f, Math.min(max, (now - s.periodStart) / 60000f));
        } else if (s.state == ClassSchedule.AFTER) {
            value = 1f;
        }

        ComplicationData.Builder b;
        if (type == ComplicationData.TYPE_LONG_TEXT) {
            String longTitle = title;
            if (s.state == ClassSchedule.LESSON && s.lessonRoom.length() > 0) {
                longTitle = title + " · " + s.lessonRoom;
            }
            b = new ComplicationData.Builder(ComplicationData.TYPE_LONG_TEXT)
                    .setLongTitle(ComplicationText.plainText(longTitle))
                    .setLongText(text);
        } else if (type == ComplicationData.TYPE_SHORT_TEXT) {
            b = new ComplicationData.Builder(ComplicationData.TYPE_SHORT_TEXT)
                    .setShortTitle(ComplicationText.plainText(title))
                    .setShortText(text);
        } else {
            b = new ComplicationData.Builder(ComplicationData.TYPE_RANGED_VALUE)
                    .setMinValue(0f)
                    .setMaxValue(max)
                    .setValue(value)
                    .setShortTitle(ComplicationText.plainText(title))
                    .setShortText(text);
        }
        b.setContentDescription(ComplicationText.plainText(title));
        b.setTapAction(ComplicationTickReceiver.openApp(this));
        return b.build();
    }

    static ComplicationText countdown(long end, String surrounding) {
        return new ComplicationText.TimeDifferenceBuilder()
                .setReferencePeriodStart(end)
                .setReferencePeriodEnd(end)
                .setStyle(ComplicationText.DIFFERENCE_STYLE_SHORT_DUAL_UNIT)
                .setMinimumUnit(TimeUnit.MINUTES)
                .setShowNowText(false)
                .setSurroundingText(surrounding)
                .build();
    }
}
