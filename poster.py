"""Bharat Decode poster: 1080x1350 (4:5).
Upar photo -> white fade -> navy headline -> navy quote box -> #Bharatdecode, logo top-right."""
import io
import os

from PIL import Image, ImageDraw, ImageFont

try:
    import cv2
    import numpy as np
except Exception:  # opencv na ho to bhi poster ban jaye
    cv2 = None

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


FACE_TARGET_Y = 300   # photo mein chehre ka center is height par rakhna hai


def _faces(im):
    """Photo mein chehre dhundo. [(x, y, w, h), ...] original pixels mein."""
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
    """Photo ko w x h mein fit karo, chehra frame mein rakhke.
    (cropped_image, (face_x, face_y) ya None) return karta hai."""
    scale = max(w / im.width, h / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    foc = _focus(im, w, h)
    im = im.resize((nw, nh), Image.LANCZOS)
    face_xy = None
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
    if foc:
        face_xy = (fx - left, fy - top)
    return im.crop((left, top, left + w, top + h)), face_xy


def _square_on_face(im):
    """Inset ke liye chehre ke aas-paas ka square crop."""
    faces = _faces(im)
    if faces:
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        cx, cy, side = x + w / 2, y + h / 2, max(w, h) * 2.4
    else:
        cx, cy, side = im.width / 2, im.height * 0.38, min(im.size)
    side = min(side, min(im.size))
    left = max(0, min(cx - side / 2, im.width - side))
    top = max(0, min(cy - side / 2, im.height - side))
    return im.crop((round(left), round(top), round(left + side), round(top + side)))


def _logo(width=120):
    lg = Image.open(LOGO).convert("RGBA")
    bbox = lg.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        lg = lg.crop(bbox)
    return lg.resize((width, round(lg.height * width / lg.width)), Image.LANCZOS)


def make_poster(photo: Image.Image, headline: str, quote_line: str) -> bytes:
    canvas = Image.new("RGB", (W, H), WHITE)
    canvas.paste(_cover(photo, W, PHOTO_H)[0], (0, 0))

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


# ---------------- Design 2: bada quote + attribution + inset photo ----------------
QPHOTO_H = 1010
QFADE_START = 600
DARK = (8, 20, 44)
ORANGE = (255, 112, 0)
INSET_D = 330


def _circle(im, d, ring=9):
    ss = 4
    im = _square_on_face(im).resize((d * ss, d * ss), Image.LANCZOS)
    mask = Image.new("L", (d * ss, d * ss), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d * ss - 1, d * ss - 1], fill=255)
    out = Image.new("RGBA", (d + 2 * ring, d + 2 * ring), (0, 0, 0, 0))
    big = Image.new("RGBA", (out.width * ss, out.height * ss), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse([0, 0, big.width - 1, big.height - 1], fill=(255, 255, 255, 255))
    big.paste(im, (ring * ss, ring * ss), mask)
    return big.resize(out.size, Image.LANCZOS)


def make_poster_quote(photo, quote, attribution, inset=None):
    """Design 2. quote = bada headline, attribution = neeche orange line,
    inset = jis par bayan hai uski photo (PIL image) ya None."""
    canvas = Image.new("RGB", (W, H), DARK)
    crop, face_xy = _cover(photo, W, QPHOTO_H, target_y=340)
    canvas.paste(crop, (0, 0))

    fade = Image.new("L", (W, QPHOTO_H), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(QFADE_START, QPHOTO_H):
        t = (y - QFADE_START) / (QPHOTO_H - QFADE_START)
        fd.line([(0, y), (W, y)], fill=round(255 * (t ** 1.15)))
    canvas.paste(Image.new("RGB", (W, QPHOTO_H), DARK), (0, 0), fade)

    # inset gol photo: chehre ke opposite side
    if inset is not None:
        circ = _circle(inset, INSET_D)
        on_right = not (face_xy and face_xy[0] > W * 0.55)
        x = W - circ.width - 48 if on_right else 48
        canvas.paste(circ, (x, 575), circ)

    d = ImageDraw.Draw(canvas)
    # quote headline (max 3 lines, white, bold)
    qf, ql, qs = _fit(FONT_BOLD, quote.strip(), W - 140, 3,
                      [70, 66, 62, 58, 54, 50, 46])
    lh = round(qs * 1.3)
    top, bot = 975, 1235
    y = top + (bot - top - lh * len(ql)) / 2 + lh / 2
    for ln in ql:
        d.text((W / 2, y), ln, font=qf, fill=WHITE, anchor="mm")
        y += lh

    # attribution line
    af, al, _ = _fit(FONT_SEMI, "- " + attribution.strip(), W - 120, 1,
                     [44, 41, 38, 35, 32, 29])
    d.text((W / 2, 1262), al[0], font=af, fill=ORANGE, anchor="mm")

    # footer strip + logo
    d.rectangle([0, 1302, W, H], fill=ORANGE)
    d.text((W / 2, 1326), "#Bharatdecode  |  Truth Beyond Headlines",
           font=_font(FONT_SEMI, 27), fill=WHITE, anchor="mm")
    lg = _logo(120)
    canvas.paste(lg, (W - lg.width - 28, 26), lg)

    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=93, subsampling=0)
    return buf.getvalue()
