"""Bharat Decode poster: 1080x1350 (4:5).
Upar photo -> white fade -> navy headline -> navy box -> #Bharatdecode, logo top-right.
Font: Anek Devanagari."""
import io
import os

from PIL import Image, ImageDraw, ImageFont

try:
    import cv2
    import numpy as np
except Exception:  # opencv na ho to bhi poster ban jaye
    cv2 = None

BASE = os.path.dirname(os.path.abspath(__file__))
_ANEK = os.path.join(BASE, "assets/fonts/AnekDevanagari.ttf")
_HIND = os.path.join(BASE, "assets/fonts/Hind-Bold.ttf")
FONT = _ANEK if os.path.exists(_ANEK) else _HIND
VARIABLE = FONT == _ANEK
LOGO = os.path.join(BASE, "assets/logo.png")

W, H = 1080, 1350
PHOTO_H = 900
FADE_START = 560
NAVY = (11, 30, 60)
WHITE = (255, 255, 255)
TAG_COLOR = (45, 55, 80)

BOX_X0, BOX_X1 = 104, 976
BOX_Y0, BOX_H = 1150, 146
FACE_TARGET_Y = 300   # photo mein chehre ka center is height par rakhna hai


def _font(size, weight=700):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    if VARIABLE:
        try:
            f.set_variation_by_axes([weight, 100])  # [Weight, Width]
        except Exception as ex:
            print("font weight set fail:", ex)
    return f


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


def _fit(text, max_w, max_lines, sizes, weight):
    for s in sizes:
        f = _font(s, weight)
        lines = _wrap(text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines, s
    f = _font(sizes[-1], weight)
    lines = _wrap(text, f, max_w)[:max_lines]
    lines[-1] = lines[-1].rstrip() + "…"
    return f, lines, sizes[-1]


def _faces(im):
    """Photo mein chehra dhundo. [(x, y, w, h), ...] original pixels mein."""
    if cv2 is None:
        return []
    try:
        gray = np.array(im.convert("L"))
        sc = 800 / max(gray.shape) if max(gray.shape) > 800 else 1.0
        if sc != 1.0:
            gray = cv2.resize(gray, (int(gray.shape[1] * sc), int(gray.shape[0] * sc)))
        gray = cv2.equalizeHist(gray)
        min_side = max(24, int(min(gray.shape) * 0.07))
        for name in ("haarcascade_frontalface_default.xml",
                     "haarcascade_frontalface_alt2.xml",
                     "haarcascade_profileface.xml"):
            casc = cv2.CascadeClassifier(cv2.data.haarcascades + name)
            rects = casc.detectMultiScale(gray, 1.1, 5, minSize=(min_side, min_side))
            if len(rects):
                return [(x / sc, y / sc, w / sc, h / sc) for x, y, w, h in rects]
    except Exception as ex:
        print("face detect fail:", ex)
    return []


def _focus(im, w, h):
    """(cx, cy, face_h) ya None. Do-teen bade chehre ek saath hon to unka beech."""
    faces = _faces(im)
    if not faces:
        return None
    faces.sort(key=lambda f: f[2] * f[3], reverse=True)
    big = faces[0]
    group = [f for f in faces if f[2] * f[3] >= 0.4 * big[2] * big[3]][:3]
    x0 = min(f[0] for f in group)
    x1 = max(f[0] + f[2] for f in group)
    y0 = min(f[1] for f in group)
    y1 = max(f[1] + f[3] for f in group)
    scale = max(w / im.width, h / im.height)
    if (x1 - x0) * scale > w * 0.9:  # saare chehre ek frame mein nahi aate
        x0, x1, y0, y1 = big[0], big[0] + big[2], big[1], big[1] + big[3]
    return (x0 + x1) / 2, (y0 + y1) / 2, y1 - y0


def _cover(im, w, h, target_y=FACE_TARGET_Y):
    """Photo ko w x h mein fit karo, chehra frame mein rakhke."""
    scale = max(w / im.width, h / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    foc = _focus(im, w, h)
    im = im.resize((nw, nh), Image.LANCZOS)
    if foc:
        fx, fy, fh = foc[0] * scale, foc[1] * scale, foc[2] * scale
        left = round(fx - w / 2)
        top = round(fy - min(target_y, max(fh * 0.9, 240)))
        print(f"  chehra mila: center=({fx:.0f},{fy:.0f}) height={fh:.0f}")
    else:
        left = (nw - w) // 2
        top = round((nh - h) * 0.12)
        print("  chehra nahi mila, upar se crop")
    left = max(0, min(left, nw - w))
    top = max(0, min(top, nh - h))
    return im.crop((left, top, left + w, top + h))


def _logo(width=120):
    lg = Image.open(LOGO).convert("RGBA")
    bbox = lg.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        lg = lg.crop(bbox)
    return lg.resize((width, round(lg.height * width / lg.width)), Image.LANCZOS)


def make_poster(photo: Image.Image, headline: str, box_line: str) -> bytes:
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

    # headline (max 2 lines, navy, extra-bold, center)
    hf, hl, hs = _fit(headline.strip(), W - 150, 2,
                      [96, 90, 84, 78, 72, 66, 60, 56, 52], 800)
    line_h = round(hs * 1.22)
    area_top, area_bot = 905, 1135
    y = area_top + (area_bot - area_top - line_h * len(hl)) / 2 + line_h / 2
    for ln in hl:
        d.text((W / 2, y), ln, font=hf, fill=NAVY, anchor="mm")
        y += line_h

    # navy box
    d.rectangle([BOX_X0, BOX_Y0, BOX_X1, BOX_Y0 + BOX_H], fill=NAVY)
    qf, ql, qs = _fit(box_line.strip(), BOX_X1 - BOX_X0 - 56, 2,
                      [46, 43, 40, 37, 34, 31], 600)
    q_lh = round(qs * 1.28)
    y = BOX_Y0 + BOX_H / 2 - q_lh * (len(ql) - 1) / 2
    for ln in ql:
        d.text(((BOX_X0 + BOX_X1) / 2, y), ln, font=qf, fill=WHITE, anchor="mm")
        y += q_lh

    # hashtag + logo
    d.text((34, 1322), "#Bharatdecode", font=_font(27, 500), fill=TAG_COLOR,
           anchor="lm")
    lg = _logo(120)
    canvas.paste(lg, (W - lg.width - 28, 26), lg)

    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=93, subsampling=0)
    return buf.getvalue()
