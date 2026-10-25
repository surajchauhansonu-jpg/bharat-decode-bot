"""Bharat Decode poster: 1080x1350 (4:5).
Upar photo -> white fade -> navy headline -> navy quote box -> #Bharatdecode, logo top-right."""
import io
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONT_BOLD = os.path.join(BASE, "assets/fonts/Hind-Bold.ttf")
FONT_SEMI = os.path.join(BASE, "assets/fonts/Hind-SemiBold.ttf")
FONT_REG = os.path.join(BASE, "assets/fonts/Hind-Regular.ttf")
LOGO = os.path.join(BASE, "assets/logo.png")

W, H = 1080, 1350
PHOTO_H = 900
FADE_START = 560
NAVY = (11, 30, 60)
WHITE = (255, 255, 255)
TAG_COLOR = (45, 55, 80)

BOX_X0, BOX_X1 = 104, 976
BOX_Y0, BOX_H = 1150, 146


def _font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def _wrap(text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # 2 line ho to balance karo (dono line lagbhag barabar)
    if len(lines) == 2 and len(words) > 2:
        best, best_w = lines, max(font.getlength(l) for l in lines)
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            mw = max(font.getlength(a), font.getlength(b))
            if mw <= max_w and mw < best_w:
                best, best_w = [a, b], mw
        lines = best
    return lines


def _fit(path, text, max_w, max_lines, sizes):
    for s in sizes:
        f = _font(path, s)
        lines = _wrap(text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines, s
    f = _font(path, sizes[-1])
    lines = _wrap(text, f, max_w)[:max_lines]
    lines[-1] = lines[-1].rstrip() + "…"
    return f, lines, sizes[-1]


def _cover(im, w, h, focus_y=0.3):
    scale = max(w / im.width, h / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = round((nh - h) * focus_y)
    return im.crop((left, top, left + w, top + h))


def _logo(width=120):
    lg = Image.open(LOGO).convert("RGBA")
    bbox = lg.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        lg = lg.crop(bbox)
    return lg.resize((width, round(lg.height * width / lg.width)), Image.LANCZOS)


def make_poster(photo: Image.Image, headline: str, quote_line: str) -> bytes:
    canvas = Image.new("RGB", (W, H), WHITE)
    canvas.paste(_cover(photo, W, PHOTO_H), (0, 0))

    # white fade (photo neeche white mein ghul jaati hai)
    fade = Image.new("L", (W, PHOTO_H), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(FADE_START, PHOTO_H):
        t = (y - FADE_START) / (PHOTO_H - FADE_START)
        fd.line([(0, y), (W, y)], fill=round(255 * (t ** 1.4)))
    canvas.paste(Image.new("RGB", (W, PHOTO_H), WHITE), (0, 0), fade)

    d = ImageDraw.Draw(canvas)

    # headline (max 2 lines, navy, bold, center)
    hf, hl, hs = _fit(FONT_BOLD, headline.strip(), W - 150, 2,
                      [96, 90, 84, 78, 72, 66, 60, 54])
    line_h = round(hs * 1.28)
    area_top, area_bot = 905, 1135
    block_h = line_h * len(hl)
    y = area_top + (area_bot - area_top - block_h) / 2 + line_h / 2
    for ln in hl:
        d.text((W / 2, y), ln, font=hf, fill=NAVY, anchor="mm")
        y += line_h

    # quote box
    d.rectangle([BOX_X0, BOX_Y0, BOX_X1, BOX_Y0 + BOX_H], fill=NAVY)
    qf, ql, qs = _fit(FONT_SEMI, quote_line.strip(), BOX_X1 - BOX_X0 - 56, 2,
                      [46, 43, 40, 37, 34, 31])
    q_lh = round(qs * 1.3)
    y = BOX_Y0 + BOX_H / 2 - q_lh * (len(ql) - 1) / 2
    for ln in ql:
        d.text(((BOX_X0 + BOX_X1) / 2, y), ln, font=qf, fill=WHITE, anchor="mm")
        y += q_lh

    # hashtag + logo
    d.text((34, 1322), "#Bharatdecode", font=_font(FONT_REG, 27), fill=TAG_COLOR,
           anchor="lm")
    lg = _logo(120)
    canvas.paste(lg, (W - lg.width - 28, 26), lg)

    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=93, subsampling=0)
    return buf.getvalue()
