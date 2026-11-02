"""Einblendung von Dr. Gómez: Modi, Videofeld, Standbild als Platzhalter für das Video, Untertitel.

Jede Folie bestimmt im Folienplan selbst, wie er erscheint (`"presenter": {"mode": …}`):

    none          keine Einblendung (Sprecher aus dem Off)
    full          Vollbild; Texte liegen links auf einem dunklen Verlauf, er steht rechts
    half_left     halbe Folie links (rechts neben der Leiste), Inhalt rechts
    half_right    halbe Folie rechts, Inhalt links
    third_left    Drittel links, Inhalt rechts
    third_right   Drittel rechts, Inhalt links
    small         kleines Feld (16:9) mit "at" ("top_right", "bottom_right") oder "box": [x, y, Breite]

Optional zeigt `"caption"` das gesprochene Wort als Untertitel über dem Video.
Das Videofeld zeigt ein Standbild von Dr. Gómez; im Schnitt wird dort das Video eingesetzt.
"""
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

from . import oxml
from .measure import Measurer
from .tokens import COLOR, EMU_PER_PX, PRESENTER_MODES as MODES, SLIDE_PX, SMALL_AT, VIDEO_PRESENTER, px

PANEL_W = {"half": 960, "third": 640}
RAIL_W = 150
GAP = 70                      # Abstand zwischen Inhalt und Videofeld
CONTENT = (240, 1800)         # Inhaltsbereich ohne Einblendung (x0, x1)
FULL_AREA = (160, 1000)       # Vollbild: Textspalte links auf dem Verlauf
FULL_KEEP_CLEAR = (1040, 0, 880, 1080)   # Vollbild: hier steht er, kein Inhalt
SMALL_RADIUS = 16
PREFIX = "presenter-"         # alle Formen der Einblendung; die Prüfung erkennt sie am Namen

Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class Presenter:
    mode: str = "none"
    box: Box | None = None              # Videofeld in px
    area: tuple[float, float] = CONTENT  # Inhaltsbereich x0, x1
    caption: str | None = None

    @property
    def kind(self) -> str:
        """none, full, panel oder small."""
        if self.mode in ("none", "full", "small"):
            return self.mode
        return "panel"

    @property
    def narrow(self) -> bool:
        """Inhalt muss in einen schmaleren Bereich als üblich."""
        return self.area != CONTENT

    @property
    def area_w(self) -> float:
        return self.area[1] - self.area[0]

    @property
    def keep_clear(self) -> Box | None:
        return FULL_KEEP_CLEAR if self.kind == "full" else self.box


def resolve(spec: dict | None) -> Presenter:
    """Folienplan-Angabe → Videofeld und Inhaltsbereich (die Angabe ist schon geprüft)."""
    spec = spec or {}
    mode = spec.get("mode", "none")
    caption = spec.get("caption") or None
    if mode == "none":
        return Presenter()
    if mode == "full":
        return Presenter(mode, (0, 0, *SLIDE_PX), FULL_AREA, caption)
    if mode == "small":
        x, y, w = spec.get("box") or SMALL_AT[spec.get("at", "bottom_right")]
        return Presenter(mode, (x, y, w, round(w * 9 / 16)), CONTENT, caption)
    size, side = mode.split("_")
    w = PANEL_W[size]
    if side == "right":
        return Presenter(mode, (SLIDE_PX[0] - w, 0, w, SLIDE_PX[1]), (CONTENT[0], SLIDE_PX[0] - w - GAP), caption)
    return Presenter(mode, (RAIL_W, 0, w, SLIDE_PX[1]), (RAIL_W + w + GAP, 1820), caption)


def frame_box(spec: dict | None) -> Box | None:
    return resolve(spec).box


# ---------------------------------------------------------------- Standbild

def _bg_color(img: Image.Image) -> tuple[int, int, int]:
    """Hintergrundfarbe des Porträts aus den oberen Ecken."""
    w = img.width
    samples = [img.crop(b).resize((1, 1), Image.BOX).getpixel((0, 0)) for b in
               ((0, 0, w // 20, w // 20), (w - w // 20, 0, w, w // 20))]
    return tuple(sum(c[i] for c in samples) // len(samples) for i in range(3))


def _feather(size: tuple[int, int], edge: int) -> Image.Image:
    """Maske mit weichen Kanten links, rechts und oben (unten läuft das Bild aus dem Rahmen)."""
    w, h = size
    mask = Image.new("L", size, 255)
    draw = ImageDraw.Draw(mask)
    for i in range(edge):
        a = round(255 * i / edge)
        draw.line([(i, 0), (i, h)], fill=a)
        draw.line([(w - 1 - i, 0), (w - 1 - i, h)], fill=a)
    top = Image.new("L", size, 255)
    tdraw = ImageDraw.Draw(top)
    for i in range(edge):
        tdraw.line([(0, i), (w, i)], fill=round(255 * i / edge))
    return ImageChops.multiply(mask, top)


# Bildausschnitt je Art: Bildhöhe relativ zum Rahmen, Kopfraum, waagerechte Lage des Gesichts
_FRAMING = {"full": (0.97, 0.05, 0.74), "panel": (0.97, 0.05, 0.5), "small": (2.1, 0.08, 0.5)}
_FACE_X, _HEAD_TOP = 0.49, 0.025     # im Porträt: Gesichtsmitte und Scheitel (Anteil an Breite/Höhe)


@lru_cache(maxsize=64)
def still_image(photo: str, w: int, h: int, kind: str) -> Path:
    """Standbild für ein Videofeld: Porträt auf erweitertem Hintergrund, passend zum Seitenverhältnis."""
    zoom, headroom, face_x = _FRAMING[kind]
    with Image.open(photo) as src:
        src = src.convert("RGB")
        canvas = Image.new("RGB", (w, h), _bg_color(src))
        ph = round(h * zoom)
        pw = round(src.width * ph / src.height)
        img = src.resize((pw, ph), Image.LANCZOS)
    x = round(face_x * w - _FACE_X * pw)
    y = round(headroom * h - _HEAD_TOP * ph)
    if y + ph < h:
        y = h - ph
    canvas.paste(img, (x, y), _feather((pw, ph), max(12, round(pw * 0.06))))
    out = Path(tempfile.mkdtemp(prefix="campus-presenter-")) / f"presenter-{kind}-{w}x{h}.jpg"
    canvas.save(out, "JPEG", quality=86, optimize=True)
    return out


def presenter_photo(plan: dict, base_dir: Path, assets: Path) -> Path:
    """Porträt für die Standbilder: das Foto aus dem Folienplan, sonst das Marken-Bild."""
    file = ((plan["episode"].get("presenter") or {}).get("photo") or {}).get("file")
    if file:
        path = Path(file) if Path(file).is_absolute() else Path(base_dir) / file
        try:
            with Image.open(path) as im:
                im.verify()
            return path
        except Exception:
            pass
    return Path(assets) / VIDEO_PRESENTER


# ---------------------------------------------------------------- Zeichnen

def _to_back(slide, *shapes) -> None:
    """Formen ganz nach hinten legen (hinter die Platzhalter der Folie)."""
    tree = slide.shapes._spTree
    for offset, shape in enumerate(shapes):
        tree.remove(shape._element)
        tree.insert(2 + offset, shape._element)


def _plain(slide, kind, name: str, box: Box):
    x, y, w, h = box
    sp = slide.shapes.add_shape(kind, px(x), px(y), px(w), px(h))
    sp.name = name
    style = sp._element.find(qn("p:style"))
    if style is not None:
        sp._element.remove(style)
    sp.line.fill.background()
    return sp


def _round_corners(pic, radius_px: float, box: Box) -> None:
    pic.auto_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE
    geom = pic._element.spPr.find(qn("a:prstGeom"))
    av = geom.find(qn("a:avLst"))
    for old in list(av):
        av.remove(old)
    gd = av.makeelement(qn("a:gd"), {"name": "adj", "fmla": f"val {round(radius_px / min(box[2], box[3]) * 100000)}"})
    av.append(gd)


def draw(slide, p: Presenter, photo: Path, dark: bool, assets: Path) -> None:
    """Videofeld mit Standbild zeichnen (ohne Untertitel)."""
    if p.kind == "none":
        return
    x, y, w, h = p.box
    still = still_image(str(photo), round(w), round(h), p.kind)
    pic = slide.shapes.add_picture(str(still), px(x), px(y), px(w), px(h))
    pic.name = PREFIX + "video"
    if p.kind == "full":
        shade = _plain(slide, MSO_SHAPE.RECTANGLE, PREFIX + "shade", p.box)
        oxml.set_linear_fill(shade, COLOR["night"], [(0, 94), (38, 82), (66, 0)], angle=0)
        _to_back(slide, pic, shade)
        logo = slide.shapes.add_picture(str(Path(assets) / "brand" / "logo-white.png"), px(64), px(986), px(110))
        logo.name = PREFIX + "logo"   # unten links wie in der Leiste
        return
    if p.kind == "panel":
        edge_x = x if x > RAIL_W else x + w
        edge = _plain(slide, MSO_SHAPE.RECTANGLE, PREFIX + "edge", (edge_x - 2, 0, 4, h))
        edge.fill.solid()
        edge.fill.fore_color.rgb = RGBColor.from_string(COLOR["sky"])
        oxml.add_glow(edge, COLOR["sky"], 40, 60 if dark else 45)
        return
    _round_corners(pic, SMALL_RADIUS, p.box)
    pic.line.color.rgb = RGBColor.from_string(COLOR["sky"])
    pic.line.width = px(3)
    oxml.add_glow(pic, COLOR["sky"], 46 if dark else 36, 55 if dark else 40)


CAPTION_MAX_LINES = 2   # Untertitel: höchstens zwei Zeilen, sonst kürzen


def caption(slide, p: Presenter, m: Measurer) -> int:
    """Das gesprochene Wort als Untertitel über dem Video: dunkles Feld, weiße Schrift, mittig unter ihm.

    Gibt die Zeilenzahl zurück (0 ohne Untertitel)."""
    if p.kind == "none" or not p.caption:
        return 0
    x, y, w, h = p.box
    if p.kind == "full":   # unter ihm, rechts neben der Textspalte
        kx, _, kw, _ = FULL_KEEP_CLEAR
        size, max_w, cx, bottom = 23, kw - 40, kx + kw / 2, SLIDE_PX[1] - 64
    elif p.kind == "panel":
        size, max_w, cx, bottom = 20, w - 64, x + w / 2, SLIDE_PX[1] - 64
    else:
        size, max_w, cx, bottom = (17 if w >= 520 else 15), w - 36, x + w / 2, y + h - 14
    pad_x, pad_y = (26, 14) if size >= 20 else (16, 9)
    lines = m.wrap(p.caption, size, max_w - 2 * pad_x)
    text_w = max(m.width_px(line, size) for line in lines) + 8   # Reserve: PowerPoint misst minimal anders
    line_h = m.line_height_px(size)
    bw, bh = min(text_w + 2 * pad_x, max_w), len(lines) * line_h + 2 * pad_y
    bx, by = cx - bw / 2, bottom - bh
    box = _plain(slide, MSO_SHAPE.ROUNDED_RECTANGLE, PREFIX + "caption-box", (bx, by, bw, bh))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor.from_string(COLOR["night"])
    oxml.set_fill_alpha(box, 82)
    box.adjustments[0] = 12 / min(bw, bh)
    tb = slide.shapes.add_textbox(px(bx + pad_x - 4), px(by + pad_y), px(bw - 2 * pad_x + 8), px(len(lines) * line_h))
    tb.name = PREFIX + "caption"
    style = {"size_pt": size, "color": COLOR["white"], "align": "center"}
    oxml.fill_text_frame(tb.text_frame, [(p.caption, style)], anchor="t")
    return len(lines)


def _box_px(shape) -> Box:
    return tuple(v / EMU_PER_PX for v in (shape.left, shape.top, shape.width, shape.height))


def intersects(a: Box, b: Box, tol: float = 1) -> bool:
    return a[0] < b[0] + b[2] - tol and b[0] < a[0] + a[2] - tol and a[1] < b[1] + b[3] - tol and b[1] < a[1] + a[3] - tol


def make_room(slide, p: Presenter, gap: float = 40) -> None:
    """Textfelder, die ins Videofeld reichen, enden davor (Titel, Kicker, Zitat, Fußzeile, Evidence …).

    Nur Breite, nie Schriftgröße. Andere Formen bleiben, wo sie sind; die Prüfung meldet Kollisionen.
    """
    zone = p.keep_clear
    if zone is None or p.kind == "full":
        return
    for shape in slide.shapes:
        if shape.name.startswith(PREFIX) or not shape.has_text_frame:
            continue
        x, y, w, h = _box_px(shape)
        if not intersects((x, y, w, h), zone) or zone[0] < x + 120:
            continue
        width = zone[0] - gap - x
        if width >= 200:
            left, top, height = shape.left, shape.top, shape.height
            shape.left, shape.top, shape.width, shape.height = left, top, px(width), height
