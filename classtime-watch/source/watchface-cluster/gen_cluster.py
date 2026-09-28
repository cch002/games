#!/usr/bin/env python3
"""Generates res/raw/watchface.xml for "Class Time Cluster", a bubble-cluster layout.

Time sits in a pill on the left; everything else is a bubble. The big bubble on the right is
the class countdown (Class Time "Current class"), with its progress ring around the edge.
Shares expression/markup helpers with gen_face.py.
Run: python3 gen_cluster.py > res/raw/watchface.xml
"""
import gen_face as g
from gen_face import W, text, group, condition, list_config, AWAKE_ONLY, AMBIENT_ONLY

ACCENT = "[CONFIGURATION.accent.0]"   # rings, countdown, icons
TINT = "[CONFIGURATION.accent.1]"     # light text on the bubbles

PALETTES = [  # id, name, accent, light tint
    ("0", "accent_lime", "#FFA3E635", "#FFECFCCB"),
    ("1", "accent_amber", "#FFF59E0B", "#FFFEF3C7"),
    ("2", "accent_teal", "#FF2DD4BF", "#FFCCFBF1"),
    ("3", "accent_sky", "#FF38BDF8", "#FFE0F2FE"),
    ("4", "accent_indigo", "#FF818CF8", "#FFE0E7FF"),
    ("5", "accent_pink", "#FFF472B6", "#FFFCE7F3"),
    ("6", "accent_coral", "#FFF7797D", "#FFFFE4E6"),
    ("7", "accent_white", "#FFE2E8F0", "#FFF8FAFC"),
]

BUBBLE_ALPHA = 40   # accent-coloured bubble fill, ~16% over black

# Geometry (450 x 450). Every bubble stays inside the round screen and clear of its neighbours;
# check_geometry() below asserts both.
PILL = dict(x=30, y=193, w=192, h=66)
HERO = dict(id="0", cx=318, cy=214, d=176)
BUBBLES = [  # slot id, centre, diameter, label, default provider, type
    dict(id="1", cx=250, cy=358, d=110, name="slot_next_label", provider=None, ptype="SHORT_TEXT"),
    dict(id="2", cx=100, cy=150, d=64, name="slot_topleft_label", provider="WATCH_BATTERY", ptype="RANGED_VALUE"),
    dict(id="3", cx=196, cy=118, d=104, name="slot_top_label", provider="STEP_COUNT", ptype="SHORT_TEXT"),
    dict(id="4", cx=100, cy=300, d=64, name="slot_bottomleft_label", provider="DAY_AND_DATE", ptype="SHORT_TEXT"),
]


def check_geometry():
    import math
    circles = [(HERO["cx"], HERO["cy"], HERO["d"] / 2)] + [(b["cx"], b["cy"], b["d"] / 2) for b in BUBBLES]
    for cx, cy, r in circles:
        assert math.hypot(cx - 225, cy - 225) + r <= 212, ("off screen", cx, cy)
    for i, a in enumerate(circles):
        for b in circles[i + 1:]:
            assert math.hypot(a[0] - b[0], a[1] - b[1]) >= a[2] + b[2] + 6, ("overlap", a, b)
    px, py, pw, ph = PILL["x"], PILL["y"], PILL["w"], PILL["h"]
    for cx, cy, r in circles:  # circle vs rectangle clearance
        nx, ny = min(max(cx, px), px + pw), min(max(cy, py), py + ph)
        assert math.hypot(cx - nx, cy - ny) >= r + 6, ("pill overlap", cx, cy)


# ---------------------------------------------------------------- building blocks

def disc(d, color, alpha, awake_only=True):
    v = AWAKE_ONLY if awake_only else ""
    return (f'<PartDraw x="0" y="0" width="{d}" height="{d}" alpha="{alpha}">{v}'
            f'<Ellipse x="0" y="0" width="{d}" height="{d}"><Fill color="{color}"/></Ellipse></PartDraw>')


def ring_track(d, inset, thickness):
    c, rd = d / 2, d - 2 * inset
    return (f'<PartDraw x="0" y="0" width="{d}" height="{d}" alpha="70">'
            f'<Arc centerX="{c}" centerY="{c}" width="{rd}" height="{rd}" startAngle="0" endAngle="360">'
            f'<Stroke thickness="{thickness}" color="{ACCENT}"/></Arc></PartDraw>')


def ring_progress(d, inset, thickness, progress_expr):
    c, rd = d / 2, d - 2 * inset
    return (f'<PartDraw x="0" y="0" width="{d}" height="{d}">'
            f'<Arc centerX="{c}" centerY="{c}" width="{rd}" height="{rd}" startAngle="0" endAngle="0">'
            f'<Stroke thickness="{thickness}" color="{ACCENT}" cap="ROUND"/>'
            f'<Transform target="endAngle" value="{progress_expr}"/></Arc></PartDraw>')


def ring(d, inset, thickness, progress_expr):
    return ring_track(d, inset, thickness) + ring_progress(d, inset, thickness, progress_expr)


def icon(d, y, size, tint=ACCENT, field="MONOCHROMATIC_IMAGE"):
    x = (d - size) // 2
    return (f'<PartImage x="{x}" y="{y}" width="{size}" height="{size}" tintColor="{tint}">'
            f'<Image resource="[COMPLICATION.{field}]"/></PartImage>')


def centred(d, y, h, size, field, color=TINT, weight="MEDIUM", pad=None):
    pad = pad if pad is not None else d // 7
    return text(pad, y, d - 2 * pad, h, size, color, "%s", [f"[COMPLICATION.{field}]"], weight=weight, ellipsis=True)


def bubble_body(d):
    """Icon / text / title arrangement for any text-ish complication, scaled to the bubble."""
    big = d >= 90
    s = d / 110.0
    rows = []
    if big:  # room for three rows: icon, text, title
        rows.append(("iconTextTitle",
                     "[COMPLICATION.MONOCHROMATIC_IMAGE] != null &amp;&amp; [COMPLICATION.TEXT] != null &amp;&amp; [COMPLICATION.TITLE] != null",
                     icon(d, int(17 * s), int(18 * s)) + centred(d, int(37 * s), int(32 * s), round(25 * s), "TEXT", weight="SEMI_BOLD")
                     + centred(d, int(69 * s), int(22 * s), round(14 * s), "TITLE", color=ACCENT)))
        rows.append(("textTitle", "[COMPLICATION.TEXT] != null &amp;&amp; [COMPLICATION.TITLE] != null",
                     centred(d, int(28 * s), int(32 * s), round(25 * s), "TEXT", weight="SEMI_BOLD")
                     + centred(d, int(60 * s), int(22 * s), round(14 * s), "TITLE", color=ACCENT)))
    ti, ty, th, ts = (int(d * 0.2), int(d * 0.47), int(d * 0.3), round(d * 0.22)) if big else (10, 29, 22, 14)
    isz = int(d * 0.2) if big else 16
    rows.append(("iconText", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null &amp;&amp; [COMPLICATION.TEXT] != null",
                 icon(d, ti, isz) + centred(d, ty, th, ts, "TEXT", weight="SEMI_BOLD", pad=6)))
    rows.append(("textOnly", "[COMPLICATION.TEXT] != null",
                 centred(d, int(d * 0.3), int(d * 0.4), round(d * (0.24 if big else 0.25)), "TEXT", weight="SEMI_BOLD", pad=6)))
    rows.append(("iconOnly", "[COMPLICATION.MONOCHROMATIC_IMAGE] != null", icon(d, int(d * 0.28), int(d * 0.44))))
    return condition(rows)


def bubble_slot(b):
    d, sid = b["d"], b["id"]
    x, y = b["cx"] - d // 2, b["cy"] - d // 2
    inset = 5 if d < 90 else 6
    thick = 4 if d < 90 else 6
    ranged = (disc(d, ACCENT, BUBBLE_ALPHA)
              + group(f"ring{sid}", ring(d, inset, thick, g.GENERIC_PROGRESS), w=d, h=d, alpha=255, variant=AWAKE_ONLY)
              + bubble_body(d))
    textual = disc(d, ACCENT, BUBBLE_ALPHA) + bubble_body(d)
    mono = disc(d, ACCENT, BUBBLE_ALPHA) + icon(d, int(d * 0.28), int(d * 0.44))
    small = (f'<PartImage x="{d // 8}" y="{d // 8}" width="{d - d // 4}" height="{d - d // 4}">'
             f'<Image resource="[COMPLICATION.SMALL_IMAGE]"/></PartImage>')
    empty = (f'<PartDraw x="0" y="0" width="{d}" height="{d}" alpha="60">{AWAKE_ONLY}'
             f'<Ellipse x="1" y="1" width="{d - 2}" height="{d - 2}"><Stroke thickness="2" color="{ACCENT}"/></Ellipse></PartDraw>')
    if b["provider"]:
        policy = (f'<DefaultProviderPolicy defaultSystemProvider="{b["provider"]}" '
                  f'defaultSystemProviderType="{b["ptype"]}"/>')
    else:  # Next class: Class Time's own feed
        policy = ('<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" '
                  'primaryProvider="eu.nohus.classtime/eu.nohus.classtime.ClassNextComplicationService" '
                  f'primaryProviderType="{b["ptype"]}"/>')
    ambient = "" if sid == "1" else '<Variant mode="AMBIENT" target="alpha" value="0"/>'
    return (f'<ComplicationSlot x="{x}" y="{y}" width="{d}" height="{d}" slotId="{sid}" displayName="{b["name"]}" '
            'supportedTypes="SHORT_TEXT RANGED_VALUE LONG_TEXT MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY">'
            f'{policy}<BoundingOval x="0" y="0" width="{d}" height="{d}"/>'
            f'<Complication type="SHORT_TEXT">{textual}</Complication>'
            f'<Complication type="RANGED_VALUE">{ranged}</Complication>'
            f'<Complication type="LONG_TEXT">{textual}</Complication>'
            f'<Complication type="MONOCHROMATIC_IMAGE">{mono}</Complication>'
            f'<Complication type="SMALL_IMAGE">{small}</Complication>'
            f'<Complication type="EMPTY">{empty}</Complication>{ambient}</ComplicationSlot>')


def hero_slot():
    d = HERO["d"]
    x, y = HERO["cx"] - d // 2, HERO["cy"] - d // 2
    count_y, count_h, count_s = 62, 52, 46

    def countdown():
        awake_mmss = text(10, count_y, d - 20, count_h, count_s, TINT, "%s:%s", g.MMSS, weight="SEMI_BOLD",
                          alpha=255, variant=AWAKE_ONLY)
        awake_min = text(10, count_y, d - 20, count_h, count_s, TINT, "%sm", g.MINS, weight="SEMI_BOLD",
                         alpha=255, variant=AWAKE_ONLY)
        ambient = text(10, count_y, d - 20, count_h, count_s, "#FFE2E8F0", "%sm", g.MINS, weight="LIGHT",
                       alpha=0, variant=AMBIENT_ONLY)
        return list_config("countdownStyle", [("0", awake_mmss), ("1", awake_min)]) + ambient

    off = text(10, count_y, d - 20, count_h, count_s, "#FF64748B", "%s", ["off_countdown"], weight="SEMI_BOLD")
    other_text = g.if_present("[COMPLICATION.TEXT]", centred(d, count_y + 4, count_h - 8, 36, "TEXT", weight="SEMI_BOLD", pad=14))
    label = g.if_present("[COMPLICATION.TITLE]", text(26, 116, d - 52, 24, 16, ACCENT, "%s", ["[COMPLICATION.TITLE]"],
                                                      weight="MEDIUM", ellipsis=True))
    top_icon = g.if_present("[COMPLICATION.MONOCHROMATIC_IMAGE]", icon(d, 34, 22))
    hero_ring = group("hero_ring", ring_track(d, 7, 8) + condition([
        ("heroOff", g.IS_OFF, ""),
        ("heroClass", g.IS_CLASS, ring_progress(d, 7, 8, g.PROGRESS)),
        ("heroOther", g.HAS_RANGE, ring_progress(d, 7, 8, g.GENERIC_PROGRESS)),
    ]), w=d, h=d, alpha=255, variant=AWAKE_ONLY)
    ranged = (disc(d, ACCENT, BUBBLE_ALPHA + 10) + hero_ring + top_icon
              + condition([("offTheClock", g.IS_OFF, off), ("classCountdown", g.IS_CLASS, countdown())], default=other_text)
              + label)
    textual = disc(d, ACCENT, BUBBLE_ALPHA + 10) + group("hero_track", ring_track(d, 7, 8), w=d, h=d, alpha=255,
                                                         variant=AWAKE_ONLY) + top_icon + other_text + label
    empty = disc(d, ACCENT, BUBBLE_ALPHA) + text(10, 76, d - 20, 24, 18, TINT, "%s", ["no_class_data"])
    return (f'<ComplicationSlot x="{x}" y="{y}" width="{d}" height="{d}" slotId="0" displayName="slot_now_label" '
            'supportedTypes="RANGED_VALUE SHORT_TEXT LONG_TEXT EMPTY">'
            '<DefaultProviderPolicy defaultSystemProvider="EMPTY" defaultSystemProviderType="EMPTY" '
            'primaryProvider="eu.nohus.classtime/eu.nohus.classtime.ClassNowComplicationService" '
            'primaryProviderType="RANGED_VALUE"/>'
            f'<BoundingOval x="0" y="0" width="{d}" height="{d}"/>'
            f'<Complication type="RANGED_VALUE">{ranged}</Complication>'
            f'<Complication type="SHORT_TEXT">{textual}</Complication>'
            f'<Complication type="LONG_TEXT">{textual}</Complication>'
            f'<Complication type="EMPTY">{empty}</Complication></ComplicationSlot>')


def time_pill():
    x, y, w, h = PILL["x"], PILL["y"], PILL["w"], PILL["h"]
    r = h / 2
    fill = (f'<PartDraw x="{x}" y="{y}" width="{w}" height="{h}" alpha="{BUBBLE_ALPHA}">{AWAKE_ONLY}'
            f'<RoundRectangle x="0" y="0" width="{w}" height="{h}" cornerRadiusX="{r}" cornerRadiusY="{r}">'
            f'<Fill color="{ACCENT}"/></RoundRectangle></PartDraw>')
    outline = (f'<PartDraw x="{x}" y="{y}" width="{w}" height="{h}" alpha="0">{AMBIENT_ONLY}'
               f'<RoundRectangle x="1" y="1" width="{w - 2}" height="{h - 2}" cornerRadiusX="{r}" cornerRadiusY="{r}">'
               f'<Stroke thickness="2" color="#FF475569"/></RoundRectangle></PartDraw>')

    def tt(weight, alpha, variant, color):
        return (f'<TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="{x}" y="{y + 4}" width="{w}" '
                f'height="{h - 8}" alpha="{alpha}">{variant}<Font family="SYNC_TO_DEVICE" size="50" weight="{weight}" '
                f'color="{color}"/></TimeText>')
    clock = (f'<DigitalClock x="0" y="0" width="{W}" height="{W}">'
             f'{tt("SEMI_BOLD", 255, AWAKE_ONLY, TINT)}{tt("LIGHT", 0, AMBIENT_ONLY, "#FFE2E8F0")}</DigitalClock>')
    return fill + outline + clock


def user_configurations():
    colors = "".join(f'<ColorOption id="{i}" displayName="{n}" colors="{a} {t}"/>' for i, n, a, t in PALETTES)
    return ('<UserConfigurations>'
            f'<ColorConfiguration id="accent" displayName="accent_label" defaultValue="0">{colors}</ColorConfiguration>'
            '<ListConfiguration id="countdownStyle" displayName="countdown_label" defaultValue="0">'
            '<ListOption id="0" displayName="countdown_mmss"/><ListOption id="1" displayName="countdown_minutes"/>'
            '</ListConfiguration></UserConfigurations>')


def watchface():
    check_geometry()
    scene = time_pill() + hero_slot() + "".join(bubble_slot(b) for b in BUBBLES)
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!-- Generated by gen_cluster.py; edit that file, not this one. -->\n'
            f'<WatchFace width="{W}" height="{W}">'
            '<Metadata key="CLOCK_TYPE" value="DIGITAL"/><Metadata key="PREVIEW_TIME" value="10:08:32"/>'
            f'{user_configurations()}<Scene backgroundColor="#FF000000">{scene}</Scene></WatchFace>\n')


if __name__ == "__main__":
    print(watchface(), end="")
