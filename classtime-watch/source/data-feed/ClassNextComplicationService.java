package eu.nohus.classtime;

import android.support.wearable.complications.ComplicationData;
import android.support.wearable.complications.ComplicationManager;
import android.support.wearable.complications.ComplicationProviderService;
import android.support.wearable.complications.ComplicationText;

/** "Next class": name, room and start time of the next lesson, today or on the next school day. */
public class ClassNextComplicationService extends ComplicationProviderService {

    @Override
    public void onComplicationActivated(int id, int type, ComplicationManager manager) {
        ComplicationTickReceiver.schedule(this);
    }

    @Override
    public void onComplicationUpdate(int id, int type, ComplicationManager manager) {
        ClassSchedule s = ClassSchedule.compute(this, System.currentTimeMillis());

        String when;
        String what;
        if (s.hasNext) {
            String clock = s.formatClock(this, s.nextStart);
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

        ComplicationData.Builder b;
        if (type == ComplicationData.TYPE_SHORT_TEXT) {
            String shortWhen = s.hasNext ? s.formatClock(this, s.nextStart) : "—";
            String shortWhat = s.hasNext && s.nextName.length() > 0 ? s.nextName : "Next";
            b = new ComplicationData.Builder(ComplicationData.TYPE_SHORT_TEXT)
                    .setShortTitle(ComplicationText.plainText(shortWhat))
                    .setShortText(ComplicationText.plainText(shortWhen));
        } else {
            b = new ComplicationData.Builder(ComplicationData.TYPE_LONG_TEXT)
                    .setLongTitle(ComplicationText.plainText(when))
                    .setLongText(ComplicationText.plainText(what));
        }
        b.setContentDescription(ComplicationText.plainText(when + ": " + what));
        b.setTapAction(ComplicationTickReceiver.openApp(this));
        manager.updateComplicationData(id, b.build());
        ComplicationTickReceiver.schedule(this);
    }
}
