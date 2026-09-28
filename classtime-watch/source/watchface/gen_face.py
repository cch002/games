#!/usr/bin/env python3
"""Generates res/raw/watchface.xml for the Class Time watch face.

Every layout variant is produced from the LAYOUTS table, so the customization options
(layout, countdown style, ring, background, toggles) stay consistent with each other.
Run from the watch face project folder: python3 gen_face.py > res/raw/watchface.xml
"""

W = 450

ACCENTS = [  # id, string name, colour
    ("0", "accent_amber", "#FFF59E0B"),
    ("1", "accent_teal", "#FF4FD1C5"),
    ("2", "accent_coral", "#FFF7797D"),
    ("3", "accent_indigo", "#FF818CF8"),
    ("4", "accent_lime", "#FFA3E635"),
    ("5", "accent_sky", "#FF38BDF8"),
    ("6", "accent_pink", "#FFF472B6"),
    ("7", "accent_white", "#FFF1F5F9"),
]

# Vertical position / height / font size of each block, per layout.
# The next-class slot (y 306-366) and unread chip (y 372-406) are shared by all layouts.
LAYOUTS = [
    dict(id="0", name="layout_countdown",
         date=(56, 30, 20), time=(84, 66, 54), count=(152, 112, 96), label=(262, 40, 28)),
    dict(id="1", name="layout_clock",
         date=(58, 30, 20), time=(86, 118, 100), count=(204, 58, 50), label=(262, 40, 28)),
    dict(id="2", name="layout_minimal",
         date=None, time=None, count=(126, 136, 118), label=(262, 40, 30)),
]

ACCENT = "[CONFIGURATION.accent.0]"
REM = "clamp([COMPLICATION.RANGED_VALUE_MAX] - [SECONDS_IN_DAY], 0, 86400)"
MMSS = [f'numberFormat("0", floor({REM} / 60))', f'numberFormat("00", {REM} % 60)']
MINS = [f'numberFormat("0", ceil({REM} / 60))']
PROGRESS = ("360 * clamp(([SECONDS_IN_DAY] - [COMPLICATION.RANGED_VALUE_MIN]) / "
            "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)")

AWAKE_ONLY = '<Variant mode="AMBIENT" target="alpha" value="0"/>'
AMBIENT_ONLY = '<Variant mode="AMBIENT" target="alpha" value="255"/>'


def text(x, y, w, h, size, color, template, params, weight="NORMAL", ellipsis=False, alpha=None, variant=""):
    a = f' alpha="{alpha}"' if alpha is not None else ""
    e = ' ellipsis="TRUE"' if ellipsis else ""
    ps = "".join(f"<Parameter expression='{p}'/>" for p in params)
    return (f'<PartText x="{x}" y="{y}" width="{w}" height="{h}"{a}>{variant}'
            f'<Text align="CENTER"{e}><Font family="SYNC_TO_DEVICE" size="{size}" weight="{weight}" color="{color}">'
            f'<Template>{template}{ps}</Template></Font></Text></PartText>')


def group(name, body, x=0, y=0, w=W, h=W, alpha=None, variant=""):
    a = f' alpha="{alpha}"' if alpha is not None else ""
    return f'<Group name="{name}" x="{x}" y="{y}" width="{w}" height="{h}"{a}>{variant}{body}</Group>'


def list_config(cid, options):
    """options: list of (option id, body). Each body is wrapped in a Group so any content is valid."""
    opts = "".join(f'<ListOption id="{oid}">{group(f"{cid}_{oid}", body)}</ListOption>' for oid, body in options)
    return f'<ListConfiguration id="{cid}">{opts}</ListConfiguration>'


def bool_config(cid, body_true):
    return (f'<BooleanConfiguration id="{cid}"><BooleanOption id="TRUE">{group(f"{cid}_on", body_true)}'
            f'</BooleanOption></BooleanConfiguration>')


def per_layout(cid, fn):
    return list_config(cid, [(L["id"], fn(L)) for L in LAYOUTS])


# ---------------------------------------------------------------- pieces

def date_block(L):
    if not L["date"]:
        return ""
    y, h, s = L["date"]
    return bool_config("showDate", text(75, y, 300, h, s, "#FF94A3B8", "%s, %s %s",
                                        ["[DAY_OF_WEEK_F]", "[MONTH_S]", "[DAY]"], weight="MEDIUM"))


def time_block(L):
    if not L["time"]:
        return ""
    y, h, s = L["time"]
    def tt(weight, alpha, variant):
        return (f'<TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="{y}" width="{W}" '
                f'height="{h}" alpha="{alpha}">{variant}<Font family="SYNC_TO_DEVICE" size="{s}" weight="{weight}" '
                f'color="#FFFFFFFF"/></TimeText>')
    return (f'<DigitalClock x="0" y="0" width="{W}" height="{W}">'
            f'{tt("MEDIUM", 255, AWAKE_ONLY)}{tt("THIN", 0, AMBIENT_ONLY)}</DigitalClock>')


def countdown_block(L):
    y, h, s = L["count"]
    awake_mmss = text(40, y, 370, h, s, ACCENT, "%s:%s", MMSS, weight="SEMI_BOLD", alpha=255, variant=AWAKE_ONLY)
    awake_min = text(40, y, 370, h, s, ACCENT, "%sm", MINS, weight="SEMI_BOLD", alpha=255, variant=AWAKE_ONLY)
    ambient = text(40, y, 370, h, s, "#FFCBD5E1", "%sm", MINS, weight="LIGHT", alpha=0, variant=AMBIENT_ONLY)
    return list_config("countdownStyle", [("0", awake_mmss), ("1", awake_min)]) + ambient


def off_block(L):
    y, h, s = L["count"]
    return text(40, y, 370, h, s, "#FF64748B", "%s", ["off_countdown"], weight="SEMI_BOLD")


def label_block(L):
    y, h, s = L["label"]
    return text(50, y, 350, h, s, "#FFCBD5E1", "%s", ["[COMPLICATION.TITLE]"], weight="MEDIUM", ellipsis=True)


def ring_block():
    def ring(thickness):
        d = 450 - 14 - thickness  # keep the stroke inside the screen edge
        track = (f'<PartDraw x="0" y="0" width="{W}" height="{W}">'
                 f'<Arc centerX="225" centerY="225" width="{d}" height="{d}" startAngle="0" endAngle="360">'
                 f'<Stroke thickness="{thickness}" color="#FF1A1F26"/></Arc></PartDraw>')
        progress = (f'<Condition><Expressions><Expression name="ringOff">[COMPLICATION.RANGED_VALUE_MIN] &lt; 0'
                    f'</Expression></Expressions><Compare expression="ringOff">{group("ring_idle", "")}</Compare>'
                    f'<Default><PartDraw x="0" y="0" width="{W}" height="{W}">'
                    f'<Arc centerX="225" centerY="225" width="{d}" height="{d}" startAngle="0" endAngle="0">'
                    f'<Stroke thickness="{thickness}" color="{ACCENT}" cap="ROUND"/>'
                    f'<Transform target="endAngle" value="{PROGRESS}"/></Arc></PartDraw></Default></Condition>')
        return track + progress
    body = list_config("ring", [("0", ring(12)), ("1", ring(6)), ("2", "")])
    return group("ring", body, alpha=255, variant=AWAKE_ONLY)


def now_slot():
    ranged = (ring_block()
              + '<Condition><Expressions><Expression name="offTheClock">[COMPLICATION.RANGED_VALUE_MIN] &lt; 0'
                '</Expression></Expressions>'
              + f'<Compare expression="offTheClock">{group("off", per_layout("layout", off_block))}</Compare>'
              + f'<Default>{group("counting", per_layout("layout", countdown_block))}</Default></Condition>'
              + group("label", per_layout("layout", label_block)))
    empty = text(50, 190, 350, 40, 24, "#FF64748B", "%s", ["no_class_data"])
    return (f'<ComplicationSlot x="0" y="0" width="{W}" height="{W}" slotId="0" displayName="slot_now_label" '
            f'supportedTypes="RANGED_VALUE EMPTY">'
            f'<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" '
            f'primaryProvider="eu.nohus.classtime/eu.nohus.classtime.ClassNowComplicationService" '
            f'primaryProviderType="RANGED_VALUE"/>'
            f'<BoundingBox x="40" y="126" width="370" height="176"/>'
            f'<Complication type="RANGED_VALUE">{ranged}</Complication>'
            f'<Complication type="EMPTY">{empty}</Complication></ComplicationSlot>')


def next_slot():
    def lines():
        return (text(0, 0, 260, 26, 18, "#FF64748B", "%s", ["[COMPLICATION.TITLE]"], weight="MEDIUM", ellipsis=True)
                + text(0, 26, 260, 32, 22, "#FFE2E8F0", "%s", ["[COMPLICATION.TEXT]"], ellipsis=True))
    shown = lambda: group("next", bool_config("showNext", lines()), w=260, h=60)
    empty = ('<PartDraw x="0" y="0" width="260" height="60"><Line startX="100" startY="30" endX="160" endY="30">'
             '<Stroke thickness="2" color="#FF1E293B"/></Line></PartDraw>')
    return ('<ComplicationSlot x="95" y="306" width="260" height="60" slotId="1" displayName="slot_next_label" '
            'supportedTypes="LONG_TEXT SHORT_TEXT EMPTY">'
            '<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" '
            'primaryProvider="eu.nohus.classtime/eu.nohus.classtime.ClassNextComplicationService" '
            'primaryProviderType="LONG_TEXT"/>'
            '<BoundingBox x="0" y="0" width="260" height="60"/>'
            f'<Complication type="LONG_TEXT">{shown()}</Complication>'
            f'<Complication type="SHORT_TEXT">{shown()}</Complication>'
            f'<Complication type="EMPTY">{empty}</Complication></ComplicationSlot>')


def unread_chip():
    chip = ('<Condition><Expressions><Expression name="hasUnread">[UNREAD_NOTIFICATION_COUNT] &gt; 0</Expression>'
            '</Expressions><Compare expression="hasUnread">'
            '<PartDraw x="0" y="0" width="150" height="34">'
            '<RoundRectangle x="0" y="0" width="150" height="34" cornerRadiusX="17" cornerRadiusY="17">'
            '<Fill color="#FF1E293B"/></RoundRectangle>'
            f'<Ellipse x="22" y="13" width="8" height="8"><Fill color="{ACCENT}"/></Ellipse></PartDraw>'
            + text(34, 0, 104, 34, 18, "#FFCBD5E1", "%s Unread", ["[UNREAD_NOTIFICATION_COUNT]"], weight="SEMI_BOLD")
            + '</Compare></Condition>')
    return group("unread", bool_config("showUnread", group("chip", chip, x=150, y=372, w=150, h=34)),
                 alpha=255, variant=AWAKE_ONLY)


def background():
    tint = (f'<PartDraw x="0" y="0" width="{W}" height="{W}" alpha="46">{AWAKE_ONLY}'
            f'<Ellipse x="0" y="0" width="{W}" height="{W}"><Fill color="{ACCENT}"/></Ellipse></PartDraw>')
    return list_config("background", [("0", ""), ("1", tint)])


def user_configurations():
    colors = "".join(f'<ColorOption id="{i}" displayName="{n}" colors="{c}"/>' for i, n, c in ACCENTS)
    layouts = "".join(f'<ListOption id="{L["id"]}" displayName="{L["name"]}"/>' for L in LAYOUTS)
    return ('<UserConfigurations>'
            f'<ColorConfiguration id="accent" displayName="accent_label" defaultValue="0">{colors}</ColorConfiguration>'
            f'<ListConfiguration id="layout" displayName="layout_label" defaultValue="0">{layouts}</ListConfiguration>'
            '<ListConfiguration id="countdownStyle" displayName="countdown_label" defaultValue="0">'
            '<ListOption id="0" displayName="countdown_mmss"/><ListOption id="1" displayName="countdown_minutes"/>'
            '</ListConfiguration>'
            '<ListConfiguration id="ring" displayName="ring_label" defaultValue="0">'
            '<ListOption id="0" displayName="ring_bold"/><ListOption id="1" displayName="ring_thin"/>'
            '<ListOption id="2" displayName="ring_off"/></ListConfiguration>'
            '<ListConfiguration id="background" displayName="background_label" defaultValue="0">'
            '<ListOption id="0" displayName="background_black"/><ListOption id="1" displayName="background_tinted"/>'
            '</ListConfiguration>'
            '<BooleanConfiguration id="showDate" displayName="show_date_label" defaultValue="TRUE"/>'
            '<BooleanConfiguration id="showNext" displayName="show_next_label" defaultValue="TRUE"/>'
            '<BooleanConfiguration id="showUnread" displayName="show_unread_label" defaultValue="TRUE"/>'
            '</UserConfigurations>')


def watchface():
    scene = (background()
             + list_config("layout", [(L["id"], date_block(L) + time_block(L)) for L in LAYOUTS])
             + now_slot() + next_slot() + unread_chip())
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!-- Generated by gen_face.py; edit that file, not this one. -->\n'
            f'<WatchFace width="{W}" height="{W}">'
            '<Metadata key="CLOCK_TYPE" value="DIGITAL"/><Metadata key="PREVIEW_TIME" value="10:08:32"/>'
            f'{user_configurations()}<Scene backgroundColor="#FF000000">{scene}</Scene></WatchFace>\n')


if __name__ == "__main__":
    print(watchface(), end="")
