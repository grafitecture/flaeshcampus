"""Ein Renderer pro Folientyp: Layout wählen, Platzhalter füllen, dynamische Elemente zeichnen."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pptx.dml.color import RGBColor
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Pt

from . import presenter as pres
from .layouts import LAYOUTS
from .measure import Measurer, Para
from .plan import default_kicker
from .presenter import Presenter
from .tokens import COLOR, EMU_PER_PX, PH_IDX, SIZE_PT, px
from .widgets_content import (bars_card, case_findings, checklist, closing_steps, compare_columns, markers, photo_steps,
                              points_text, quiz_options, scale_caption, scale_chips, steps_grid, summary_items,
                              timeline)
from .widgets_frame import evidence, focus_box, footer, place_photo, rail_progress

LAYOUT_BY_KEY = {ldef.key: ldef.name for ldef in LAYOUTS}
CHAPTER_TITLE = next(p for ldef in LAYOUTS if ldef.key == "chapter" for p in ldef.placeholders if p.name == "Title")
DARK_KEYS = {"cover", "chapter", "hook", "closing", "photo", "quiz"}
NO_FOOTER = {"cover", "chapter", "photo"}


@dataclass
class BuildReport:
    slides: int = 0
    briefs: list[tuple[int, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    presenter: list[dict] = field(default_factory=list)   # Schnittliste: Folie, Modus, Videofeld, Untertitel


@dataclass
class Ctx:
    prs: object
    plan: dict
    m: Measurer
    base_dir: Path
    report: BuildReport
    assets: Path = Path(__file__).resolve().parents[2] / "assets"
    photo: Path | None = None              # Porträt für die Standbilder im Videofeld


# ---------------------------------------------------------------- Grundfunktionen

def new_slide(ctx: Ctx, layout_name: str):
    layout = next(lay for lay in ctx.prs.slide_layouts if lay.name == layout_name)
    slide = ctx.prs.slides.add_slide(layout)
    ctx.report.slides += 1
    return slide


def _placeholder(slide, name: str):
    for ph in slide.placeholders:
        if name == "Title":
            if ph.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
                return ph
        elif ph.placeholder_format.idx == PH_IDX[name]:
            return ph
    return None


def fill(slide, name: str, text: str | None) -> None:
    ph = _placeholder(slide, name)
    if ph is None:
        return
    if not text or not str(text).strip():
        ph._element.getparent().remove(ph._element)
        return
    tf = ph.text_frame
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)
    lines = str(text).split("\n")
    tf.paragraphs[0].add_run().text = lines[0]
    for line in lines[1:]:
        tf.add_paragraph().add_run().text = line


def _photo(ctx: Ctx, slide, name: str, photo: dict | None, ellipse: bool = False) -> None:
    brief = place_photo(slide, PH_IDX[name], photo, ctx.base_dir, ctx.report.warnings, ellipse=ellipse)
    if brief:
        ctx.report.briefs.append((ctx.report.slides, brief))


def presenter_of(s: dict, key: str = "presenter") -> Presenter:
    spec = s.get(key, s.get("presenter"))
    if s["type"] == "cover" and not spec:
        spec = {"mode": "third_right"}
    return pres.resolve(spec)


def _frame(ctx: Ctx, slide, s: dict, chapter: int | None = None, p: Presenter = Presenter()) -> None:
    """Leiste, Evidence, Fußzeile, Notizen; danach die Einblendung von Dr. Gómez."""
    ep = ctx.plan["episode"]
    key = s["type"]
    dark = key in DARK_KEYS or p.kind == "full"
    x0, width = p.area[0], p.area_w
    if p.kind == "full":   # Vollbild: das Video deckt die Leiste; nur das Logo bleibt
        fill(slide, "Episode", None)
    else:
        fill(slide, "Episode", f"{ep['number']:02d}")
        if key != "cover":
            rail_progress(slide, ep["chapters"], chapter if chapter is not None else s.get("chapter"), dark)
    if s.get("evidence"):
        evidence(slide, s["evidence"], dark, x=x0, w=min(1240, width))
    if key not in NO_FOOTER and p.kind != "full":
        footer(slide, f"{ep['title'].upper()} · {ctx.report.slides}", dark, x=x0, w=min(1200, width))
    if s.get("notes"):
        slide.notes_slide.notes_text_frame.text = s["notes"]
    _presenter(ctx, slide, p, dark)


def _presenter(ctx: Ctx, slide, p: Presenter, dark: bool) -> None:
    if p.kind == "none":
        return
    pres.make_room(slide, p)
    pres.draw(slide, p, ctx.photo or ctx.assets / "brand" / "video-presenter.jpg", dark, ctx.assets)
    if pres.caption(slide, p, ctx.m) > pres.CAPTION_MAX_LINES:
        ctx.report.warnings.append(f"Folie {ctx.report.slides}: Untertitel länger als {pres.CAPTION_MAX_LINES} "
                                   f"Zeilen – kürzen")
    ctx.report.presenter.append({"slide": ctx.report.slides, "mode": p.mode,
                                 "box": [round(v) for v in p.box], "caption": p.caption})


def _place(shape, x: float | None = None, y: float | None = None, w: float | None = None,
           h: float | None = None) -> None:
    """Platzhalter verschieben/strecken (px); alle vier Werte setzen, sonst fehlen geerbte Maße im xfrm."""
    left, top, width, height = shape.left, shape.top, shape.width, shape.height
    shape.left = left if x is None else px(x)
    shape.top = top if y is None else px(y)
    shape.width = width if w is None else px(w)
    shape.height = height if h is None else px(h)


def _to_area(slide, p: Presenter, *names: str) -> None:
    """Spalten-Platzhalter in den Inhaltsbereich neben dem Videofeld rücken: gleicher Anfang, höchstens so breit."""
    if not p.narrow:
        return
    for name in names:
        ph = _placeholder(slide, name)
        if ph is not None:
            _place(ph, x=p.area[0], w=min(ph.width / EMU_PER_PX, p.area_w))


def _recolor(slide, name: str, color: str) -> None:
    """Textfarbe auf der Folie überschreiben (helle Layouts im Vollbild über dem Video)."""
    ph = _placeholder(slide, name)
    if ph is None:
        return
    for para in ph.text_frame.paragraphs:
        for run in para.runs:
            run.font.color.rgb = RGBColor.from_string(COLOR[color])


def _start(ctx: Ctx, s: dict, title: bool = True, p: Presenter = Presenter()):
    slide = new_slide(ctx, LAYOUT_BY_KEY[s["type"]])
    fill(slide, "Kicker", s.get("kicker") or default_kicker(ctx.plan, s))
    if title:
        fill(slide, "Title", s.get("title"))
    _to_area(slide, p, "Kicker", "Title")
    if title and p.narrow:
        _two_line_title(ctx, slide)
    if p.kind == "full":
        _recolor(slide, "Title", "white")
    return slide


def _two_line_title(ctx: Ctx, slide) -> None:
    """Neben einem großen Videofeld darf der Titel zweizeilig sein: Kicker und Titel rücken nach oben,
    der Inhalt darunter bleibt, wo er ist."""
    title = _placeholder(slide, "Title")
    if title is None:
        return
    size = SIZE_PT["title"]
    width = title.width / EMU_PER_PX
    lines = len(ctx.m.wrap(title.text_frame.text, size, width))
    if lines != 2:
        return
    _place(title, y=108, h=2 * ctx.m.line_height_px(size) + 4)
    kicker = _placeholder(slide, "Kicker")
    if kicker is not None:
        _place(kicker, y=66)


def _points(slide, points: list[dict] | None) -> None:
    ph = _placeholder(slide, "Points")
    if ph is None:
        return
    if points:
        points_text(ph, points)
    else:
        ph._element.getparent().remove(ph._element)


def _focus(ctx: Ctx, slide, s: dict) -> None:
    focus = s["focus"]
    focus_box(slide, (1220, 330, 580), focus.get("label", "Clinical focus"), focus["title"],
              focus.get("text", ""), ctx.m)


# ---------------------------------------------------------------- Renderer

def render_cover(ctx: Ctx, s: dict) -> None:
    ep = ctx.plan["episode"]
    presenter = ep.get("presenter") or {}
    slide = new_slide(ctx, LAYOUT_BY_KEY["cover"])
    fill(slide, "Kicker", s.get("kicker") or f"Online Training · Episode {ep['number']:02d}")
    fill(slide, "Title", ep["title"])
    fill(slide, "Subtitle", ep.get("subtitle"))
    fill(slide, "Presenter", presenter.get("name"))
    fill(slide, "Credentials", presenter.get("credentials"))
    photo = _placeholder(slide, "Photo")   # das Videofeld zeichnet die Einblendung, randabfallend
    photo._element.getparent().remove(photo._element)
    _frame(ctx, slide, s, p=presenter_of(s))


def _set_box(shape, top_delta: int = 0, height_delta: int = 0, width: int | None = None) -> None:
    """Platzhalter verschieben/strecken; alle vier Werte setzen, sonst fehlen geerbte Maße im xfrm."""
    left, top, old_width, height = shape.left, shape.top, shape.width, shape.height
    shape.left, shape.top = left, top + top_delta
    shape.width, shape.height = old_width if width is None else width, height + height_delta


def _grow_chapter_title(ctx: Ctx, slide, text: str, p: Presenter = Presenter()) -> None:
    """Lange Kapitelnamen („Activate & Monitor“) brechen um: Titel wächst nach unten, der Satz rückt nach."""
    title = _placeholder(slide, "Title")
    level = CHAPTER_TITLE.levels[0]
    para = [Para(text, level["size_pt"], level.get("ln_spc_pct", 100))]
    width = title.width / EMU_PER_PX
    if ctx.m.block_height_px(para, width) <= title.height / EMU_PER_PX:
        return
    left = title.left / EMU_PER_PX
    if p.kind == "small" and p.box[0] > left:   # sonst reicht die Box ins Videofeld
        width = min(width, p.box[0] - left - 24)
    need = ctx.m.block_height_px(para, width)
    cap = 2 * ctx.m.line_height_px(level["size_pt"], level.get("ln_spc_pct", 100))
    if need > cap + 1 or ctx.m.long_words(text, level["size_pt"], width):
        ctx.report.warnings.append(f"Folie {ctx.report.slides}: Kapitelname „{text}“ passt nicht in zwei Zeilen "
                                   f"– kürzen oder trennen")
    extra = px(min(need, cap)) - title.height
    _set_box(title, height_delta=extra, width=px(width))
    line = _placeholder(slide, "Line")
    if line is not None:
        _set_box(line, top_delta=extra)


CHAPTER_STACK_NUMBER_PT = 240


def _stack_chapter(ctx: Ctx, slide, p: Presenter, title: str, line: str | None) -> None:
    """Kapitel neben einem großen Videofeld: Nummer, Kicker, Name und Satz übereinander, senkrecht zentriert."""
    m, x0, w = ctx.m, p.area[0], p.area_w
    level = CHAPTER_TITLE.levels[0]
    ln = level.get("ln_spc_pct", 100)
    size = level["size_pt"]
    if m.long_words(title, size, w - 12):      # „Document“ passt bei 85 pt nicht in die halbe Folie
        size = 72
    num_pt = CHAPTER_STACK_NUMBER_PT
    num_line = m.line_height_px(num_pt, 85)
    title_h = m.block_height_px([Para(title, size, ln)], w - 12)
    line_w = min(w, 720)
    line_h = m.block_height_px([Para(line, SIZE_PT["line"])], line_w) if line else 0
    digit = num_line * 0.62                      # sichtbare Ziffer ohne Ober- und Unterlänge
    total = digit + 44 + 40 + 6 + title_h + (24 + line_h if line else 0)
    top = max(40, (1080 - total) / 2)
    _place(_placeholder(slide, "Number"), x=x0 - 14, y=top - num_line * 0.2, w=min(w, 640), h=num_line)
    for run in _placeholder(slide, "Number").text_frame.paragraphs[0].runs:
        run.font.size = Pt(num_pt)
    y = top + digit + 44
    _place(_placeholder(slide, "Kicker"), x=x0, y=y, w=w, h=40)
    y += 46
    title_ph = _placeholder(slide, "Title")
    _place(title_ph, x=x0 - 6, y=y, w=w, h=title_h + 4)
    if size != level["size_pt"]:
        for para in title_ph.text_frame.paragraphs:
            for run in para.runs:
                run.font.size = Pt(size)
    if line:
        _place(_placeholder(slide, "Line"), x=x0, y=y + title_h + 24, w=line_w, h=line_h + 6)


def render_chapter(ctx: Ctx, s: dict) -> None:
    chapters = ctx.plan["episode"]["chapters"]
    n = s["chapter"]
    p = presenter_of(s)
    slide = new_slide(ctx, LAYOUT_BY_KEY["chapter"])
    fill(slide, "Number", str(n))
    fill(slide, "Kicker", s.get("kicker") or f"Phase {n} of {len(chapters)}")
    title = s.get("title") or chapters[n - 1]
    fill(slide, "Title", title)
    fill(slide, "Line", s.get("line"))
    if p.kind in ("full", "panel"):
        _stack_chapter(ctx, slide, p, title, s.get("line"))
    else:
        _grow_chapter_title(ctx, slide, title, p)
    _frame(ctx, slide, s, chapter=n, p=p)


def render_hook(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, title=False, p=p)
    quote = s["quote"].strip()
    if not quote.startswith(("“", '"')):
        quote = f"“{quote}”"
    fill(slide, "Quote", quote)
    fill(slide, "TruthLabel", s["truth"].get("label", "The hard truth"))
    fill(slide, "TruthText", s["truth"]["text"])
    fill(slide, "AnswerLabel", s["answer"].get("label", "The fläsh answer"))
    fill(slide, "AnswerText", s["answer"]["text"])
    _frame(ctx, slide, s, p=p)


def render_closing(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    closing_steps(slide, s["steps"])
    nxt = s["next"]
    fill(slide, "NextLabel", nxt.get("label", "Up next"))
    fill(slide, "NextTitle", nxt["title"])
    fill(slide, "NextText", nxt.get("text"))
    _frame(ctx, slide, s, p=p)


NARROW_POINT_GAP_PT = 15   # statt 22 pt zwischen den Punkten, wenn das Videofeld Platz nimmt


def render_points(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    _points(slide, s["points"])
    if s.get("focus"):
        ph = _placeholder(slide, "Points")
        _place(ph, w=900)
        _focus(ctx, slide, s)
    elif p.narrow and _placeholder(slide, "Points") is not None:
        # neben dem Videofeld: schmaler, dafür etwas höher und mit engerem Abstand zwischen den Punkten
        ph = _placeholder(slide, "Points")
        _place(ph, x=p.area[0], y=320, w=min(1260, p.area_w), h=560 if s.get("evidence") else 660)
        for para in ph.text_frame.paragraphs[1:]:
            if para.level == 0:
                para.space_before = Pt(NARROW_POINT_GAP_PT)
    _frame(ctx, slide, s, p=p)


def render_points_photo(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    _points(slide, s["points"])
    _photo(ctx, slide, "Photo", s["photo"])
    fill(slide, "Caption", s.get("caption"))
    _frame(ctx, slide, s, p=p)


def render_points_chart(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    _points(slide, s["points"])
    bars_card(slide, s["chart"])
    _frame(ctx, slide, s, p=p)


def render_statement(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, title=False, p=p)
    fill(slide, "Big", s.get("big"))
    fill(slide, "Statement", s.get("statement"))
    fill(slide, "Text", s.get("text"))
    _to_area(slide, p, "Big", "Statement", "Text")
    if p.kind == "full":   # helles Layout über dem Video: Schrift hell
        _recolor(slide, "Statement", "white")
        _recolor(slide, "Text", "on_dark")
    _frame(ctx, slide, s, p=p)


def render_checklist(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    checklist(slide, s["items"], w=900 if s.get("focus") else 1260)
    if s.get("focus"):
        _focus(ctx, slide, s)
    _frame(ctx, slide, s, p=p)


def render_steps(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    start = s.get("start", 1)
    if any("photo" in step for step in s["steps"]):
        for brief in photo_steps(slide, s["steps"], ctx.base_dir, ctx.report.warnings, start, s.get("caption")):
            ctx.report.briefs.append((ctx.report.slides, brief))
    else:
        area = (p.area[0], 330, min(1260, p.area_w), 560)
        steps_grid(slide, s["steps"], dark=False, start=start, area=area)
    _frame(ctx, slide, s, p=p)


def render_compare(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    compare_columns(slide, s["left"], s["right"], s.get("style", "do_dont"))
    _frame(ctx, slide, s, p=p)


def render_scale(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    x0, w = p.area[0], p.area_w
    if "scale" in s:
        scale_chips(slide, s["scale"]["items"], s["scale"].get("highlight", []), box=(x0, 330, min(1560, w), 140))
    else:
        timeline(slide, s["timeline"]["points"], box=(x0, 330, min(1260, w), 200))
    if s.get("caption"):
        scale_caption(slide, s["caption"], y=490 if "scale" in s else 510,  # unter zweizeiligen Zeitstrahl-Texten
                      x=x0, w=min(1260, w))
    _points(slide, s.get("points"))
    _to_area(slide, p, "Points")
    _frame(ctx, slide, s, p=p)


def render_summary(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    summary_items(slide, s["items"])
    _frame(ctx, slide, s, p=p)


def render_photo(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    _photo(ctx, slide, "Photo", s["photo"])
    fill(slide, "Caption", s.get("caption"))
    _frame(ctx, slide, s, p=p)


def render_before_after(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    _photo(ctx, slide, "PhotoBefore", s["before"]["photo"])
    _photo(ctx, slide, "PhotoAfter", s["after"]["photo"])
    fill(slide, "LabelBefore", s["before"]["label"])
    fill(slide, "LabelAfter", s["after"]["label"])
    _frame(ctx, slide, s, p=p)


def render_photo_annotated(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    ph = _placeholder(slide, "Photo")  # Maße aus der Vorlage, auch wenn das Layout verändert wurde
    box = tuple(v / EMU_PER_PX for v in (ph.left, ph.top, ph.width, ph.height))
    _photo(ctx, slide, "Photo", s["photo"])
    markers(slide, box, s["markers"])
    _frame(ctx, slide, s, p=p)


def render_case(ctx: Ctx, s: dict) -> None:
    p = presenter_of(s)
    slide = _start(ctx, s, p=p)
    fill(slide, "Story", s["story"])
    case_findings(slide, s["findings"])
    _frame(ctx, slide, s, p=p)


def render_quiz(ctx: Ctx, s: dict) -> None:
    for reveal in (False, True):
        p = presenter_of(s, "presenter_answer" if reveal else "presenter")
        slide = new_slide(ctx, LAYOUT_BY_KEY["quiz"])
        fill(slide, "Kicker", s.get("kicker") or ("Knowledge check · Answer" if reveal else "Knowledge check"))
        fill(slide, "Question", s["question"])
        _to_area(slide, p, "Kicker", "Question")
        if p.narrow:   # schmalere Frage bekommt Platz bis knapp über die Antworten
            _place(_placeholder(slide, "Question"), h=280)
        quiz_options(slide, s["options"], s["answer"] if reveal else None, s.get("explanation") if reveal else None,
                     x=p.area[0], w=min(1260, p.area_w))
        notes = dict(s)
        if reveal:
            notes["notes"] = s.get("explanation") or s.get("notes")
        _frame(ctx, slide, notes, p=p)


RENDERERS: dict[str, Callable[[Ctx, dict], None]] = {
    "cover": render_cover, "chapter": render_chapter, "hook": render_hook, "closing": render_closing,
    "points": render_points, "points_photo": render_points_photo, "points_chart": render_points_chart,
    "statement": render_statement, "checklist": render_checklist, "steps": render_steps,
    "compare": render_compare, "scale": render_scale, "summary": render_summary, "photo": render_photo,
    "before_after": render_before_after, "photo_annotated": render_photo_annotated, "case": render_case,
    "quiz": render_quiz,
}
