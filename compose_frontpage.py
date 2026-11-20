#!/usr/bin/env python3
"""Compose the front page for the Friday 20 November 2026 edition.

The sheet is drawn with Pillow on a 1024x1024 canvas: a masthead, a lead
story with a photograph, two further illustrated stories, two text stories
in columns and a briefs strip along the bottom.  Running this file writes
``entry.png`` next to it; ``main.py`` is the program the grader runs and
it ships that PNG to the output directory after verifying it.
"""

import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

SIDE = 1024                 # the canvas is square, SIDE x SIDE pixels
EDGE = 34                   # outer margin of the sheet
PAPER = (246, 241, 230)     # warm newsprint
INK = (22, 22, 26)          # near-black ink
FAINT = (96, 90, 80)        # grey-brown for captions and furniture
ACCENT = (122, 28, 28)      # oxblood red for kickers

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_font(path, size):
    return ImageFont.truetype(path, size)


def wrapped(draw, text, font, width):
    """Split ``text`` into lines that fit ``width`` pixels.

    Wrapping is measured against the real font instead of counting
    characters, so narrow and wide letters are treated honestly.
    """
    lines = []
    for word in text.split():
        trial = word if not lines else lines[-1] + " " + word
        if lines and draw.textlength(trial, font=font) > width:
            lines.append(word)
        elif lines:
            lines[-1] = trial
        else:
            lines.append(word)
    return lines


def paste_cover(canvas, path, box):
    """Paste the photo at ``path`` so it covers ``box`` (x, y, w, h).

    The photo is centre-cropped to the box's aspect ratio first, the way
    a picture desk crops wire photos to the hole on the page.
    """
    x, y, w, h = box
    photo = Image.open(path).convert("RGB")
    target = w / h
    pw, ph = photo.size
    if pw / ph > target:            # too wide: trim the sides
        crop = int(ph * target)
        left = (pw - crop) // 2
        photo = photo.crop((left, 0, left + crop, ph))
    else:                           # too tall: trim top and bottom
        crop = int(pw / target)
        top = (ph - crop) // 2
        photo = photo.crop((0, top, pw, top + crop))
    canvas.paste(photo.resize((w, h), Image.LANCZOS), (x, y))


class FrontPage:
    """A one-page newspaper being assembled top to bottom."""

    def __init__(self):
        self.img = Image.new("RGB", (SIDE, SIDE), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self.y = EDGE               # cursor: next free row of pixels

    # -- page furniture ------------------------------------------------
    def thick_rule(self, gap_before=6, gap_after=10):
        self.y += gap_before
        self.d.rectangle([EDGE, self.y, SIDE - EDGE, self.y + 3], fill=INK)
        self.y += 3 + gap_after

    def thin_rule(self, gap_before=4, gap_after=6):
        self.y += gap_before
        self.d.line([EDGE, self.y, SIDE - EDGE, self.y], fill=INK, width=1)
        self.y += 1 + gap_after

    def banner(self):
        d = self.d
        small = load_font(SANS, 17)
        d.text((EDGE, self.y), "VOL. I — No. 21", font=small, fill=FAINT)
        centre = "FRIDAY, 20 NOVEMBER 2026"
        w = d.textlength(centre, font=small)
        d.text(((SIDE - w) / 2, self.y), centre, font=small, fill=FAINT)
        late = "LATE EDITION"
        w = d.textlength(late, font=small)
        d.text((SIDE - EDGE - w, self.y), late, font=small, fill=FAINT)
        self.y += 26
        name_font = load_font(SERIF_BOLD, 74)
        name = "The World Ledger"
        w = d.textlength(name, font=name_font)
        d.text(((SIDE - w) / 2, self.y), name, font=name_font, fill=INK)
        self.y += 84
        strap = load_font(SANS_BOLD, 19)
        line = "THE WORLD'S NEWS OF ONE DAY, SET ON ONE PAGE"
        w = d.textlength(line, font=strap)
        d.text(((SIDE - w) / 2, self.y), line, font=strap, fill=ACCENT)
        self.y += 24
        self.thick_rule()

    # -- story pieces --------------------------------------------------
    def kicker(self, x, text, width):
        f = load_font(SANS_BOLD, 18)
        self.d.text((x, self.y), text.upper(), font=f, fill=ACCENT)
        return 24

    def headline(self, x, text, width, size):
        f = load_font(SERIF_BOLD, size)
        used = 0
        for line in wrapped(self.d, text, f, width):
            self.d.text((x, self.y + used), line, font=f, fill=INK)
            used += int(size * 1.12)
        return used

    def deck(self, x, text, width, size=21):
        f = load_font(SERIF, size)
        used = 0
        for line in wrapped(self.d, text, f, width):
            self.d.text((x, self.y + used), line, font=f, fill=INK)
            used += int(size * 1.34)
        return used

    def caption(self, x, text, width):
        f = load_font(SANS, 15)
        used = 0
        for line in wrapped(self.d, text, f, width):
            self.d.text((x, self.y + used), line, font=f, fill=FAINT)
            used += 20
        return used

    def photo_block(self, x, path, w, h, caption_text):
        """A photograph with its caption, drawn at the cursor row."""
        top = self.y
        paste_cover(self.img, path, (x, top, w, h))
        self.y = top + h + 4
        used = self.caption(x, caption_text, w)
        self.y = top
        return h + 4 + used

    def lead(self, story):
        """The lead: words on the left, the picture on the right."""
        top = self.y
        text_w = 548
        self.y += self.kicker(EDGE, story["kicker"], text_w)
        self.y += self.headline(EDGE, story["headline"], text_w, 36)
        self.y += 4
        byline = load_font(SANS, 16)
        self.d.text((EDGE, self.y), story["byline"], font=byline, fill=FAINT)
        self.y += 24
        left_h = (self.y - top) + self.deck(EDGE, story["deck"], text_w, 19)
        photo_x = EDGE + text_w + 26
        photo_w = SIDE - EDGE - photo_x
        self.y = top
        right_h = self.photo_block(
            photo_x, story["photo"], photo_w, 200, story["caption"])
        self.y = top + max(left_h, right_h)

    def illustrated_row(self, story):
        """A story whose photograph sits on the left of its words."""
        top = self.y
        photo_w = 428
        left_h = self.photo_block(
            EDGE, story["photo"], photo_w, 140, story["caption"])
        x = EDGE + photo_w + 24
        text_w = SIDE - EDGE - x
        self.y = top
        self.y += self.kicker(x, story["kicker"], text_w)
        self.y += self.headline(x, story["headline"], text_w, 30)
        self.y += 2
        right_h = self.deck(x, story["deck"], text_w, 19) + (self.y - top)
        self.y = top + max(left_h, right_h)

    def text_story(self, x, story, width):
        top = self.y
        self.y += self.kicker(x, story["kicker"], width)
        self.y += self.headline(x, story["headline"], width, 21)
        self.y += 2
        used = self.deck(x, story["deck"], width, 16) + (self.y - top)
        self.y = top
        return used


LEAD = {
    "kicker": "Washington — The Iran War",
    "headline": "Trump Puts Iran Decision Off Until the New Year",
    "byline": "By the Ledger Wire — Washington",
    "deck": (
        "President Trump told Axios he will not decide the next step in "
        "the Iran war until the new year. The Senate then voted 51 to 48 "
        "to block a measure ordering him to end the war or win "
        "Congress's approval to fight it."
    ),
    "photo": os.path.join(ASSETS, "senate.jpg"),
    "caption": "The Senate chamber, which voted 51–48 on the war measure.",
}

KYIV = {
    "kicker": "Kyiv — Russia-Ukraine War",
    "headline": "Strikes on Kyiv's Bridges Kill Eight",
    "deck": (
        "Missiles and drones struck bridges across the capital overnight, "
        "Mayor Vitali Klitschko said; 28 people were injured across "
        "nine regions."
    ),
    "photo": os.path.join(ASSETS, "kyiv.jpg"),
    "caption": "Dawn over the Dnipro after the overnight strikes on Kyiv.",
}

SHENZHEN = {
    "kicker": "Shenzhen — Diplomacy",
    "headline": "Trump, Putin and Xi: Nuclear War “Must Never Be Fought”",
    "deck": (
        "A joint statement after the Shenzhen meeting renews the pledge "
        "that a nuclear war cannot be won — but brings no breakthrough "
        "on Ukraine."
    ),
}

PACIFIC = {
    "kicker": "The Pacific — Climate",
    "headline": "U.S. Leases 31.5 Million Acres of Seabed for Mining",
    "deck": (
        "The Marine Minerals Administration leased the tract to Wetstone "
        "U.S. Ventures for $6 million — the first sale of its kind, in a "
        "new race for seabed metals."
    ),
}

KENYA = {
    "kicker": "Nairobi — Health",
    "headline": "Kenya's Last Ebola Patient Goes Home",
    "deck": (
        "Thirty-seven days after the first case, the last patient was "
        "discharged. The outbreak is over."
    ),
    "photo": os.path.join(ASSETS, "kenya.jpg"),
    "caption": "Applause as the last patient is discharged.",
}

BRIEFS = [
    "WARSAW — Russian missiles and a drone violated Poland's airspace overnight, Warsaw says.",
    "ROME — Italy fines Meta €805 million over its access to Android users' photos.",
    "NEW YORK — Grand Theft Auto VI tops $2.3 billion in sales on its launch day.",
    "TALLINN — Estonia shuts its Russian border for six months; Moscow cries “new Iron Curtain.”",
]


def bottom_row(page):
    """Three columns: two text stories and the Kenya picture story."""
    top = page.y
    col_w = 296
    gap = 34
    h1 = page.text_story(EDGE, SHENZHEN, col_w)
    x2 = EDGE + col_w + gap
    h2 = page.text_story(x2, PACIFIC, col_w)
    x3 = x2 + col_w + gap
    page.y = top
    photo_h = page.photo_block(x3, KENYA["photo"], col_w, 82, KENYA["caption"])
    page.y = top + photo_h + 4
    h3 = page.kicker(x3, KENYA["kicker"], col_w)
    page.y += h3
    head_h = page.headline(x3, KENYA["headline"], col_w, 21)
    page.y += head_h
    h3 += head_h
    page.y += 2
    h3 += page.deck(x3, KENYA["deck"], col_w, 16)
    page.y = top + max(h1, h2, photo_h + 4 + h3)


def briefs_strip(page):
    """The IN BRIEF strip: six one-line stories in two columns."""
    page.thin_rule(gap_before=2, gap_after=6)
    head = load_font(SANS_BOLD, 19)
    page.d.text((EDGE, page.y), "IN BRIEF", font=head, fill=INK)
    page.y += 25
    body = load_font(SANS, 15)
    col_w = 462
    xs = [EDGE, EDGE + col_w + 32]
    pitch = 40                      # two lines at 18 px, plus air
    for i, item in enumerate(BRIEFS):
        x = xs[i % 2]
        lines = wrapped(page.d, item, body, col_w)
        y0 = page.y + (i // 2) * pitch
        for j, line in enumerate(lines):
            page.d.text((x, y0 + j * 18), line, font=body, fill=INK)
    page.y += ((len(BRIEFS) + 1) // 2) * pitch


def footer(page):
    page.thin_rule(gap_before=0, gap_after=6)
    f = load_font(SANS, 14)
    left = "Sources: Just Security · One Turn News · Bangladesh Chronicle"
    page.d.text((EDGE, page.y), left, font=f, fill=FAINT)
    right = "Set by an AI compositor — Fri 20 Nov 2026"
    w = page.d.textlength(right, font=f)
    page.d.text((SIDE - EDGE - w, page.y), right, font=f, fill=FAINT)


def build():
    page = FrontPage()
    page.banner()
    page.lead(LEAD)
    page.thin_rule()
    page.illustrated_row(KYIV)
    page.thin_rule()
    bottom_row(page)
    briefs_strip(page)
    footer(page)
    out = os.path.join(HERE, "entry.png")
    page.img.save(out, optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes; cursor ended at", page.y)


if __name__ == "__main__":
    build()
