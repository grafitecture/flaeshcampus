"""Rahmen-Widgets: Leisten-Fortschritt, Evidence, Fußzeile, Fokus-Box, Fotos und Bildbriefings."""
import tempfile
from pathlib import Path

from PIL import Image
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_SHAPE

from . import oxml
from .measure import Measurer
from .tokens import COLOR, EMU_PER_PX, LABEL_SPC, SIZE_PT, ZONE, px

RAIL_DOT_X = 68          # Mitte der Punkte in der Leiste
RAIL_TOP = 315           # Mitte des ersten Punkts (Punkt-Tops ab y 300)
RAIL_LINE = "3D4B52"


def style(size: str | float, color: str, **extra) -> dict:
    size_pt = SIZE_PT[size] if isinstance(size, str) else size
    return {"size_pt": size_pt, "color": COLOR.get(color, color), **extra}


def textbox(slide, name: str, box, paragraphs: list[tuple[str, dict]], anchor: str = "t"):
    x, y, w, h = box
    tb = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tb.name = name
    oxml.fill_text_frame(tb.text_frame, paragraphs, anchor=anchor)
    return tb


def shape(slide, kind, name: str, box, fill: str | None = None, line=None, glow=None, radius_px: float = 0):
    x, y, w, h = box
    sp = slide.shapes.add_shape(kind, px(x), px(y), px(w), px(h))
    sp.name = name
    style_el = sp._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
    if style_el is not None:
        sp._element.remove(style_el)
    if fill:
        sp.fill.solid()
        sp.fill.fore_color.rgb = RGBColor.from_string(COLOR.get(fill, fill))
    else:
        sp.fill.background()
    if line:
        color, width, *dash = line
        sp.line.color.rgb = RGBColor.from_string(COLOR.get(color, color))
        sp.line.width = px(width)
        if dash and dash[0]:
            sp.line.dash_style = MSO_LINE.DASH
    else:
        sp.line.fill.background()
    if glow:
        color, radius, alpha = glow
        oxml.add_glow(sp, COLOR.get(color, color), radius, alpha)
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        sp.adjustments[0] = (radius_px or 18) / min(w, h)
    return sp


def rail_progress(slide, chapters: list[str], current: int | None, dark: bool) -> None:
    n = len(chapters)
    pitch = min(104, 600 / (n - 1)) if n > 1 else 0
    centers = [RAIL_TOP + i * pitch for i in range(n)]
    shape(slide, MSO_SHAPE.RECTANGLE, "rail-line", (RAIL_DOT_X - 1, centers[0], 2, centers[-1] - centers[0]),
          fill=RAIL_LINE)
    for i, cy in enumerate(centers, 1):
        if current and i == current:
            size, name = 30, f"rail-dot-{i}-active"
            dot = dict(fill="sky", glow=("sky", 26, 95))
            num_color = "sky"
        elif current and i < current:
            size, name, dot, num_color = 16, f"rail-dot-{i}", dict(fill="steel"), "steel"
        else:
            size, name = 16, f"rail-dot-{i}"
            dot = dict(fill="rail" if dark else "night", line=("dim", 3))
            num_color = "dim"
        shape(slide, MSO_SHAPE.OVAL, name, (RAIL_DOT_X - size / 2, cy - size / 2, size, size), **dot)
        textbox(slide, f"rail-num-{i}", (92, cy - 16, 40, 32), [(str(i), style("small", num_color))], anchor="ctr")


def evidence(slide, text: str, dark: bool) -> None:
    textbox(slide, "evidence-label", (240, 920, 600, 24),
            [("Evidence", style("label", "sky", caps=True, spc=LABEL_SPC))])
    textbox(slide, "evidence-text", (240, 948, 1240, 36),
            [(text, style("small", "muted_dark" if dark else "muted"))])


def footer(slide, text: str, dark: bool) -> None:
    textbox(slide, "footer", (240, 1010, 1200, 30),
            [(text, style("label", "muted_dark" if dark else "steel", caps=True, spc=LABEL_SPC))])


def focus_box(slide, box: tuple[int, int, int], label: str, title: str, text: str, m: Measurer) -> int:
    x, y, w = box
    pad_x, pad_y, inner = 46, 44, w - 92
    label_h = m.line_height_px(SIZE_PT["label"])
    title_h = len(m.wrap(title, SIZE_PT["focus_title"], inner)) * m.line_height_px(SIZE_PT["focus_title"])
    text_h = len(m.wrap(text, SIZE_PT["body"], inner)) * m.line_height_px(SIZE_PT["body"]) if text else 0
    height = round(pad_y + label_h + 10 + title_h + (18 + text_h if text else 0) + pad_y)
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, "focus-card", (x, y, w, height),
          fill="night", line=("sky", 2), glow=("sky", 50, 40))
    top = y + pad_y
    textbox(slide, "focus-label", (x + pad_x, top, inner, label_h),
            [(label, style("label", "sky", caps=True, spc=LABEL_SPC))])
    top += label_h + 10
    textbox(slide, "focus-title", (x + pad_x, top, inner, title_h), [(title, style("focus_title", "white"))])
    if text:
        textbox(slide, "focus-text", (x + pad_x, top + title_h + 18, inner, text_h),
                [(text, style("body", "on_dark"))])
    return height


def _as_px(ph) -> tuple[float, float, float, float]:
    return tuple(v / EMU_PER_PX for v in (ph.left, ph.top, ph.width, ph.height))


def _usable_image(path: Path) -> Path:
    if path.suffix.lower() in (".jpg", ".jpeg", ".png"):
        return path
    out = Path(tempfile.mkdtemp(prefix="campus-img-")) / (path.stem + ".jpg")
    Image.open(path).convert("RGB").save(out, "JPEG", quality=92)
    return out


def place_photo(slide, idx: int, photo: dict | None, base_dir: Path, warnings: list[str],
                ellipse: bool = False) -> str | None:
    ph = slide.placeholders[idx]
    photo = photo or {}
    file, brief = photo.get("file"), photo.get("brief")
    path = Path(file) if file else None
    if path is not None and not path.is_absolute():
        path = Path(base_dir) / path
    if path is not None and path.exists():
        pic = ph.insert_picture(str(_usable_image(path)))
        if ellipse:
            pic.auto_shape_type = MSO_SHAPE.OVAL
            pic.line.color.rgb = RGBColor.from_string(COLOR["sky"])
            pic.line.width = px(6)
            oxml.add_glow(pic, COLOR["sky"], 90, 60)
        return None
    if file:
        warnings.append(f"Foto fehlt: {file}")
    text = brief or f"Photo missing: {file}"
    box = _as_px(ph)
    ph._element.getparent().remove(ph._element)
    brief_card(slide, box, text)
    return text


def brief_card(slide, box, brief: str) -> None:
    x, y, w, h = box
    shape(slide, MSO_SHAPE.RECTANGLE, "brief-card", box, fill="mist", line=("steel", 2, True))
    cx, cy = x + w / 2, y + h / 2
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, "brief-icon", (cx - 32, cy - 78, 64, 46),
          fill="steel", radius_px=8)
    shape(slide, MSO_SHAPE.OVAL, "brief-icon-lens", (cx - 12, cy - 67, 24, 24), fill="mist")
    textbox(slide, "brief-text", (x + 40, cy - 16, w - 80, min(h / 2, 120)),
            [(brief, style("body", "slate", align="center"))])


def zone_ring_on_top(slide, dark: bool) -> None:
    shape(slide, MSO_SHAPE.OVAL, "zone-ring-top", ZONE, fill="ring_dark" if dark else "white",
          line=("sky", 4), glow=("sky", 60, 55))
