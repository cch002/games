#!/usr/bin/env python3
"""Generates app/src/main/res/raw/watchface.xml (Watch Face Format v2).

The face is drawn entirely with vector shapes, so there are no image assets to
maintain. Tweak the constants below and re-run:  python3 generate_watchface.py
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
BLUE = "#3DB2E8"          # battery + day-of-week
GREEN = "#2BD66B"         # steps
RED = "#E8322B"           # second hand
LOW_RED = "#FF5A4E"       # battery gauge when low
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


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def i(v):
    return str(int(round(v)))


def polar(r, deg):
    a = math.radians(deg)
    return C + r * math.sin(a), C - r * math.cos(a)


def ticks():
    out = []
    for i in range(60):
        hour = i % 5 == 0
        r0 = 203 if hour else 211
        x0, y0 = polar(r0, i * 6)
        x1, y1 = polar(222, i * 6)
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


def gauge(name, cx, colour, percent_expr, value_part, icon_part):
    """A ring gauge on a dark disc: track, progress arc, big value, small icon."""
    box = 2 * GAUGE_R
    x0, y0 = cx - GAUGE_R, C - GAUGE_R
    end = f"{ARC_START} + {ARC_SWEEP / 100:g} * clamp({percent_expr}, 0, 100)"
    return f"""  <Group name="{name}" x="{i(x0)}" y="{i(y0)}" width="{box}" height="{box}">
    <PartDraw x="0" y="0" width="{box}" height="{box}">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Ellipse x="0" y="0" width="{box}" height="{box}"><Fill color="{DISC}"/></Ellipse>
    </PartDraw>
    <PartDraw x="0" y="0" width="{box}" height="{box}">
      <Variant mode="AMBIENT" target="alpha" value="90"/>
      <Arc centerX="{GAUGE_R}" centerY="{GAUGE_R}" width="{2 * ARC_R}" height="{2 * ARC_R}" startAngle="{ARC_START}" endAngle="{ARC_START + ARC_SWEEP}">
        <Stroke color="{TRACK}" thickness="{ARC_W}" cap="ROUND"/>
      </Arc>
    </PartDraw>
    <PartDraw x="0" y="0" width="{box}" height="{box}">
      <Variant mode="AMBIENT" target="alpha" value="150"/>
      <Arc centerX="{GAUGE_R}" centerY="{GAUGE_R}" width="{2 * ARC_R}" height="{2 * ARC_R}" startAngle="{ARC_START}" endAngle="{ARC_START + ARC_SWEEP}">
        <Transform target="endAngle" value="{end}"/>
        <Stroke color="{colour}" thickness="{ARC_W}" cap="ROUND"/>
      </Arc>
    </PartDraw>
{value_part}
{icon_part}
  </Group>"""


def value_text(expr, size):
    box = 2 * GAUGE_R
    return f"""    <PartText x="6" y="{GAUGE_R - 28}" width="{box - 12}" height="48">
      <Text align="CENTER"><Font family="{FONT}" size="{size}" weight="BOLD" color="{WHITE}"><Template>%d<Parameter expression="{expr}"/></Template></Font></Text>
    </PartText>"""


def battery_icon(colour):
    # a small upright battery just above the gap in the ring
    x, y = GAUGE_R - 6, GAUGE_R + 26
    return f"""    <PartDraw name="battery_icon" x="{x}" y="{y}" width="12" height="22">
      <RoundRectangle x="3.5" y="0" width="5" height="3" cornerRadiusX="1" cornerRadiusY="1"><Fill color="{colour}"/></RoundRectangle>
      <RoundRectangle x="0" y="2.5" width="12" height="19" cornerRadiusX="2.5" cornerRadiusY="2.5"><Fill color="{colour}"/></RoundRectangle>
    </PartDraw>"""


def shoe_icon(colour):
    # a simple sneaker silhouette
    x, y = GAUGE_R - 12, GAUGE_R + 29
    return f"""    <PartDraw name="shoe_icon" x="{x}" y="{y}" width="24" height="18">
      <RoundRectangle x="2" y="0" width="9" height="12" cornerRadiusX="3" cornerRadiusY="3"><Fill color="{colour}"/></RoundRectangle>
      <RoundRectangle x="2" y="6" width="22" height="9" cornerRadiusX="4.5" cornerRadiusY="4.5"><Fill color="{colour}"/></RoundRectangle>
      <RoundRectangle x="0" y="14" width="24" height="3.5" cornerRadiusX="1.5" cornerRadiusY="1.5"><Fill color="{colour}"/></RoundRectangle>
    </PartDraw>"""


def battery_gauge():
    body = gauge("battery_gauge", C - GAUGE_DX, BLUE, "[BATTERY_PERCENT]",
                 value_text("[BATTERY_PERCENT]", 38), battery_icon(BLUE))
    # Swap the arc/icon colour to red when the battery is low.
    low = gauge("battery_gauge_low", C - GAUGE_DX, LOW_RED, "[BATTERY_PERCENT]",
                value_text("[BATTERY_PERCENT]", 38), battery_icon(LOW_RED))
    return f"""  <Condition>
    <Expressions>
      <Expression name="low">[BATTERY_PERCENT] &lt;= 15</Expression>
    </Expressions>
    <Compare expression="low">
{indent(low, 2)}
    </Compare>
    <Default>
{indent(body, 2)}
    </Default>
  </Condition>"""


def steps_gauge():
    return gauge("steps_gauge", C + GAUGE_DX, GREEN, "[STEP_PERCENT]",
                 value_text("[STEP_COUNT]", 30), shoe_icon(GREEN))


def date_dial():
    r = SUB_R
    return f"""{disc("date_disc", C, TOP_Y, r)}
    <PartText name="day_of_week" x="{i(C - r)}" y="{TOP_Y - 36}" width="{2 * r}" height="30">
      <Text align="CENTER"><Font family="{FONT}" size="21" weight="MEDIUM" color="{BLUE}"><Upper><Template>%s<Parameter expression="[DAY_OF_WEEK_S]"/></Template></Upper></Font></Text>
    </PartText>
    <PartText name="day_of_month" x="{i(C - r)}" y="{TOP_Y - 8}" width="{2 * r}" height="44">
      <Text align="CENTER"><Font family="{FONT}" size="36" weight="BOLD" color="{WHITE}"><Template>%d<Parameter expression="[DAY]"/></Template></Font></Text>
    </PartText>"""


def bottom_complication():
    r = SUB_R
    d = 2 * r
    text = f"""<PartText x="4" y="{r - 4}" width="{d - 8}" height="38">
            <Text align="CENTER" ellipsis="TRUE"><Font family="{FONT}" size="26" weight="MEDIUM" color="{WHITE}"><Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template></Font></Text>
          </PartText>"""
    return f"""{disc("bottom_disc", C, BOTTOM_Y, r)}
    <ComplicationSlot slotId="0" name="bottom" displayName="Bottom" x="{i(C - r)}" y="{i(BOTTOM_Y - r)}" width="{d}" height="{d}"
        supportedTypes="SHORT_TEXT MONOCHROMATIC_IMAGE SMALL_IMAGE" isCustomizable="TRUE">
      <DefaultProviderPolicy defaultSystemProvider="SUNRISE_SUNSET" defaultSystemProviderType="SHORT_TEXT"/>
      <BoundingOval x="0" y="0" width="{d}" height="{d}"/>
      <Complication type="SHORT_TEXT">
        <Group name="short_text" x="0" y="0" width="{d}" height="{d}">
          <PartImage x="{r - 14}" y="{r - 36}" width="28" height="28" tintColor="{SUN}">
            <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/>
          </PartImage>
          {text}
        </Group>
      </Complication>
      <Complication type="MONOCHROMATIC_IMAGE">
        <PartImage x="{r - 24}" y="{r - 24}" width="48" height="48" tintColor="{WHITE}">
          <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/>
        </PartImage>
      </Complication>
      <Complication type="SMALL_IMAGE">
        <PartImage x="{r - 32}" y="{r - 32}" width="64" height="64">
          <Image resource="[COMPLICATION.SMALL_IMAGE]"/>
        </PartImage>
      </Complication>
    </ComplicationSlot>"""


def hand(name, expr, y_tip, y_tail, width, colour, ambient_alpha=None):
    ambient = (f'\n    <Variant mode="AMBIENT" target="alpha" value="{ambient_alpha}"/>'
               if ambient_alpha is not None else "")
    return f"""  <Group name="{name}" x="0" y="0" width="{SIZE}" height="{SIZE}" pivotX="0.5" pivotY="0.5">
    <Transform target="angle" value="{expr}"/>{ambient}
    <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}">
      <Line startX="{f(C)}" startY="{y_tail}" endX="{f(C)}" endY="{y_tip}"><Stroke color="{colour}" thickness="{width}" cap="ROUND"/></Line>
    </PartDraw>
  </Group>"""


def indent(block, levels):
    pad = "  " * levels
    return "\n".join(pad + line if line else line for line in block.splitlines())


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

    <!-- Left: battery gauge -->
{indent(battery_gauge(), 1)}

    <!-- Right: steps gauge -->
{indent(steps_gauge(), 1)}

    <!-- Bottom: user-selectable complication (sunrise/sunset by default) -->
{bottom_complication()}

    <!-- Hands -->
{indent(hand("hour_hand", "([HOUR_0_11] + [MINUTE] / 60) * 30", 126, C, 13, WHITE), 1)}
{indent(hand("minute_hand", "([MINUTE] + [SECOND] / 60) * 6", 50, C, 11, WHITE), 1)}
    <Group name="second_hand" x="0" y="0" width="{SIZE}" height="{SIZE}" pivotX="0.5" pivotY="0.5">
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Transform target="angle" value="[SECOND] * 6"/>
      <PartDraw x="0" y="0" width="{SIZE}" height="{SIZE}">
        <Line startX="{f(C)}" startY="{C + 34}" endX="{f(C)}" endY="16"><Stroke color="{RED}" thickness="3" cap="ROUND"/></Line>
        <Ellipse x="{C - 8}" y="{C - 8}" width="16" height="16"><Fill color="{RED}"/></Ellipse>
        <Ellipse x="{C - 2.5}" y="{C - 2.5}" width="5" height="5"><Fill color="#000000"/></Ellipse>
      </PartDraw>
    </Group>
    <!-- Hub shown in ambient mode, when the second hand is hidden -->
    <PartDraw name="ambient_hub" x="{i(C - 7)}" y="{i(C - 7)}" width="14" height="14" alpha="0">
      <Variant mode="AMBIENT" target="alpha" value="255"/>
      <Ellipse x="0" y="0" width="14" height="14"><Fill color="{WHITE}"/></Ellipse>
    </PartDraw>
  </Scene>
</WatchFace>
"""


if __name__ == "__main__":
    out = Path(__file__).parent / "app/src/main/res/raw/watchface.xml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build())
    print(f"wrote {out}")
