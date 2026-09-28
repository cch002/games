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
         date=(56, 30, 20), time=(84, 66, 54), count=(156, 106, 88), label=(262, 40, 28)),
    dict(id="1", name="layout_clock",
         date=(58, 30, 20), time=(86, 118, 100), count=(204, 58, 50), label=(262, 40, 28)),
    dict(id="2", name="layout_minimal",
         date=None, time=None, count=(140, 120, 92), label=(262, 40, 30)),
]

ACCENT = "[CONFIGURATION.accent.0]"
# Class Time's "Current class" sends seconds-of-day + MARKER so the face can recognise it.
MARKER = 1000000
REM = f"clamp([COMPLICATION.RANGED_VALUE_MAX] - {MARKER} - [SECONDS_IN_DAY], 0, 86400)"
MMSS = [f'numberFormat("0", floor({REM} / 60))', f'numberFormat("00", {REM} % 60)']
MINS = [f'numberFormat("0", ceil({REM} / 60))']
PROGRESS = (f"360 * clamp(([SECONDS_IN_DAY] + {MARKER} - [COMPLICATION.RANGED_VALUE_MIN]) / "
            "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)")
# Any other ranged complication: plain value progress.
GENERIC_PROGRESS = ("360 * clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / "
                    "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)")
IS_OFF = f"[COMPLICATION.RANGED_VALUE_MIN] &gt;= {MARKER - 1} &amp;&amp; [COMPLICATION.RANGED_VALUE_MIN] &lt; {MARKER}"
IS_CLASS = f"[COMPLICATION.RANGED_VALUE_MIN] &gt;= {MARKER}"
HAS_RANGE = "[COMPLICATION.RANGED_VALUE_MAX] &gt; [COMPLICATION.RANGED_VALUE_MIN]"


def condition(branches, default=""):
    """branches: list of (name, expression, body); first match wins."""
    exprs = "".join(f'<Expression name="{n}">{e}</Expression>' for n, e, _ in branches)
    cmps = "".join(f'<Compare expression="{n}">{group(n + "_body", b)}</Compare>' for n, _, b in branches)
    d = f"<Default>{group('default_body', default)}</Default>" if default else ""
    return f"<Condition><Expressions>{exprs}</Expressions>{cmps}{d}</Condition>"


def if_present(field, body):
    """Only draw body when the complication actually sent this field."""
    name = "has_" + field.split(".")[-1].rstrip("]").lower()
    return condition([(name, f"{field} != null", body)])

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


def off_block(L):  # noqa: E302
    y, h, s = L["count"]
    return text(40, y, 370, h, s, "#FF64748B", "%s", ["off_countdown"], weight="SEMI_BOLD")


def label_block(L):
    y, h, s = L["label"]
    return text(50, y, 350, h, s, "#FFCBD5E1", "%s", ["[COMPLICATION.TITLE]"], weight="MEDIUM", ellipsis=True)


def ring_block(ranged=True):
    """Progress ring. ranged=False draws only the track (for text complications in the middle slot)."""
    def arc(d, thickness, color, end_expr=None):
        t = f'<Transform target="endAngle" value="{end_expr}"/>' if end_expr else ""
        cap = ' cap="ROUND"' if end_expr else ""
        end_angle = "0" if end_expr else "360"
        return (f'<PartDraw x="0" y="0" width="{W}" height="{W}">'
                f'<Arc centerX="225" centerY="225" width="{d}" height="{d}" startAngle="0" endAngle="{end_angle}">'
                f'<Stroke thickness="{thickness}" color="{color}"{cap}/>{t}</Arc></PartDraw>')

    def ring(thickness):
        d = 450 - 14 - thickness  # keep the stroke inside the screen edge
        track = arc(d, thickness, "#FF1A1F26")
        if not ranged:
            return track
        progress = condition([
            ("ringOff", IS_OFF, ""),
            ("ringClass", IS_CLASS, arc(d, thickness, ACCENT, PROGRESS)),
            ("ringOther", HAS_RANGE, arc(d, thickness, ACCENT, GENERIC_PROGRESS)),
        ])
        return track + progress
    body = list_config("ring", [("0", ring(12)), ("1", ring(6)), ("2", "")])
    return group("ring", body, alpha=255, variant=AWAKE_ONLY)


def big_text_block(L):
    """Another complication in the middle slot: its text in the countdown position."""
    y, h, s = L["count"]
    return if_present("[COMPLICATION.TEXT]",
                      text(40, y, 370, h, round(s * 0.8), ACCENT, "%s", ["[COMPLICATION.TEXT]"],
                           weight="SEMI_BOLD", ellipsis=True))


def title_block(L):
    return if_present("[COMPLICATION.TITLE]", label_block(L))


def now_slot():
    ranged = (ring_block()
              + condition([
                  ("offTheClock", IS_OFF, per_layout("layout", off_block)),
                  ("classCountdown", IS_CLASS, per_layout("layout", countdown_block)),
              ], default=per_layout("layout", big_text_block))
              + group("label", per_layout("layout", title_block)))
    textual = (ring_block(ranged=False) + group("big", per_layout("layout", big_text_block))
               + group("label", per_layout("layout", title_block)))
    empty = text(50, 190, 350, 40, 24, "#FF64748B", "%s", ["no_class_data"])
    return (f'<ComplicationSlot x="0" y="0" width="{W}" height="{W}" slotId="0" displayName="slot_now_label" '
            f'supportedTypes="RANGED_VALUE SHORT_TEXT LONG_TEXT EMPTY">'
            f'<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" '
            f'primaryProvider="eu.nohus.classtime/eu.nohus.classtime.ClassNowComplicationService" '
            f'primaryProviderType="RANGED_VALUE"/>'
            f'<BoundingBox x="40" y="126" width="370" height="176"/>'
            f'<Complication type="RANGED_VALUE">{ranged}</Complication>'
            f'<Complication type="SHORT_TEXT">{textual}</Complication>'
            f'<Complication type="LONG_TEXT">{textual}</Complication>'
            f'<Complication type="EMPTY">{empty}</Complication></ComplicationSlot>')


NEXT_W, NEXT_H = 260, 60
TITLE_COLOR, TEXT_COLOR = "#FF64748B", "#FFE2E8F0"


def next_title_line():
    return text(0, 0, NEXT_W, 26, 18, TITLE_COLOR, "%s", ["[COMPLICATION.TITLE]"], weight="MEDIUM", ellipsis=True)


def next_text_line(y=26, h=32):
    return text(0, y, NEXT_W, h, 22, TEXT_COLOR, "%s", ["[COMPLICATION.TEXT]"], ellipsis=True)


def next_icon(y, size):
    x = (NEXT_W - size) // 2
    return (f'<PartImage x="{x}" y="{y}" width="{size}" height="{size}" tintColor="#FF94A3B8">'
            f'<Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>')


def next_two_lines():
    """Title (or icon) above, text below; text alone is centred when there is nothing above it."""
    return condition([
        ("titleAndText", "[COMPLICATION.TITLE] != null &amp;&amp; [COMPLICATION.TEXT] != null",
         next_title_line() + next_text_line()),
        ("iconAndText", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null &amp;&amp; [COMPLICATION.TEXT] != null",
         next_icon(2, 22) + next_text_line()),
        ("textOnly", "[COMPLICATION.TEXT] != null", next_text_line(12, 36)),
        ("iconOnly", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null", next_icon(14, 32)),
    ])


def next_ranged_bar():
    """Thin progress bar under a ranged complication."""
    return condition([("barRange", HAS_RANGE,
        f'<PartDraw x="80" y="57" width="100" height="3">'
        f'<RoundRectangle x="0" y="0" width="100" height="3" cornerRadiusX="1.5" cornerRadiusY="1.5">'
        f'<Fill color="#FF1E293B"/></RoundRectangle>'
        f'<RoundRectangle x="0" y="0" width="100" height="3" cornerRadiusX="1.5" cornerRadiusY="1.5">'
        f'<Fill color="{ACCENT}"/>'
        f'<Transform target="width" value="100 * clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / '
        f'([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)"/>'
        f'</RoundRectangle></PartDraw>')])


def next_slot():
    mono = next_icon(14, 32)
    small = (f'<PartImage x="{(NEXT_W - 40) // 2}" y="10" width="40" height="40">'
             f'<Image resource="[COMPLICATION.SMALL_IMAGE]"/></PartImage>')
    empty = (f'<PartDraw x="0" y="0" width="{NEXT_W}" height="{NEXT_H}"><Line startX="100" startY="30" endX="160" endY="30">'
             '<Stroke thickness="2" color="#FF1E293B"/></Line></PartDraw>')
    return (f'<ComplicationSlot x="95" y="306" width="{NEXT_W}" height="{NEXT_H}" slotId="1" displayName="slot_next_label" '
            'supportedTypes="LONG_TEXT SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY">'
            '<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" '
            'primaryProvider="eu.nohus.classtime/eu.nohus.classtime.ClassNextComplicationService" '
            'primaryProviderType="LONG_TEXT"/>'
            f'<BoundingBox x="0" y="0" width="{NEXT_W}" height="{NEXT_H}"/>'
            f'<Complication type="LONG_TEXT">{next_two_lines()}</Complication>'
            f'<Complication type="SHORT_TEXT">{next_two_lines()}</Complication>'
            f'<Complication type="RANGED_VALUE">{next_two_lines()}{next_ranged_bar()}</Complication>'
            f'<Complication type="MONOCHROMATIC_IMAGE">{mono}</Complication>'
            f'<Complication type="SMALL_IMAGE">{small}</Complication>'
            f'<Complication type="EMPTY">{empty}</Complication></ComplicationSlot>')


# ---------------------------------------------------------------- extra slots

SIDE = 60                       # diameter of the round side slots
SIDE_Y = 178                    # beside the countdown in every layout
SIDE_XS = {"2": 38, "3": 352}   # slotId -> x (clear of the countdown and inside the ring)
SLOT_BG = "#FF11161C"


def side_contents(ranged):
    c = SIDE / 2
    bg = (f'<PartDraw x="0" y="0" width="{SIDE}" height="{SIDE}"><Ellipse x="0" y="0" width="{SIDE}" height="{SIDE}">'
          f'<Fill color="{SLOT_BG}"/></Ellipse></PartDraw>')
    ring = ""
    if ranged:
        d = SIDE - 6
        ring = (f'<PartDraw x="0" y="0" width="{SIDE}" height="{SIDE}">'
                f'<Arc centerX="{c}" centerY="{c}" width="{d}" height="{d}" startAngle="0" endAngle="360">'
                f'<Stroke thickness="4" color="#FF1E293B"/></Arc></PartDraw>'
                + condition([("sideRange", HAS_RANGE,
                    f'<PartDraw x="0" y="0" width="{SIDE}" height="{SIDE}">'
                    f'<Arc centerX="{c}" centerY="{c}" width="{d}" height="{d}" startAngle="0" endAngle="0">'
                    f'<Stroke thickness="4" color="{ACCENT}" cap="ROUND"/>'
                    f'<Transform target="endAngle" value="{GENERIC_PROGRESS}"/></Arc></PartDraw>')]))

    def icon(y, size):
        x = (SIDE - size) // 2
        return (f'<PartImage x="{x}" y="{y}" width="{size}" height="{size}" tintColor="#FFCBD5E1">'
                f'<Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>')

    def line(y, h, size):
        return text(4, y, SIDE - 8, h, size, "#FFE2E8F0", "%s", ["[COMPLICATION.TEXT]"], weight="MEDIUM", ellipsis=True)
    body = condition([
        ("sideIconText", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null &amp;&amp; [COMPLICATION.TEXT] != null",
         icon(10, 18) + line(28, 22, 15)),
        ("sideText", "[COMPLICATION.TEXT] != null", line(18, 24, 18)),
        ("sideIcon", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null", icon(15, 30)),
    ])
    return bg + ring + body


def side_slot(slot_id, provider, provider_type):
    x = SIDE_XS[slot_id]
    mono = (f'<PartDraw x="0" y="0" width="{SIDE}" height="{SIDE}"><Ellipse x="0" y="0" width="{SIDE}" height="{SIDE}">'
            f'<Fill color="{SLOT_BG}"/></Ellipse></PartDraw>'
            f'<PartImage x="15" y="15" width="30" height="30" tintColor="#FFCBD5E1">'
            f'<Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>')
    small = (f'<PartImage x="4" y="4" width="{SIDE - 8}" height="{SIDE - 8}">'
             f'<Image resource="[COMPLICATION.SMALL_IMAGE]"/></PartImage>')
    return (f'<ComplicationSlot x="{x}" y="{SIDE_Y}" width="{SIDE}" height="{SIDE}" slotId="{slot_id}" '
            f'displayName="slot_side_{slot_id}_label" '
            'supportedTypes="RANGED_VALUE SHORT_TEXT MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY">'
            f'<DefaultProviderPolicy defaultSystemProvider="{provider}" defaultSystemProviderType="{provider_type}"/>'
            f'<BoundingOval x="0" y="0" width="{SIDE}" height="{SIDE}"/>'
            f'<Complication type="RANGED_VALUE">{side_contents(True)}</Complication>'
            f'<Complication type="SHORT_TEXT">{side_contents(False)}</Complication>'
            f'<Complication type="MONOCHROMATIC_IMAGE">{mono}</Complication>'
            f'<Complication type="SMALL_IMAGE">{small}</Complication>'
            f'<Complication type="EMPTY">{group("side_empty", "", w=SIDE, h=SIDE)}</Complication>'
            f'<Variant mode="AMBIENT" target="alpha" value="0"/>'
            f'</ComplicationSlot>')


CHIP_X, CHIP_Y, CHIP_W, CHIP_H = 140, 372, 170, 34


def chip_contents(ranged):
    pill = (f'<PartDraw x="0" y="0" width="{CHIP_W}" height="{CHIP_H}">'
            f'<RoundRectangle x="0" y="0" width="{CHIP_W}" height="{CHIP_H}" cornerRadiusX="17" cornerRadiusY="17">'
            f'<Fill color="#FF1E293B"/></RoundRectangle></PartDraw>')
    fill = ""
    if ranged:
        fill = condition([("chipRange", HAS_RANGE,
            f'<PartDraw x="0" y="0" width="{CHIP_W}" height="{CHIP_H}" alpha="90">'
            f'<RoundRectangle x="0" y="0" width="{CHIP_W}" height="{CHIP_H}" cornerRadiusX="17" cornerRadiusY="17">'
            f'<Fill color="{ACCENT}"/>'
            f'<Transform target="width" value="{CHIP_H} + ({CHIP_W} - {CHIP_H}) * clamp(([COMPLICATION.RANGED_VALUE_VALUE] - '
            f'[COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)"/>'
            f'</RoundRectangle></PartDraw>')])
    marker_icon = (f'<PartImage x="14" y="8" width="18" height="18" tintColor="{ACCENT}">'
                   f'<Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>')
    marker_dot = (f'<PartDraw x="19" y="13" width="8" height="8"><Ellipse x="0" y="0" width="8" height="8">'
                  f'<Fill color="{ACCENT}"/></Ellipse></PartDraw>')

    def words(template, params):
        return text(36, 0, CHIP_W - 48, CHIP_H, 18, "#FFCBD5E1", template, params, weight="SEMI_BOLD", ellipsis=True)
    body = condition([
        ("chipTextTitle", "[COMPLICATION.TEXT] != null &amp;&amp; [COMPLICATION.TITLE] != null",
         words("%s %s", ["[COMPLICATION.TEXT]", "[COMPLICATION.TITLE]"])),
        ("chipText", "[COMPLICATION.TEXT] != null", words("%s", ["[COMPLICATION.TEXT]"])),
    ])
    marker = condition([("chipHasIcon", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null", marker_icon)], default=marker_dot)
    return pill + fill + marker + body


def chip_slot():
    mono = (f'<PartDraw x="0" y="0" width="{CHIP_W}" height="{CHIP_H}">'
            f'<RoundRectangle x="0" y="0" width="{CHIP_W}" height="{CHIP_H}" cornerRadiusX="17" cornerRadiusY="17">'
            f'<Fill color="#FF1E293B"/></RoundRectangle></PartDraw>'
            f'<PartImage x="{(CHIP_W - 22) // 2}" y="6" width="22" height="22" tintColor="#FFCBD5E1">'
            f'<Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/></PartImage>')
    return (f'<ComplicationSlot x="{CHIP_X}" y="{CHIP_Y}" width="{CHIP_W}" height="{CHIP_H}" slotId="4" '
            'displayName="slot_bottom_label" supportedTypes="SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE EMPTY">'
            '<DefaultProviderPolicy defaultSystemProvider="UNREAD_NOTIFICATION_COUNT" defaultSystemProviderType="SHORT_TEXT"/>'
            f'<BoundingBox x="0" y="0" width="{CHIP_W}" height="{CHIP_H}"/>'
            f'<Complication type="SHORT_TEXT">{chip_contents(False)}</Complication>'
            f'<Complication type="RANGED_VALUE">{chip_contents(True)}</Complication>'
            f'<Complication type="MONOCHROMATIC_IMAGE">{mono}</Complication>'
            f'<Complication type="EMPTY">{group("chip_empty", "", w=CHIP_W, h=CHIP_H)}</Complication>'
            '<Variant mode="AMBIENT" target="alpha" value="0"/>'
            '</ComplicationSlot>')


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
            '</UserConfigurations>')


def watchface():
    scene = (background()
             + list_config("layout", [(L["id"], date_block(L) + time_block(L)) for L in LAYOUTS])
             + now_slot() + next_slot()
             + side_slot("2", "WATCH_BATTERY", "RANGED_VALUE") + side_slot("3", "STEP_COUNT", "SHORT_TEXT")
             + chip_slot())
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!-- Generated by gen_face.py; edit that file, not this one. -->\n'
            f'<WatchFace width="{W}" height="{W}">'
            '<Metadata key="CLOCK_TYPE" value="DIGITAL"/><Metadata key="PREVIEW_TIME" value="10:08:32"/>'
            f'{user_configurations()}<Scene backgroundColor="#FF000000">{scene}</Scene></WatchFace>\n')


if __name__ == "__main__":
    print(watchface(), end="")
