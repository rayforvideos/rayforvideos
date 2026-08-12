#!/usr/bin/env python3
"""Generate the animated GitHub profile header SVG, dark + light variants.

Typing is done by staggering `fill-opacity` on one <tspan> per character.
An earlier version animated a <clipPath> rect's width instead; Chromium
computes those values correctly but never repaints the clip, so the reveal
was invisible. Per-character opacity repaints fine and, unlike a clip wipe,
does not depend on the viewer's monospace metrics.

Timeline (10s loop): name types, tagline types, subtitle fades in,
everything holds, then fades out before the loop restarts.
"""
import pathlib

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
CYCLE = 10.0

NAME = "Ray"
TAGLINE = "frontend & devtools engineer in south korea 🇰🇷"
SUBTITLE = "i like making slow things fast and big things small."

NAME_START, NAME_STEP = 0.30, 0.16      # ends 0.78s
TAG_START, TAG_STEP = 1.20, 0.038       # 45 units -> ends 2.91s
CURSOR_IN = 2.98
SUB_IN, SUB_FULL = 3.25, 3.95

# Brand green sampled from the frog avatar (#B5D240 is its dominant fill),
# plus a cooler green to give the blobs and the sheen some depth.
FROG = "#B5D240"
LEAF = "#5FBF6A"

THEMES = {
    "dark": dict(bg="#0D1117", name="#E6EDF3", tag="#8B949E", sub="#6E7681",
                 blob_a=0.40, blob_b=0.34, blob_group=0.60,
                 ink=FROG),
    # the avatar green is too pale to read as a line or cursor on white,
    # so the light theme darkens it while the blobs keep the true hue
    "light": dict(bg="#FFFFFF", name="#0B0B0B", tag="#57606A", sub="#6E7781",
                  blob_a=0.26, blob_b=0.22, blob_group=0.80,
                  ink="#7E9A20"),
}


def esc(ch):
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(ch, ch)


def units(text):
    """Split into user-perceived characters, not codepoints.

    A flag emoji like 🇰🇷 is two regional-indicator codepoints; splitting it
    would render as the letters "KR". Variation selectors and ZWJ sequences
    are absorbed into the preceding unit for the same reason.
    """
    RI_LO, RI_HI = 0x1F1E6, 0x1F1FF
    out, i = [], 0
    while i < len(text):
        cluster = text[i]
        i += 1
        if RI_LO <= ord(cluster) <= RI_HI and i < len(text) and RI_LO <= ord(text[i]) <= RI_HI:
            cluster += text[i]
            i += 1
        while i < len(text) and text[i] in "️‍":
            cluster += text[i]
            i += 1
            if cluster.endswith("‍") and i < len(text):  # ZWJ joins the next unit
                cluster += text[i]
                i += 1
        out.append(cluster)
    return out


def typed(text, start, step):
    """One <tspan> per user-perceived character, each popping in at its moment.

    Emitted with no whitespace between tspans: the <text> element carries
    xml:space="preserve" so that literal spaces survive, which means any
    indentation would survive too.
    """
    parts = []
    for i, ch in enumerate(units(text)):
        at = round((start + i * step) / CYCLE, 5)
        parts.append(
            f'<tspan fill-opacity="0">{esc(ch)}'
            f'<animate attributeName="fill-opacity" values="0;1" keyTimes="0;{at}"'
            f' calcMode="discrete" dur="{CYCLE:g}s" repeatCount="indefinite"/>'
            f'</tspan>'
        )
    return "".join(parts)


TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 240" width="880" height="240" role="img" aria-label="{aria}">
  <defs>
    <radialGradient id="blobA" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{frog}" stop-opacity="{blob_a}"/>
      <stop offset="100%" stop-color="{frog}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="blobB" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{leaf}" stop-opacity="{blob_b}"/>
      <stop offset="100%" stop-color="{leaf}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{ink}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{ink}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{leaf}" stop-opacity="0"/>
      <animate attributeName="x1" values="-1;1" dur="6s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0;2" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <!-- static clip: keeps the drifting blobs inside the card's rounded corners -->
    <clipPath id="card">
      <rect width="880" height="240" rx="14"/>
    </clipPath>
  </defs>

  <rect width="880" height="240" rx="14" fill="{bg}"/>

  <!-- slow drifting colour blobs -->
  <g opacity="{blob_group}" clip-path="url(#card)">
    <circle r="85" fill="url(#blobA)" cx="150" cy="60">
      <animateTransform attributeName="transform" type="translate"
        values="0,0; 90,30; 30,-15; 0,0" dur="14s" repeatCount="indefinite"/>
    </circle>
    <circle r="95" fill="url(#blobB)" cx="740" cy="185">
      <animateTransform attributeName="transform" type="translate"
        values="0,0; -80,-35; -20,20; 0,0" dur="17s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- text: types in, holds, fades out before the loop restarts -->
  <g>
    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.90;0.95;1"
      dur="{cycle:g}s" repeatCount="indefinite"/>

    <text xml:space="preserve" font-family="{font}" x="440" y="100" text-anchor="middle" font-size="46" font-weight="700" fill="{name_fill}">{name_tspans}</text>

    <text xml:space="preserve" font-family="{font}" x="440" y="140" text-anchor="middle" font-size="17" fill="{tag_fill}">{tag_tspans}<tspan fill="{ink}" fill-opacity="0">_<animate attributeName="fill-opacity" values="0;1" keyTimes="0;{cursor_in}" calcMode="discrete" dur="{cycle:g}s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" calcMode="discrete" repeatCount="indefinite"/></tspan></text>

    <g>
      <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{sub_in};{sub_full};0.90;0.95;1"
        dur="{cycle:g}s" repeatCount="indefinite"/>
      <text font-family="{font}" x="440" y="186" text-anchor="middle" font-size="13.5" fill="{sub_fill}">{subtitle}</text>
    </g>
  </g>

  <rect x="140" y="212" width="600" height="2" fill="url(#rule)"/>
</svg>
"""

# screen-reader label, derived so it cannot drift from the visible text
ARIA = f"{NAME} - " + TAGLINE.replace("&", "and").replace(" 🇰🇷", "")

out = pathlib.Path(__file__).parent
for theme, c in THEMES.items():
    svg = TEMPLATE.format(
        aria=ARIA,
        frog=FROG, leaf=LEAF, ink=c["ink"], font=FONT, cycle=CYCLE,
        bg=c["bg"], name_fill=c["name"], tag_fill=c["tag"], sub_fill=c["sub"],
        blob_a=c["blob_a"], blob_b=c["blob_b"], blob_group=c["blob_group"],
        name_tspans=typed(NAME, NAME_START, NAME_STEP),
        tag_tspans=typed(TAGLINE, TAG_START, TAG_STEP),
        subtitle=SUBTITLE,
        cursor_in=round(CURSOR_IN / CYCLE, 5),
        sub_in=round(SUB_IN / CYCLE, 5),
        sub_full=round(SUB_FULL / CYCLE, 5),
    )
    (out / f"header-{theme}.svg").write_text(svg)
    print(f"wrote header-{theme}.svg ({len(svg)} bytes)")
