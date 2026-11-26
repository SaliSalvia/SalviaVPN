"""Makes every icon of the program from its artwork, docs/images/logo.png:
the galactic shield in its nebula, which is the logo the documentation
shows and the app draws beside its name. From it:

- Android (android/app/src/main/res): an adaptive icon for Android 8+, the
  artwork on the night sky as the background layer and an empty foreground
  layer to keep, 108 dp each, which the launcher crops to its own shape
  with the shield still whole; and ic_launcher.png for older Android, the
  artwork, rounded. The status bar icon (res/drawable/ic_stat_logo.xml) is
  a white glyph by hand, since a status bar takes one color. The Android TV
  banner (res/drawable-xhdpi/banner.png, 320 x 180 px): the artwork and the
  name in white on the night theme's indigo.
- Windows (windows/runner/resources/app_icon.ico): the artwork, in every
  size Explorer and the taskbar use; the small sizes sharpened, since the
  taskbar shows 24 or 32 px.
- The core (core/internal/desktop): appicon.ico, the same for its
  executable (tools/winres).
- The web dashboard (core/internal/service/web/icon.png): the artwork, for
  the page icon and the logo.
- The app's logo (assets/logo.png): the artwork, beside its name.
- The tray icons: the shield of the artwork as a white glyph on a dark
  tile, since 16 px cannot show the nebula; the pins of one side after the
  other are filled while connecting (four frames), and otherwise a dot of
  the state's color sits at the tile's bottom right corner. The app's tray
  (assets/tray: .ico for Windows, .png for Linux): off, busy1 to busy4, on
  and idle (green), error (red). The core's tray
  (core/internal/desktop/tray: .ico for Windows, .png elsewhere): one icon
  per state, green while the proxy runs, blue while Windows' system proxy
  points at it, faded while asleep, red on an error; the first frame while
  waiting.

docs/images/logo.png is the source, so a new logo is a new file there and
this script run again; it never writes that file.

Run from app/ after changing the artwork (needs Pillow):

    python tool/app_icons.py
"""
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..')
CORE = os.path.join(APP, '..', 'core')
RES = os.path.join(APP, 'android', 'app', 'src', 'main', 'res')
LOGO = os.path.join(APP, '..', 'docs', 'images', 'logo.png')

LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS
DENSITY = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
WINDOWS_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]

# The artwork's share of the adaptive icon's 108 dp canvas: a launcher shows
# the middle 72 dp (67%), so 0.86 keeps the shield inside the crop.
ART = 0.86
NIGHT = (0x0A, 0x06, 0x22, 255)
WHITE = (255, 255, 255, 255)

ADAPTIVE = '''<?xml version="1.0" encoding="utf-8"?>
<!-- The launcher icon on Android 8+: the artwork over the night sky; the
     launcher crops both layers to its own shape. Made by
     tool/app_icons.py. -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
'''


def square(base, size):
    """The artwork, a size px square (it is a square already)."""
    return base.resize((size, size), LANCZOS)


def crisp(image):
    """A small size: sharpened and given a little more contrast and color,
    which a few pixels otherwise lose."""
    alpha = image.getchannel('A')
    rgb = image.convert('RGB').filter(
        ImageFilter.UnsharpMask(radius=0.6 if image.width <= 24 else 0.8, percent=120, threshold=0))
    rgb = ImageEnhance.Color(ImageEnhance.Contrast(rgb).enhance(1.06)).enhance(1.10)
    out = rgb.convert('RGBA')
    out.putalpha(alpha)
    return out


def rounded(image, share):
    """The image with its corners cut back, share of its side."""
    size = image.width
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=round(size * share), fill=255)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def write_ico(path, base):
    """An .ico of every size Windows asks for: the small ones sharpened."""
    images = []
    for n in WINDOWS_SIZES:
        image = square(base, n)
        images.append(crisp(image) if n <= 48 else image)
    images[-1].save(path, format='ICO', sizes=[(n, n) for n in WINDOWS_SIZES], append_images=images[:-1])


def android(base):
    for dpi, k in DENSITY.items():
        folder = os.path.join(RES, 'mipmap-' + dpi)
        os.makedirs(folder, exist_ok=True)
        px = round(108 * k)
        art = square(base, round(px * ART))
        layer = Image.new('RGBA', (px, px), NIGHT)
        layer.alpha_composite(art, ((px - art.width) // 2, (px - art.height) // 2))
        layer.save(os.path.join(folder, 'ic_launcher_background.png'), optimize=True)
        # The launcher expects a foreground layer; the background carries
        # the whole icon.
        Image.new('RGBA', (px, px), (0, 0, 0, 0)).save(
            os.path.join(folder, 'ic_launcher_foreground.png'), optimize=True)
        side = round(48 * k)
        image = square(base, side)
        rounded(crisp(image) if side <= 48 else image, 0.2).save(
            os.path.join(folder, 'ic_launcher.png'), optimize=True)
    folder = os.path.join(RES, 'mipmap-anydpi-v26')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'ic_launcher.xml'), 'w', newline='\n') as f:
        f.write(ADAPTIVE)


def tv_banner(base):
    """Android TV's banner, which its home screen shows in the apps row:
    the artwork and the name, 320 x 180 px (160 x 90 dp at xhdpi), on the
    app's night indigo (its night theme), which stands out from the TV's
    black home screen as the other apps' tiles do."""
    w, h = 320, 180
    out = Image.new('RGBA', (w, h))
    top, bottom = (0x24, 0x1B, 0x6E), (0x0C, 0x0A, 0x3E)
    grad = Image.new('RGB', (1, 2))
    grad.putpixel((0, 0), top)
    grad.putpixel((0, 1), bottom)
    out.paste(grad.resize((w, h)).convert('RGBA'), (0, 0))
    art = rounded(square(base, 104), 0.18)
    font = ImageFont.truetype(os.path.join(APP, 'assets', 'fonts', 'Vazirmatn-Bold.ttf'), 34)
    name = 'SalviaVPN'
    draw = ImageDraw.Draw(out)
    left, top_box, right, bottom_box = draw.textbbox((0, 0), name, font=font)
    gap = 14
    x = (w - (art.width + gap + right - left)) // 2
    out.alpha_composite(art, (x, (h - art.height) // 2))
    draw.text((x + art.width + gap - left, (h - (bottom_box - top_box)) // 2 - top_box),
              name, font=font, fill=WHITE)
    folder = os.path.join(RES, 'drawable-xhdpi')
    os.makedirs(folder, exist_ok=True)
    out.save(os.path.join(folder, 'banner.png'), optimize=True)


def windows(base):
    write_ico(os.path.join(APP, 'windows', 'runner', 'resources', 'app_icon.ico'), base)


def linux(base):
    square(base, 256).save(os.path.join(APP, 'linux', 'runner', 'resources', 'app_icon.png'), optimize=True)


def app_logo(base):
    square(base, 256).save(os.path.join(APP, 'assets', 'logo.png'), optimize=True)


def core(base):
    desktop = os.path.join(CORE, 'internal', 'desktop')
    write_ico(os.path.join(desktop, 'appicon.ico'), base)
    square(base, 192).save(os.path.join(CORE, 'internal', 'service', 'web', 'icon.png'), optimize=True)


# The tray's state colors: green while connected, red on an error, and the
# core's own: blue while Windows' system proxy points at the proxy, faded
# while asleep.
DOT_GOOD, DOT_BAD = (63, 225, 176), (226, 40, 80)
DOT_SET = (96, 165, 250)
TRAY_SIZES = [16, 20, 24, 32, 48, 64]
TRAY_TILE = (26, 21, 46, 255)
TILE = 320


def asleep(color):
    return tuple(round(c * 0.45 + g * 0.55) for c, g in zip(color, (150, 160, 158)))


def shield(cx, cy, w, h):
    """The artwork's shield as an outline of points: a flat top, straight
    sides to the shoulders, and curves to the point at the bottom."""
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - h / 2, cy + h / 2
    shoulder = y0 + h * 0.42
    steps = 10
    curve = []
    for i in range(steps + 1):
        t = i / steps
        curve.append((
            (1 - t) ** 2 * x1 + 2 * (1 - t) * t * x1 + t * t * cx,
            (1 - t) ** 2 * shoulder + 2 * (1 - t) * t * (y0 + h * 0.90) + t * t * y1,
        ))
    mirrored = [(2 * cx - x, y) for (x, y) in curve][::-1]
    return [(x0, y0), (x1, y0)] + curve + mirrored


def tray_icon(side=None, dot=None):
    """A tray icon (320 px): the artwork's shield, white on a dark tile, a
    dot of color dot (RGB) at the tile's bottom right corner for the state,
    and, while connecting, a white dot of light at the shield's side
    (0 bottom, 1 left, 2 top, 3 right)."""
    img = Image.new('RGBA', (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, TILE - 1, TILE - 1], radius=round(TILE * 0.22), fill=TRAY_TILE)
    cx, cy = TILE / 2, TILE * 0.52
    w, h = TILE * 0.50, TILE * 0.60
    d.polygon(shield(cx, cy, w, h), fill=WHITE)
    if side is not None:
        x, y = [
            (cx, cy + h / 2), (cx - w / 2, cy), (cx, cy - h / 2), (cx + w / 2, cy),
        ][side]
        ring = TILE * 0.075
        d.ellipse([x - ring, y - ring, x + ring, y + ring], fill=TRAY_TILE)
        r = TILE * 0.048
        d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)
    if dot:
        x, y = TILE * 0.735, TILE * 0.735
        ring = TILE * 0.135 + TILE * 0.035
        d.ellipse([x - ring, y - ring, x + ring, y + ring], fill=TRAY_TILE)
        r = TILE * 0.135
        d.ellipse([x - r, y - r, x + r, y + r], fill=dot + (255,))
    return img


def save_ico(path, big):
    images = [big.resize((n, n), LANCZOS) for n in TRAY_SIZES]
    images[-1].save(path, format='ICO', sizes=[(n, n) for n in TRAY_SIZES], append_images=images[:-1])


def tray():
    # The app's tray.
    app = os.path.join(APP, 'assets', 'tray')
    icons = {
        'off': tray_icon(),
        'on': tray_icon(dot=DOT_GOOD),
        'idle': tray_icon(dot=DOT_GOOD),
        'error': tray_icon(dot=DOT_BAD),
    }
    # Connecting: a white dot of light from side to side, around the shield.
    for frame in range(1, 5):
        icons['busy%d' % frame] = tray_icon(side=frame - 1)
    for name, big in icons.items():
        save_ico(os.path.join(app, name + '.ico'), big)
        # Linux (AppIndicator) takes a .png; 64 px stays sharp when scaled.
        big.resize((64, 64), LANCZOS).save(os.path.join(app, name + '.png'), optimize=True)
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
        big.resize((32, 32), LANCZOS).save(os.path.join(folder, name + '.png'), optimize=True)


def main():
    base = Image.open(LOGO).convert('RGBA')
    android(base)
    tv_banner(base)
    windows(base)
    linux(base)
    app_logo(base)
    core(base)
    tray()


if __name__ == '__main__':
    main()
