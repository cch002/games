#!/usr/bin/env python3
"""Generates app/src/main/res/raw/watchface.xml (Watch Face Format v2).

The face is drawn entirely with vector shapes, so there are no image assets to
maintain. Tweak the constants below and re-run:  python3 generate_watchface.py

Notes from testing on a Pixel Watch 3:
- Text templates must use %s. %d renders nothing on the watch.
- The battery and steps rings are complication slots, not the built-in
  [BATTERY_PERCENT] / [STEP_COUNT] sources, so they can be swapped in Edit.
"""
import math
from pathlib import Path

SIZE = 450
C = SIZE / 2

# Palette
WHITE = "#FFFFFF"
TICK_GREY = "#8A8A8A"
DISC = "#1E1E1E"          # background of the round sub-dials
TRACK = "#3A3A3A"         # unfilled part of the gauges
BLUE = "#3DB2E8"          # left ring + day-of-week
GREEN = "#2BD66B"         # right ring
RED = "#E8322B"           # second hand
SUN = "#F28B82"           # bottom complication icon tint

FONT = "SYNC_TO_DEVICE"   # the watch's system font

# Layout
NUMERAL_R = 180
GAUGE_DX = 90             # left/right gauge centre offset from face centre
GAUGE_R = 62              # sub-dial disc radius
ARC_R = 55                # gauge arc radius (centre line of stroke)
ARC_W = 9
ARC_START, ARC_SWEEP = -145, 290   # gap at the bottom of each gauge (0 deg = 12 o'clock)
TOP_Y, BOTTOM_Y, SUB_R = 120, 330, 54

# Complication expressions (same formulas as Google's WFF samples)
RANGED_FRACTION = ("(clamp([COMPLICATION.RANGED_VALUE_VALUE], [COMPLICATION.RANGED_VALUE_MIN], "
                   "[COMPLICATION.RANGED_VALUE_MAX]) - [COMPLICATION.RANGED_VALUE_MIN]) / "
                   "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN])")
GOAL_FRACTION = ("clamp([COMPLICATION.GOAL_PROGRESS_VALUE], 0, [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]) / "
                 "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE]")


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def i(v):
    return str(int(round(v)))


def polar(r, deg):
    a = math.radians(deg)
    return C + r * math.sin(a), C - r * math.cos(a)


def indent(block, levels):
    pad = "  " * levels
    return "\n".join(pad + line if line else line for line in block.splitlines())


def ticks():
    out = []
    for n in range(60):
        hour = n % 5 == 0
        x0, y0 = polar(203 if hour else 211, n * 6)
        x1, y1 = polar(222, n * 6)
        colour, width = (WHITE, 4) if hour else (TICK_GREY, 2)
        out.append(
            f'        <Line startX="{f(x0)}" startY="{f(y0)}" endX="{f(x1)}" endY="{f(y1)}">'
            f'<Stroke color="{colour}" thickness="{width}" cap="BUTT"/></Line>'
        )
    return "\n".join(out)


def numerals():
    out = []
    w, h = 50, 36
    for n in range(1, 13):
        x, y = polar(NUMERAL_R, n * 30)
        out.append(f"""      <PartText x="{i(x - w / 2)}" y="{i(y - h / 2)}" width="{w}" height="{h}">
        <Text align="CENTER"><Font family="{FONT}" size="27" weight="MEDIUM" color="{WHITE}">{n}</Font></Text>
      </PartText>""")
    return "\n".join(out)


def disc(name, cx, cy, r):
    return f"""    <PartDraw name="{name}" x="{i(cx - r)}" y="{i(cy - r)}" width="{2 * r}" height="{2 * r}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Ellipse x="0" y="0" width="{2 * r}" height="{2 * r}"><Fill color="{DISC}"/></Ellipse>
    </PartDraw>"""


def text_part(expr, x, y, w, h, size, colour=WHITE, weight="BOLD"):
    return f"""<PartText x="{i(x)}" y="{i(y)}" width="{i(w)}" height="{i(h)}">
  <Text align="CENTER" ellipsis="TRUE"><Font family="{FONT}" size="{size}" weight="{weight}" color="{colour}"><Template><![CDATA[%s]]><Parameter expression="{expr}"/></Template></Font></Text>
</PartText>"""


def image_part(resource, x, y, size, tint=None):
    tint_attr = f' tintColor="{tint}"' if tint else ""
    return f"""<PartImage x="{i(x)}" y="{i(y)}" width="{size}" height="{size}"{tint_attr}>
  <Image resource="{resource}"/>
</PartImage>"""


def ring_arcs(box, colour, fraction=None):
    """Grey track, plus a coloured arc filled to `fraction` (0..1) when given."""
    arc = (f'<Arc centerX="{GAUGE_R}" centerY="{GAUGE_R}" width="{2 * ARC_R}" height="{2 * ARC_R}" '
           f'startAngle="{ARC_START}" endAngle="{ARC_START + ARC_SWEEP}">')
    out = f"""<PartDraw x="0" y="0" width="{box}" height="{box}">
  <Variant mode="AMBIENT" target="alpha" value="90"/>
  {arc}
    <Stroke color="{TRACK}" thickness="{ARC_W}" cap="ROUND"/>
  </Arc>
</PartDraw>"""
    if fraction:
        out += f"""
<PartDraw x="0" y="0" width="{box}" height="{box}">
  <Variant mode="AMBIENT" target="alpha" value="150"/>
  {arc}
    <Stroke color="{colour}" thickness="{ARC_W}" cap="ROUND"/>
    <Transform target="endAngle" value="{ARC_START} + {ARC_SWEEP} * ({fraction})"/>
  </Arc>
</PartDraw>"""
    return out


def value_and_icon(box, colour, prefix):
    """Big [TEXT] in the middle and a small tinted icon above the ring's gap.
    Falls back to [TITLE] when a provider sends no text."""
    value = text_part("[COMPLICATION.TEXT]", 6, GAUGE_R - 26, box - 12, 46, 32)
    title = text_part("[COMPLICATION.TITLE]", 6, GAUGE_R - 26, box - 12, 46, 26)
    icon = image_part("[COMPLICATION.MONOCHROMATIC_IMAGE]", GAUGE_R - 12, GAUGE_R + 24, 24, colour)
    return f"""<Condition>
  <Expressions>
    <Expression name="{prefix}_text"><![CDATA[[COMPLICATION.TEXT] != null]]></Expression>
    <Expression name="{prefix}_title"><![CDATA[[COMPLICATION.TITLE] != null]]></Expression>
  </Expressions>
  <Compare expression="{prefix}_text">
{indent(value, 2)}
  </Compare>
  <Compare expression="{prefix}_title">
{indent(title, 2)}
  </Compare>
</Condition>
<Condition>
  <Expressions>
    <Expression name="{prefix}_icon"><![CDATA[[COMPLICATION.MONOCHROMATIC_IMAGE] != null]]></Expression>
  </Expressions>
  <Compare expression="{prefix}_icon">
{indent(icon, 2)}
  </Compare>
</Condition>"""


def ring_slot(slot_id, name, label, cx, colour, provider, provider_type):
    """A ring gauge that accepts any small complication.

    Ranged values and goal progress fill the ring; short text shows an empty
    ring; images sit in the middle of the dial."""
    box = 2 * GAUGE_R
    x0, y0 = cx - GAUGE_R, C - GAUGE_R
    back = f"""<PartDraw x="0" y="0" width="{box}" height="{box}">
  <Variant mode="AMBIENT" target="alpha" value="0"/>
  <Ellipse x="0" y="0" width="{box}" height="{box}"><Fill color="{DISC}"/></Ellipse>
</PartDraw>"""

    def block(ctype, *parts):
        body = "\n".join(indent(p, 1) for p in (back,) + parts)
        return f"""<Complication type="{ctype}">
{body}
</Complication>"""

    blocks = [
        block("RANGED_VALUE", ring_arcs(box, colour, RANGED_FRACTION),
              value_and_icon(box, colour, f"{name}_ranged")),
        block("GOAL_PROGRESS", ring_arcs(box, colour, GOAL_FRACTION),
              value_and_icon(box, colour, f"{name}_goal")),
        block("SHORT_TEXT", ring_arcs(box, colour),
              value_and_icon(box, colour, f"{name}_short")),
        block("MONOCHROMATIC_IMAGE", ring_arcs(box, colour),
              image_part("[COMPLICATION.MONOCHROMATIC_IMAGE]", GAUGE_R - 24, GAUGE_R - 24, 48, colour)),
        block("SMALL_IMAGE",
              image_part("[COMPLICATION.SMALL_IMAGE]", GAUGE_R - 36, GAUGE_R - 36, 72)),
        block("EMPTY", ring_arcs(box, colour)),
    ]
    return f"""<ComplicationSlot slotId="{slot_id}" name="{name}" displayName="{label}" x="{i(x0)}" y="{i(y0)}" width="{box}" height="{box}"
    supportedTypes="RANGED_VALUE GOAL_PROGRESS SHORT_TEXT MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY" isCustomizable="TRUE">
  <DefaultProviderPolicy defaultSystemProvider="{provider}" defaultSystemProviderType="{provider_type}"/>
  <BoundingOval x="0" y="0" width="{box}" height="{box}" outlinePadding="2"/>
{indent(chr(10).join(blocks), 1)}
</ComplicationSlot>"""


def date_dial():
    r = SUB_R
    dow = text_part("[DAY_OF_WEEK_S]", C - r, TOP_Y - 36, 2 * r, 30, 21, BLUE, "MEDIUM")
    day = text_part("[DAY]", C - r, TOP_Y - 8, 2 * r, 44, 36)
    return f"""{disc("date_disc", C, TOP_Y, r)}
{indent(dow, 2)}
{indent(day, 2)}"""


def bottom_complication():
    r = SUB_R
    d = 2 * r
    text = text_part("[COMPLICATION.TEXT]", 4, r - 4, d - 8, 38, 26, weight="MEDIUM")
    icon = image_part("[COMPLICATION.MONOCHROMATIC_IMAGE]", r - 14, r - 36, 28, SUN)
    return f"""{disc("bottom_disc", C, BOTTOM_Y, r)}
    <ComplicationSlot slotId="0" name="bottom" displayName="Bottom" x="{i(C - r)}" y="{i(BOTTOM_Y - r)}" width="{d}" height="{d}"
        supportedTypes="SHORT_TEXT MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY" isCustomizable="TRUE">
      <DefaultProviderPolicy defaultSystemProvider="SUNRISE_SUNSET" defaultSystemProviderType="SHORT_TEXT"/>
      <BoundingOval x="0" y="0" width="{d}" height="{d}" outlinePadding="2"/>
      <Complication type="SHORT_TEXT">
{indent(icon, 4)}
{indent(text, 4)}
      </Complication>
      <Complication type="MONOCHROMATIC_IMAGE">
{indent(image_part("[COMPLICATION.MONOCHROMATIC_IMAGE]", r - 24, r - 24, 48, WHITE), 4)}
      </Complication>
      <Complication type="SMALL_IMAGE">
{indent(image_part("[COMPLICATION.SMALL_IMAGE]", r - 32, r - 32, 64), 4)}
      </Complication>
      <Complication type="EMPTY">
      </Complication>
    </ComplicationSlot>"""


def hand(name, expr, y_tip, width, colour):
    return f"""  <Group name="{name}" x="0" y="0" width="{SIZE}" height="{SIZE}" pivotX="0.5" pivotY="0.5">
    <Transform target="angle" value="{expr}"/>
    <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}">
      <Line startX="{f(C)}" startY="{f(C)}" endX="{f(C)}" endY="{y_tip}"><Stroke color="{colour}" thickness="{width}" cap="ROUND"/></Line>
    </PartDraw>
  </Group>"""


def build():
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED by generate_watchface.py - edit that file, not this one. -->
<WatchFace width="{SIZE}" height="{SIZE}" clipShape="CIRCLE">
  <Metadata key="CLOCK_TYPE" value="ANALOG"/>
  <Metadata key="PREVIEW_TIME" value="10:08:30"/>
  <Scene backgroundColor="#000000">

    <!-- Minute track -->
    <PartDraw name="ticks" x="0" y="0" width="{SIZE}" height="{SIZE}">
      <Variant mode="AMBIENT" target="alpha" value="140"/>
{ticks()}
    </PartDraw>

    <!-- 1-12 -->
    <Group name="numerals" x="0" y="0" width="{SIZE}" height="{SIZE}">
      <Variant mode="AMBIENT" target="alpha" value="170"/>
{numerals()}
    </Group>

    <!-- Top: day + date -->
{date_dial()}

    <!-- Left ring: battery by default -->
{indent(ring_slot(1, "left", "Left ring", C - GAUGE_DX, BLUE, "WATCH_BATTERY", "RANGED_VALUE"), 2)}

    <!-- Right ring: steps by default -->
{indent(ring_slot(2, "right", "Right ring", C + GAUGE_DX, GREEN, "STEP_COUNT", "SHORT_TEXT"), 2)}

    <!-- Bottom: sunrise/sunset by default -->
{bottom_complication()}

    <!-- Hands -->
{indent(hand("hour_hand", "([HOUR_0_11] + [MINUTE] / 60) * 30", 126, 13, WHITE), 1)}
{indent(hand("minute_hand", "([MINUTE] + [SECOND] / 60) * 6", 50, 11, WHITE), 1)}
    <Group name="second_hand" x="0" y="0" width="{SIZE}" height="{SIZE}" pivotX="0.5" pivotY="0.5">
      <Transform target="angle" value="[SECOND] * 6"/>
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}">
        <Line startX="{f(C)}" startY="{i(C + 34)}" endX="{f(C)}" endY="16"><Stroke color="{RED}" thickness="3" cap="ROUND"/></Line>
        <Ellipse x="{f(C - 8)}" y="{f(C - 8)}" width="16" height="16"><Fill color="{RED}"/></Ellipse>
        <Ellipse x="{f(C - 2.5)}" y="{f(C - 2.5)}" width="5" height="5"><Fill color="#000000"/></Ellipse>
      </PartDraw>
    </Group>
  </Scene>
</WatchFace>
"""


if __name__ == "__main__":
    out = Path(__file__).parent / "app/src/main/res/raw/watchface.xml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build())
    print(f"wrote {out}")
