package eu.nohus.classtime;

import android.content.Context;
import android.content.SharedPreferences;
import android.text.format.DateFormat;
import java.util.Calendar;

/**
 * Where "now" sits in the synced timetable, in wall-clock millis. Shared by the
 * complication data sources that feed the Class Time watch face.
 */
final class ClassSchedule {
    static final int NO_DATA = 0;
    static final int FREE_DAY = 1;     // no lessons today
    static final int BEFORE = 2;       // before the first lesson today
    static final int LESSON = 3;
    static final int BREAK = 4;
    static final int AFTER = 5;        // after the last lesson today

    private static final String PREFS = "eu.nohus.classtime_preferences";
    private static final String TIMETABLE_KEY = "timetableData";

    int state = NO_DATA;
    String lessonName = "";
    String lessonRoom = "";
    long periodStart;   // start of the current lesson / break / wait
    long periodEnd;     // end of the current lesson / break / wait

    boolean hasNext;
    boolean nextIsToday;
    String nextName = "";
    String nextRoom = "";
    long nextStart;
    String nextDayLabel = "";   // e.g. "Tomorrow" or "Mon" when the next lesson is not today

    /** Millis at which this state stops being accurate (a lesson or break boundary, or midnight). */
    long validUntil;

    static ClassSchedule compute(Context context, long nowMillis) {
        ClassSchedule s = new ClassSchedule();
        SharedPreferences prefs = context.getSharedPreferences(PREFS, 0);
        String json = prefs.getString(TIMETABLE_KEY, null);
        if (json == null || json.length() < 3) {
            s.validUntil = nowMillis + 15 * 60 * 1000L;
            return s;
        }
        TimetableEngineReadOnly engine = new TimetableEngineReadOnly(context, json);
        if (engine.store == null) {
            s.validUntil = nowMillis + 15 * 60 * 1000L;
            return s;
        }
        // The app lets the user shift its clock (e.g. to match a school bell); honour it.
        long correction = engine.timeCorrection * 1000L;
        long corrected = nowMillis + correction;

        Calendar cal = Calendar.getInstance();
        cal.setTimeInMillis(corrected);
        int day = toAppDay(cal.get(Calendar.DAY_OF_WEEK));
        int minuteOfDay = cal.get(Calendar.HOUR_OF_DAY) * 60 + cal.get(Calendar.MINUTE);
        cal.set(Calendar.HOUR_OF_DAY, 0);
        cal.set(Calendar.MINUTE, 0);
        cal.set(Calendar.SECOND, 0);
        cal.set(Calendar.MILLISECOND, 0);
        long midnight = cal.getTimeInMillis() - correction;   // real millis of corrected midnight
        long nextMidnight = midnight + dayLengthMillis(cal);

        int count = engine.getLessonsOnDay(day);
        s.validUntil = nextMidnight;
        if (count <= 0) {
            s.state = FREE_DAY;
            s.periodStart = midnight;
            s.periodEnd = nextMidnight;
            s.findNextDay(context, engine, cal, day, midnight);
            return s;
        }

        int firstStart = engine.getLessonStartTime(day, 1);
        int lastEnd = engine.getLessonEndTime(day, count);
        if (minuteOfDay < firstStart) {
            s.state = BEFORE;
            s.periodStart = midnight;
            s.periodEnd = midnight + firstStart * 60000L;
            s.setNextToday(engine, day, 1, midnight);
            s.validUntil = s.periodEnd;
            return s;
        }
        if (minuteOfDay >= lastEnd) {
            s.state = AFTER;
            s.periodStart = midnight + lastEnd * 60000L;
            s.periodEnd = nextMidnight;
            s.findNextDay(context, engine, cal, day, midnight);
            return s;
        }
        for (int i = 1; i <= count; i++) {
            int start = engine.getLessonStartTime(day, i);
            int end = engine.getLessonEndTime(day, i);
            if (minuteOfDay >= start && minuteOfDay < end) {
                s.state = LESSON;
                s.lessonName = clean(engine.getLesson(day, i));
                s.lessonRoom = clean(engine.getRoom(day, i));
                s.periodStart = midnight + start * 60000L;
                s.periodEnd = midnight + end * 60000L;
                if (i < count) s.setNextToday(engine, day, i + 1, midnight);
                else s.findNextDay(context, engine, cal, day, midnight);
                s.validUntil = s.periodEnd;
                return s;
            }
            if (i < count) {
                int nextStart = engine.getLessonStartTime(day, i + 1);
                if (minuteOfDay >= end && minuteOfDay < nextStart) {
                    s.state = BREAK;
                    s.periodStart = midnight + end * 60000L;
                    s.periodEnd = midnight + nextStart * 60000L;
                    s.setNextToday(engine, day, i + 1, midnight);
                    s.validUntil = s.periodEnd;
                    return s;
                }
            }
        }
        // Overlapping or oddly ordered lessons: treat as a gap until the next boundary.
        s.state = BREAK;
        s.periodStart = nowMillis;
        s.periodEnd = nowMillis + 60000L;
        s.validUntil = s.periodEnd;
        return s;
    }

    private void setNextToday(TimetableEngineReadOnly engine, int day, int lesson, long midnight) {
        hasNext = true;
        nextIsToday = true;
        nextName = clean(engine.getLesson(day, lesson));
        nextRoom = clean(engine.getRoom(day, lesson));
        nextStart = midnight + engine.getLessonStartTime(day, lesson) * 60000L;
    }

    private void findNextDay(Context context, TimetableEngineReadOnly engine, Calendar midnightCal, int day, long midnight) {
        Calendar c = (Calendar) midnightCal.clone();
        long dayStart = midnight;
        for (int offset = 1; offset <= 7; offset++) {
            dayStart += dayLengthMillis(c);
            c.add(Calendar.DAY_OF_MONTH, 1);
            int d = ((day - 1 + offset) % 7) + 1;
            if (engine.getLessonsOnDay(d) > 0) {
                hasNext = true;
                nextIsToday = false;
                nextName = clean(engine.getLesson(d, 1));
                nextRoom = clean(engine.getRoom(d, 1));
                nextStart = dayStart + engine.getLessonStartTime(d, 1) * 60000L;
                nextDayLabel = offset == 1 ? "Tomorrow"
                        : DateFormat.format("EEE", c).toString();
                return;
            }
        }
    }

    String formatClock(Context context, long millis) {
        return DateFormat.format(DateFormat.is24HourFormat(context) ? "H:mm" : "h:mm", millis).toString();
    }

    /** Timetable days run 1 = Monday .. 7 = Sunday. */
    private static int toAppDay(int calendarDay) {
        return calendarDay == Calendar.SUNDAY ? 7 : calendarDay - 1;
    }

    private static long dayLengthMillis(Calendar midnight) {
        Calendar next = (Calendar) midnight.clone();
        next.add(Calendar.DAY_OF_MONTH, 1);
        return next.getTimeInMillis() - midnight.getTimeInMillis();
    }

    private static String clean(String s) {
        if (s == null || "READ ERROR".equals(s)) return "";
        return s.trim();
    }
}
