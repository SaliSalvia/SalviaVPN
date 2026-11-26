successfully downloaded text file (SHA: 35e4e452a0dd07e4bb6bafe87f09b0df49b65506)successfully downloaded text file (SHA: a7766a60d335b38e3be90d8d5d25f859ffeb2492)successfully downloaded text file (SHA: e14c481b54bbade29b40032805078921593dc47a)"""Makes every icon of the program from its artwork: the raster that
docs/images/logo.png carries (source_art()). The tray keeps its own chip,
which it draws itself (symbol()): a square chip with three pins on each
side, and on its face a four-point star with two companion dots, the
constellation of its nebula.
The tile under it is the logo's nebula: a deep indigo sky with violet, pink,
and cyan glows and a scatter of stars. From it:

- Android (android/app/src/main/res): an adaptive icon for Android 8+, the
  nebula as the background layer and the symbol as the foreground layer,
  108 dp each, which the launcher crops to its own shape; and
  ic_launcher.png for older Android, the same tile, rounded. The status bar
  icon (res/drawable/ic_stat_logo.xml) is the symbol in white, by hand. The
  Android TV banner (res/drawable-xhdpi/banner.png, 320 x 180 px): the
  symbol and the name in white on the night theme's indigo.
- Windows (windows/runner/resources/app_icon.ico): the tile, in every size
  Explorer and the taskbar use; the small sizes sharpened, since the
  taskbar shows 24 or 32 px.
- The core (core/internal/desktop): appicon.ico, the same for its
  executable (tools/winres).
- The web dashboard (core/internal/service/web/icon.png): the tile, for
  the page icon and the logo.
- The app's logo (assets/logo.png): the tile, beside its name.
- The tray icons: the symbol on a dark tile, plain while off; while
  connecting, the pins of one side after the other are filled (four
  frames); otherwise a dot of the state's color sits at the chip's bottom
  right corner. The app's tray (assets/tray: .ico for Windows, .png for
  Linux): off, busy1 to busy4, on and idle (green), error (red). The core's
  tray (core/internal/desktop/tray: .ico for Windows, .png elsewhere): one
  icon per state, green while the proxy runs, blue while Windows' system
  proxy points at it, faded while asleep, red on an error; the first frame
  while waiting.

The documentation's wordmark is docs/images/wordmark.png: the artwork with
the name in the nebula's colors beside it, made by wordmark().

Run from app/ after changing the symbol or the colors (needs Pillow):

    python tool/app_icons.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..')
CORE = os.path.join(APP, '..', 'core')
RES = os.path.join(APP, 'android', 'app', 'src', 'main', 'res')
SOURCE = os.path.join(APP, '..', 'docs', 'images', 'logo.png')

# The symbol's height as a share of the 108 dp canvas. Launchers show about
# the middle 72 dp (67%), so 0.46 makes it about 70% of the tile.
ART = 0.46
DENSITY = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
WINDOWS_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]

# The nebula of the SalviaVPN logo: a deep indigo sky, its violet, pink,
# and cyan clouds, and the lavender of its chrome.
NIGHT_TOP = (0x24, 0x1B, 0x6E)
NIGHT_MID = (0x17, 0x10, 0x57)
NIGHT_BOTTOM = (0x0C, 0x0A, 0x3E)
VIOLET = (0x6B, 0x3C, 0xC9)
PINK = (0xE5, 0x69, 0xF6)
CYAN = (0x23, 0x82, 0xE4)
LAVENDER = (0xB9, 0xA6, 0xFF)
WHITE = (255, 255, 255, 255)

ADAPTIVE = '''<?xml version="1.0" encoding="utf-8"?>
<!-- The launcher icon on Android 8+: the symbol over the nebula;
     the launcher crops both layers to its own shape. Made by
     tool/app_icons.py. -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
'''


# The symbol in a 24 grid: a square chip (CHIP) with three pins on each
# side at PIN_OFF from the side's middle, and on its face a four-point
# star (STAR), the sparkle of the logo. The tray shows the state as a dot
# of DOT radius inside the chip's bottom right corner, with a gap of
# DOT_GAP around it; while connecting, a white dot of light travels
# around the chip's four sides (side indexes: 0 bottom, 1 left, 2 top,
# 3 right), riding the middle pin of one side at a time.
CHIP = (6.0, 6.0, 18.0, 18.0)
PIN_OFF = (-2.9, 0.0, 2.9)
PIN_LEN, PIN_W = 2.0, 1.2
CHIP_STROKE, CHIP_RADIUS = 1.5, 1.8
STAR, STAR_IN = 3.8, 1.5
DOT, DOT_GAP = 1.3, 0.3


def source_art(size):
    """The program's artwork, docs/images/logo.png, centered to a square
    where it is not one already, on a size px RGBA canvas. Every icon but
    the tray's comes from it."""
    with Image.open(SOURCE) as img:
        art = img.convert('RGBA')
    side = min(art.width, art.height)
    left = (art.width - side) // 2
    top = (art.height - side) // 2
    art = art.crop((left, top, left + side, top + side))
    return art.resize((size, size), Image.LANCZOS)


def star_points(cx, cy, r, inner, rays=4):
    """The outline of a `rays`-pointed sparkle: `inner` is the radius of
    the valleys between the points."""
    pts = []
    for i in range(rays * 2):
        ang = math.pi * i / rays - math.pi / 2
        rr = inner if i % 2 else r
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def symbol(size):
    """The symbol, white on transparent, on a size px square for the 24
    grid. Drawn at 4x."""
    k = 4
    s = size * k / 24
    img = Image.new('RGBA', (size * k, size * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # The pins: three on each side, from the chip's edge outward.
    x0, y0, x1, y1 = CHIP
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sides = [
        [(cx + off, y1 + PIN_LEN, cx + off, y1) for off in PIN_OFF],           # bottom
        [(x0 - PIN_LEN, cy + off, x0, cy + off) for off in PIN_OFF],           # left
        [(cx + off, y0 - PIN_LEN, cx + off, y0) for off in PIN_OFF],           # top
        [(x1, cy + off, x1 + PIN_LEN, cy + off) for off in PIN_OFF],           # right
    ]
    for pins in sides:
        for (ax, ay, bx, by) in pins:
            d.rounded_rectangle(
                [min(ax, bx) - PIN_W / 2, min(ay, by) - PIN_W / 2,
                 max(ax, bx) + PIN_W / 2, max(ay, by) + PIN_W / 2],
                radius=PIN_W * s / 2, fill=WHITE)
    # The chip's outline, and the star on its face: the logo's sparkle,
    # drawn alone so it stays whole where the tile is small.
    d.rounded_rectangle(
        [x0 * s, y0 * s, x1 * s, y1 * s],
        radius=CHIP_RADIUS * s, outline=WHITE, width=max(1, round(CHIP_STROKE * s)))
    d.polygon(star_points(cx * s, cy * s, STAR * s, STAR_IN * s), fill=WHITE)
    return img.resize((size, size), Image.LANCZOS)


def nebula(size, seed=3):
    """The logo's sky, on a size px square: a diagonal indigo gradient,
    its violet, pink, and cyan clouds, and a scatter of stars."""
    # The gradient: a 2x2 grid of the sky's corners, stretched smooth.
    corners = Image.new('RGB', (2, 2))
    corners.putpixel((0, 0), NIGHT_TOP)
    corners.putpixel((1, 0), NIGHT_MID)
    corners.putpixel((0, 1), NIGHT_MID)
    corners.putpixel((1, 1), NIGHT_BOTTOM)
    img = corners.resize((size, size), Image.BILINEAR).convert('RGBA')
    # The clouds: soft round glows, one of each of the nebula's colors,
    # kept to the tile's edges so the symbol's middle stays dark.
    clouds = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    blobs = [
        (0.10, 0.14, 0.42, VIOLET, 88),
        (0.96, 0.62, 0.30, PINK, 66),
        (0.22, 0.94, 0.32, CYAN, 62),
        (0.66, 0.02, 0.18, LAVENDER, 40),
    ]
    for (fx, fy, fr, color, alpha) in blobs:
        bx, by, br = fx * size, fy * size, fr * size
        cd.ellipse([bx - br, by - br, bx + br, by + br], fill=color + (alpha,))
    img.alpha_composite(clouds.filter(ImageFilter.GaussianBlur(size * 0.10)))
    # The stars: dots of white and the clouds' colors toward the tile's
    # edges, a few of them sparkles; a fixed seed keeps every icon's sky
    # the same, and the middle stays clear for the symbol.
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    tints = [WHITE[:3], PINK, CYAN, LAVENDER]
    center = size / 2
    clear = size * 0.34
    for i in range(max(10, round(size * size / 6000))):
        for _ in range(8):
            x, y = rnd.random() * size, rnd.random() * size
            if math.hypot(x - center, y - center) > clear:
                break
        r = (0.5 + rnd.random() * 1.0) * size / 128
        tint = tints[rnd.randrange(len(tints))]
        alpha = round(55 + rnd.random() * 70)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tint + (alpha,))
        if i % 9 == 0:
            ray = r * (2.4 + rnd.random() * 1.2)
            w = max(1, round(size / 220))
            for (dx, dy) in ((1, 0), (0, 1)):
                d.line([(x - ray * dx, y - ray * dy), (x + ray * dx, y + ray * dy)],
                       fill=tint + (round(alpha * 0.55),), width=w)
    return img


def art_layer(art, size, share):
    """The art's visible part, its larger side share of size, centered."""
    art = art.crop(art.getchannel('A').getbbox())
    scale = size * share / max(art.size)
    w, h = max(1, round(art.width * scale)), max(1, round(art.height * scale))
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    layer.alpha_composite(art.resize((w, h), Image.LANCZOS), ((size - w) // 2, (size - h) // 2))
    return layer


def tile(glyph, size):
    """The legacy launcher tile: the artwork, with rounded corners."""
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 5, fill=255)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(glyph.resize((size, size), Image.LANCZOS), (0, 0), mask)
    return out


def android(glyph):
    for dpi, k in DENSITY.items():
        folder = os.path.join(RES, 'mipmap-' + dpi)
        os.makedirs(folder, exist_ok=True)
        px = round(108 * k)
        # The background layer is the artwork itself; since launchers
        # crop it, the same artwork shrunk into the safe zone rides on
        # top as the foreground layer.
        source_art(px).save(os.path.join(folder, 'ic_launcher_background.png'), optimize=True)
        small = round(px * 0.62)
        layer = Image.new('RGBA', (px, px), (0, 0, 0, 0))
        layer.alpha_composite(tile(source_art(small), small), ((px - small) // 2, (px - small) // 2))
        layer.save(os.path.join(folder, 'ic_launcher_foreground.png'), optimize=True)
        tile(glyph, round(48 * k)).save(os.path.join(folder, 'ic_launcher.png'), optimize=True)
    folder = os.path.join(RES, 'mipmap-anydpi-v26')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'ic_launcher.xml'), 'w', newline='\n') as f:
        f.write(ADAPTIVE)


def tv_banner(glyph):
    """Android TV's banner, which its home screen shows in the apps row:
    the symbol and the name, 320 x 180 px (160 x 90 dp at xhdpi), on the
    app's night indigo (its night theme), which stands out from the TV's
    black home screen as the other apps' tiles do."""
    w, h = 320, 180
    out = Image.new('RGBA', (w, h))
    grad = Image.new('RGB', (1, 2))
    grad.putpixel((0, 0), NIGHT_TOP)
    grad.putpixel((0, 1), NIGHT_BOTTOM)
    out.paste(grad.resize((w, h), Image.BILINEAR), (0, 0))
    symbol = art_layer(glyph, 96, 1.0)
    font = ImageFont.truetype(os.path.join(APP, 'assets', 'fonts', 'Vazirmatn-Bold.ttf'), 34)
    name = 'SalviaVPN'
    draw = ImageDraw.Draw(out)
    left, top, right, bottom = draw.textbbox((0, 0), name, font=font)
    gap = 14
    x = (w - (symbol.width + gap + right - left)) // 2
    out.alpha_composite(symbol, (x, (h - symbol.height) // 2))
    draw.text((x + symbol.width + gap - left, (h - (bottom - top)) // 2 - top), name, font=font, fill=(255, 255, 255, 255))
    folder = os.path.join(RES, 'drawable-xhdpi')
    os.makedirs(folder, exist_ok=True)
    out.save(os.path.join(folder, 'banner.png'), optimize=True)


def crisp(art, size):
    """A small size: shrunk from the full art, then sharpened and given a
    little more contrast and color, which a few pixels otherwise lose."""
    image = art_layer(art, size, 1.0)
    alpha = image.getchannel('A')
    rgb = image.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.6 if size <= 24 else 0.8, percent=120, threshold=0))
    rgb = ImageEnhance.Color(ImageEnhance.Contrast(rgb).enhance(1.06)).enhance(1.10)
    out = rgb.convert('RGBA')
    out.putalpha(alpha)
    return out


def write_ico(path, art):
    # Each size drawn from the full art; up to 48 px sharpened.
    images = [crisp(art, n) if n <= 48 else art_layer(art, n, 1.0) for n in WINDOWS_SIZES]
    images[-1].save(path, format='ICO', sizes=[(n, n) for n in WINDOWS_SIZES], append_images=images[:-1])


def app_logo(tile_art):
    art_layer(tile_art, 256, 1.0).save(os.path.join(APP, 'assets', 'logo.png'), optimize=True)


def windows(tile_art):
    write_ico(os.path.join(APP, 'windows', 'runner', 'resources', 'app_icon.ico'), tile_art)


def core(tile_art):
    desktop = os.path.join(CORE, 'internal', 'desktop')
    write_ico(os.path.join(desktop, 'appicon.ico'), tile_art)
    art_layer(tile_art, 192, 1.0).save(os.path.join(CORE, 'internal', 'service', 'web', 'icon.png'), optimize=True)


def wordmark(tile_art):
    """The documentation's wordmark (docs/images/wordmark.png): the tile and the
    name in the nebula's colors beside it, with the sparkle of its stars
    and the sweep of its signature underline."""
    def sweep_color(t):
        """The nebula's color at t (0..1) along the name's sweep."""
        stops = [(0.0, (0x7B, 0x4A, 0xDC)), (0.50, PINK), (1.0, (0x1E, 0x6F, 0xD6))]
        for i in range(1, len(stops)):
            if t <= stops[i][0]:
                (t0, c0), (t1, c1) = stops[i - 1], stops[i]
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                return tuple(round(c0[j] + (c1[j] - c0[j]) * f) for j in range(3))
        return stops[-1][1]

    tile = art_layer(tile_art, 256, 1.0)
    name = 'SalviaVPN'
    font = ImageFont.truetype(os.path.join(APP, 'assets', 'fonts', 'Inter', 'Inter-Bold.ttf'), 132)
    # The name's box, to size the banner around it.
    probe = Image.new('RGBA', (8, 8))
    box = ImageDraw.Draw(probe).textbbox((0, 0), name, font=font)
    gap = 46
    w = tile.width + gap + (box[2] - box[0]) + 150
    h = 320
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(tile, ((h - tile.height) // 2, (h - tile.height) // 2))
    # The name: a horizontal sweep of the nebula's colors through the
    # letters, a soft light edge, and a sheen along their top.
    text = Image.new('L', (box[2] - box[0] + 8, box[3] - box[1] + 8), 0)
    ImageDraw.Draw(text).text((4 - box[0], 4 - box[1]), name, font=font, fill=255)
    tx = tile.width + gap
    ty = (h - text.height) // 2 - 14
    ramp = Image.new('RGB', (256, 1))
    for x in range(256):
        ramp.putpixel((x, 0), sweep_color(x / 255))
    sweep = ramp.resize((text.width, text.height), Image.BILINEAR).convert('RGBA')
    colored = Image.new('RGBA', (text.width, text.height), (0, 0, 0, 0))
    colored.paste(sweep, (0, 0), text)
    out.alpha_composite(colored, (tx, ty))
    # The signature: the logo's sweep, a clean tapering wedge that starts
    # below the name's middle and rises past its end, a small star riding
    # the tip.
    x_start = tx + text.width * 0.34
    x_end = tx + text.width + 48
    y_start = ty + text.height + 30
    y_end = ty + text.height + 6
    steps = 120
    top, bottom = [], []
    for i in range(steps):
        t = i / (steps - 1)
        x = x_start + (x_end - x_start) * t
        y = y_start + (y_end - y_start) * t - 7 * math.sin(math.pi * t)
        half = 2.3 * (1 - t * 0.82) + 0.4
        top.append((x - half, y - half))
        bottom.append((x + half, y + half))
    # A soft pink glow under the sweep, then the sweep itself, a violet-to-
    # pink wedge through a mask so its edges stay crisp.
    glow = Image.new('RGBA', out.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(0, steps, 2):
        t = i / (steps - 1)
        x = x_start + (x_end - x_start) * t
        y = y_start + (y_end - y_start) * t - 7 * math.sin(math.pi * t)
        r = 6 * (1 - t) + 2
        gd.ellipse([x - r, y - r, x + r, y + r], fill=PINK + (40,))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(4)))
    mask = Image.new('L', out.size, 0)
    ImageDraw.Draw(mask).polygon(top + bottom[::-1], fill=255)
    ramp2 = Image.new('RGB', (256, 1))
    for x in range(256):
        ramp2.putpixel((x, 0), sweep_color(0.1 + 0.6 * x / 255))
    layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
    layer.paste(ramp2.resize(out.size, Image.BILINEAR).convert('RGBA'), (0, 0), mask)
    out.alpha_composite(layer)
    d = ImageDraw.Draw(out)
    # The tip's star, in the sweep's cyan: white would vanish on the
    # documentation's light page.
    d.polygon(star_points(x_end + 2, y_end - 14, 10, 2.8), fill=(0x1E, 0x6F, 0xD6, 255))
    d.polygon(star_points(x_end + 2, y_end - 14, 4.5, 1.4), fill=(255, 255, 255, 235))
    out.save(os.path.join(APP, '..', 'docs', 'images', 'wordmark.png'), optimize=True)


# The tray's state colors: green while connected, red on an error, and the
# core's own: blue while Windows' system proxy points at the proxy, faded
# while asleep.
DOT_GOOD, DOT_BAD = (63, 225, 176), (226, 40, 80)
DOT_SET = (96, 165, 250)
TRAY_SIZES = [16, 20, 24, 32, 48, 64]


def asleep(color):
    return tuple(round(c * 0.45 + g * 0.55) for c, g in zip(color, (150, 160, 158)))


TRAY_TILE = (26, 21, 46, 255)


def tray_icon(side=None, dot=None):
    """A tray icon (80 px): the symbol on a dark tile, a dot of color dot
    (RGB) inside the chip's bottom right corner for the state, and, while
    connecting, a white dot of light at the middle pin of side side (0
    bottom, 1 left, 2 top, 3 right), traveling around the chip."""
    n = 320
    img = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=round(n * 0.22), fill=TRAY_TILE)
    art = symbol(round(n * 1.12))
    off = (n - art.width) // 2
    img.alpha_composite(art, (off, off))
    s = art.width / 24
    x0, y0, x1, y1 = CHIP
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if side is not None:
        # The traveling light: on the middle pin of that side, ringed with
        # the tile's dark so it stands clear of the pin and the frame.
        place = [
            (cx, y1 + PIN_LEN / 2),
            (x0 - PIN_LEN / 2, cy),
            (cx, y0 - PIN_LEN / 2),
            (x1 + PIN_LEN / 2, cy),
        ][side]
        x, y = off + place[0] * s, off + place[1] * s
        r = (DOT + DOT_GAP) * s * 1.15
        d.ellipse([x - r, y - r, x + r, y + r], fill=TRAY_TILE)
        r = DOT * s * 1.15
        d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)
    if dot:
        x, y = off + (x1 - 2.5) * s, off + (y1 - 2.5) * s
        r = (DOT + DOT_GAP) * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=TRAY_TILE)
        r = DOT * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=dot + (255,))
    return img.resize((80, 80), Image.LANCZOS)


def save_ico(path, big):
    images = [big.resize((n, n), Image.LANCZOS) for n in TRAY_SIZES]
    images[-1].save(path, format='ICO', sizes=[(n, n) for n in TRAY_SIZES], append_images=images[:-1])


def tray():
    # The app's tray.
    app = os.path.join(APP, 'assets', 'tray')
    for old in os.listdir(app):
        os.remove(os.path.join(app, old))
    icons = {
        'off': tray_icon(),
        'on': tray_icon(dot=DOT_GOOD),
        'idle': tray_icon(dot=DOT_GOOD),
        'error': tray_icon(dot=DOT_BAD),
    }
    # Connecting: a white dot of light from side to side, around the chip.
    for frame in range(1, 5):
        icons['busy%d' % frame] = tray_icon(side=frame - 1)
    for name, big in icons.items():
        save_ico(os.path.join(app, name + '.ico'), big)
        # Linux (AppIndicator) takes a .png; 64 px stays sharp when scaled.
        big.resize((64, 64), Image.LANCZOS).save(os.path.join(app, name + '.png'), optimize=True)
    # The core's tray: an .ico for Windows, a 32 px .png elsewhere.
    folder = os.path.join(CORE, 'internal', 'desktop', 'tray')
    os.makedirs(folder, exist_ok=True)
    states = {
        'running': tray_icon(dot=DOT_GOOD),
        'set': tray_icon(dot=DOT_SET),
        'running-asleep': tray_icon(dot=asleep(DOT_GOOD)),
        'set-asleep': tray_icon(dot=asleep(DOT_SET)),
        'waiting': tray_icon(side=0),
        'error': tray_icon(dot=DOT_BAD),
        'off': tray_icon(),
    }
    for name, big in states.items():
        save_ico(os.path.join(folder, name + '.ico'), big)
        big.resize((32, 32), Image.LANCZOS).save(os.path.join(folder, name + '.png'), optimize=True)


def main():
    glyph = source_art(1024)
    android(glyph)
    tv_banner(glyph)
    windows(glyph)
    core(glyph)
    app_logo(glyph)
    wordmark(glyph)
    tray()


if __name__ == '__main__':
    main()
