package eu.nohus.classtime;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.support.wearable.complications.ProviderUpdateRequester;

/**
 * Keeps the class complications fresh: every minute while a countdown is running (so faces
 * that only read the ranged value still move), otherwise at the next boundary or midnight.
 * Uses a non-wakeup alarm, so a sleeping watch catches up when it next wakes.
 */
public class ComplicationTickReceiver extends BroadcastReceiver {
    private static final int FLAG_IMMUTABLE = 0x04000000;

    @Override
    public void onReceive(Context context, Intent intent) {
        requestUpdate(context);
        schedule(context);
    }

    static void requestUpdate(Context context) {
        new ProviderUpdateRequester(context,
                new ComponentName(context, ClassNowComplicationService.class)).requestUpdateAll();
        new ProviderUpdateRequester(context,
                new ComponentName(context, ClassNextComplicationService.class)).requestUpdateAll();
    }

    static void schedule(Context context) {
        long now = System.currentTimeMillis();
        ClassSchedule s = ClassSchedule.compute(context, now);
        long at = s.validUntil;
        if (s.resolveBlock(now)) {
            long nextMinute = (now / 60000L + 1) * 60000L;
            at = Math.min(at, nextMinute);
        }
        if (at <= now) at = now + 60000L;
        at += 1000L; // land just after the boundary, not just before it

        Intent tick = new Intent(context, ComplicationTickReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, 0, tick,
                PendingIntent.FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE);
        AlarmManager alarms = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarms != null) alarms.set(AlarmManager.RTC, at, pi);
    }

    static PendingIntent openApp(Context context) {
        Intent open = new Intent(context, TimetableActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        return PendingIntent.getActivity(context, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE);
    }
}
