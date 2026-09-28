package eu.nohus.classtime;

import android.graphics.drawable.Icon;
import android.support.wearable.complications.ComplicationData;
import android.support.wearable.complications.ComplicationManager;
import android.support.wearable.complications.ComplicationProviderService;
import android.support.wearable.complications.ComplicationText;
import java.util.concurrent.TimeUnit;

/**
 * "Current class": what the countdown is running against ("left in Per 3", "until Per 4",
 * "Off the clock!") and how long is left.
 *
 * RANGED_VALUE carries the block as seconds since local midnight plus MARKER: min = block
 * start, max = block end, value = now. The Class Time watch face subtracts MARKER and compares
 * with its own [SECONDS_IN_DAY] clock, so its M:SS countdown and ring tick every second; the
 * marker also lets it tell this data apart from other ranged complications. Off the clock is
 * min = MARKER - 1, max = MARKER. Other faces just see an ordinary min/value/max progress.
 */
public class ClassNowComplicationService extends ComplicationProviderService {
    static final String OFF_LABEL = "Off the clock!";
    /** Added to seconds-of-day; 1,086,400 max still fits a float exactly. */
    static final float MARKER = 1000000f;

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
        boolean timed = s.resolveBlock(now);
        String label = timed ? s.blockLabel
                : s.state == ClassSchedule.NO_DATA ? "Open Class Time on your phone" : OFF_LABEL;
        ComplicationText countdown = timed
                ? countdown(s.blockEnd, "^1")
                : ComplicationText.plainText("--");

        ComplicationData.Builder b;
        if (type == ComplicationData.TYPE_LONG_TEXT) {
            b = new ComplicationData.Builder(ComplicationData.TYPE_LONG_TEXT)
                    .setLongTitle(ComplicationText.plainText(label))
                    .setLongText(countdown);
        } else if (type == ComplicationData.TYPE_SHORT_TEXT) {
            b = new ComplicationData.Builder(ComplicationData.TYPE_SHORT_TEXT)
                    .setShortTitle(ComplicationText.plainText(label))
                    .setShortText(countdown);
        } else {
            float min = MARKER - 1f;
            float max = MARKER;
            float value = MARKER - 1f;
            if (timed) {
                min = MARKER + ClassSchedule.secondsOfDay(s.blockStart);
                max = MARKER + ClassSchedule.secondsOfDay(s.blockEnd);
                if (max <= min) max = min + 1f;   // guard against zero-length or midnight-spanning blocks
                value = Math.max(min, Math.min(max, MARKER + ClassSchedule.secondsOfDay(now)));
            }
            b = new ComplicationData.Builder(ComplicationData.TYPE_RANGED_VALUE)
                    .setMinValue(min)
                    .setMaxValue(max)
                    .setValue(value)
                    .setShortTitle(ComplicationText.plainText(label))
                    .setShortText(countdown);
        }
        Icon icon = ComplicationTickReceiver.icon(this, "ic_complication_now");
        if (icon != null) b.setIcon(icon);
        b.setContentDescription(ComplicationText.plainText(label));
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
