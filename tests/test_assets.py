import subprocess

from PIL import Image

from conftest import SKILL

BRAND = SKILL / "assets" / "brand"


def test_logo_pngs():
    for name in ("logo-white.png", "logo-slate.png"):
        path = BRAND / name
        assert path.exists(), name
        im = Image.open(path)
        assert im.mode == "RGBA"
        assert im.width == 1200
        assert im.getpixel((0, 0))[3] == 0
        ratio = im.width / im.height
        assert abs(ratio - 595.3 / 252) / (595.3 / 252) < 0.01


def test_portrait():
    path = SKILL / "examples" / "photos" / "gomez.jpg"
    im = Image.open(path)
    assert im.format == "JPEG"
    assert im.width >= 700


def test_font_installed(font_path):
    listing = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
    assert "Corporate S" in listing
