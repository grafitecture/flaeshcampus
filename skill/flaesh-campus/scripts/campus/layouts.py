"""Deklarative Definition der 18 Layouts (Maße in px auf dem 1920 × 1080-Raster)."""
from dataclasses import dataclass, field
from typing import Literal

from .tokens import COLOR, KICKER_SPC, LABEL_SPC, SIZE_PT

Box = tuple[float, float, float, float]


@dataclass
class PhDef:
    name: str
    ph_type: Literal["title", "body", "pic"]
    box: Box
    levels: list[dict]
    prompt: list[str]
    anchor: str = "t"
    geom: str = "rect"
    fill: str | None = None
    fill_alpha: int | None = None
    line: tuple | None = None          # (Farbe, Breite px)
    glow: tuple | None = None          # (Farbe, Radius px, Deckkraft %)
    insets: tuple[float, float, float, float] = (0, 0, 0, 0)


@dataclass
class DecorDef:
    kind: Literal["rect", "roundrect", "ellipse", "text", "image", "radial"]
    name: str
    box: Box
    style: dict = field(default_factory=dict)


@dataclass
class LayoutDef:
    name: str
    key: str
    frame: Literal["cover", "dark", "light", "full"]
    placeholders: list[PhDef]
    decor: list[DecorDef]


def lvl(size: str | float, color: str, **extra) -> dict:
    """Ebenen-Stil: Größe als SIZE_PT-Schlüssel oder pt-Zahl, Farbe als COLOR-Schlüssel."""
    size_pt = SIZE_PT[size] if isinstance(size, str) else size
    return {"size_pt": size_pt, "color": COLOR[color], **extra}


KICKER = lvl("kicker", "sky", caps=True, spc=KICKER_SPC)
LABEL_STEEL = lvl("label", "steel", caps=True, spc=LABEL_SPC)
LABEL_SKY = lvl("label", "sky", caps=True, spc=LABEL_SPC)
POINT_LEVELS = [
    lvl("lead", "slate", spc_before_pt=22, mar_l_px=80, indent_px=-80, tab_px=80),
    lvl("body", "ink", spc_before_pt=6, mar_l_px=80),
]
PIC_LEVELS = [lvl("small", "muted", align="center")]

EPISODE_PH = PhDef("Episode", "body", (0, 108, 150, 70), [lvl("rail_ep", "white", align="center")], ["00"])
KICKER_PH = PhDef("Kicker", "body", (240, 110, 1500, 40), [KICKER], ["Phase 1 · Chapter"])


def title_ph(dark: bool) -> PhDef:
    return PhDef("Title", "title", (240, 150, 1500, 100), [lvl("title", "white" if dark else "slate")],
                 ["Slide title"])


def points_ph(box: Box) -> PhDef:
    return PhDef("Points", "body", box, POINT_LEVELS, ["01\tPoint title", "Short explanation"])


def pic_ph(name: str, box: Box, **extra) -> PhDef:
    return PhDef(name, "pic", box, PIC_LEVELS, ["Insert photo"], anchor="ctr", **extra)


def text_ph(name: str, box: Box, size: str, color: str, prompt: str, **extra) -> PhDef:
    return PhDef(name, "body", box, [lvl(size, color)], [prompt], **extra)


def frame_decor(frame: str) -> list[DecorDef]:
    """Rahmen-Elemente je Rahmentyp (light, dark, cover, full)."""
    decor: list[DecorDef] = []
    if frame == "cover":
        decor += [
            DecorDef("radial", "glow-bg", (766, -220, 1520, 1520),
                     {"color": COLOR["sky"], "stops": [(0, 34), (50, 10), (100, 0)]}),
            DecorDef("ellipse", "arc-1", (1126, 140, 800, 800), {"line": (COLOR["sky"], 2, 28)}),
            DecorDef("ellipse", "arc-2", (1036, 50, 980, 980), {"line": (COLOR["sky"], 2, 14)}),
        ]
    rail_color = COLOR["night"] if frame == "light" else COLOR["rail"]
    decor.append(DecorDef("rect", "rail", (0, 0, 150, 1080), {"fill": rail_color}))
    decor.append(DecorDef("text", "rail-ep-label", (0, 84, 150, 30),
                          {"text": "EP", "level": {**LABEL_STEEL, "align": "center"}}))
    if frame == "cover":
        decor += [
            DecorDef("image", "cover-logo", (230, 96, 200, 85), {"file": "brand/logo-white.png"}),
            DecorDef("text", "cover-campus", (452, 108, 320, 80),
                     {"text": "Campus", "level": lvl(29, "sky"), "anchor": "b"}),
        ]
    else:
        decor.append(DecorDef("image", "rail-logo", (31, 960, 88, 37), {"file": "brand/logo-white.png"}))
    # Die Kreis-Zone (ZONE) bleibt für die Videoeinblendung frei, wird aber nicht mehr gezeichnet (Martin, 19.10.).
    return decor


def _card(name: str, box: Box, accent: bool) -> DecorDef:
    style = {"fill": COLOR["night2"], "radius_px": 18}
    if accent:
        style.update(line=(COLOR["sky"], 2), glow=(COLOR["sky"], 50, 40))
    return DecorDef("roundrect", name, box, style)


def _layout(name: str, key: str, frame: str, placeholders=(), decor=()) -> LayoutDef:
    return LayoutDef(name, key, frame, [EPISODE_PH, *placeholders], list(decor))


def _light(name: str, key: str, *extra: PhDef, title: bool = True) -> LayoutDef:
    head = [KICKER_PH, title_ph(False)] if title else [KICKER_PH]
    return _layout(name, key, "light", [*head, *extra])


_PHOTO_CARD = {"fill": COLOR["night"]}  # deckend und 2 px überlappend: ein Band ohne helle Fugen

LAYOUTS: list[LayoutDef] = [
    _layout("01 Title", "cover", "cover", [
        PhDef("Kicker", "body", (230, 356, 980, 40), [KICKER], ["Online Training · Episode 00"]),
        PhDef("Title", "title", (226, 404, 960, 230), [lvl("display", "white", ln_spc_pct=90)],
              ["Episode title"]),
        text_ph("Subtitle", (230, 654, 820, 110), "subtitle", "on_dark", "Subtitle of the episode"),
        text_ph("Presenter", (230, 876, 1000, 52), "lead", "white", "Dr. Germán Gómez"),
        text_ph("Credentials", (230, 930, 1000, 80), "small", "steel", "Credentials"),
        PhDef("Photo", "pic", (1236, 250, 580, 580), PIC_LEVELS, ["Insert portrait"], anchor="ctr",
              geom="ellipse", line=(COLOR["sky"], 6), glow=(COLOR["sky"], 90, 60)),
    ]),
    _layout("02 Chapter", "chapter", "dark", [
        PhDef("Number", "body", (230, 20, 560, 880),
              [lvl("chapter_number", "sky", ln_spc_pct=85, glow=(COLOR["sky"], 80, 65))], ["1"]),
        PhDef("Kicker", "body", (800, 330, 900, 40), [KICKER], ["Phase 1 of 5"]),
        PhDef("Title", "title", (792, 376, 1000, 180), [lvl("chapter_title", "white", ln_spc_pct=90)], ["Chapter"]),
        text_ph("Line", (800, 590, 700, 130), "line", "on_dark", "One sentence about this chapter."),
    ], decor=[
        DecorDef("radial", "glow-bg", (-60, -200, 1240, 1240),
                 {"color": COLOR["sky"], "stops": [(0, 26), (50, 8), (100, 0)], "behind": True}),
    ]),
    _layout("03 Hook", "hook", "dark", [
        KICKER_PH,
        text_ph("Quote", (240, 170, 1300, 300), "quote", "white", "The question your patient asks"),
        PhDef("TruthLabel", "body", (290, 560, 500, 30), [LABEL_STEEL], ["The hard truth"]),
        text_ph("TruthText", (290, 610, 500, 240), "body", "on_dark", "What really happens."),
        PhDef("AnswerLabel", "body", (930, 560, 520, 30), [LABEL_SKY], ["The fläsh answer"]),
        text_ph("AnswerText", (930, 610, 520, 240), "body", "white", "How the protocol solves it."),
    ], decor=[
        _card("truth-card", (240, 520, 600, 360), accent=False),
        _card("answer-card", (880, 520, 620, 360), accent=True),
    ]),
    _layout("04 Closing", "closing", "dark", [
        KICKER_PH, title_ph(True),
        PhDef("NextLabel", "body", (1230, 370, 520, 30), [LABEL_SKY], ["Up next"]),
        text_ph("NextTitle", (1230, 410, 520, 120), "lead", "white", "Episode 00 · Title"),
        text_ph("NextText", (1230, 540, 520, 110), "body", "on_dark", "What the next episode covers."),
    ], decor=[
        _card("next-card", (1180, 330, 620, 330), accent=True),
    ]),
    _light("05 Points", "points", points_ph((240, 330, 1260, 560))),
    _light("06 Points + Photo", "points_photo", points_ph((240, 330, 700, 560)),
           pic_ph("Photo", (1000, 300, 800, 400)),
           text_ph("Caption", (1000, 712, 540, 40), "small", "muted", "Photo caption")),
    _light("07 Points + Chart", "points_chart", points_ph((240, 330, 700, 560))),
    _light("08 Statement", "statement",
           PhDef("Big", "body", (240, 200, 1300, 330), [lvl("statement_big", "sky", ln_spc_pct=85)], ["30"]),
           text_ph("Statement", (240, 560, 1200, 150), "statement", "slate", "Statement in one or two lines"),
           text_ph("Text", (240, 730, 1200, 130), "body", "ink", "Supporting sentence."), title=False),
    _light("09 Checklist", "checklist"),
    _light("10 Steps", "steps"),
    _light("11 Compare", "compare"),
    _light("12 Scale", "scale", points_ph((240, 560, 1260, 330))),
    _light("13 Summary", "summary"),
    _layout("14 Photo", "photo", "full", [
        pic_ph("Photo", (150, 0, 1770, 1080)),
        PhDef("Kicker", "body", (190, 780, 1300, 62), [KICKER], ["Step by step"],
              insets=(40, 22, 40, 0), **_PHOTO_CARD),
        PhDef("Title", "title", (190, 840, 1300, 112), [lvl("title", "white")], ["Photo title"],
              insets=(40, 6, 40, 0), **_PHOTO_CARD),
        text_ph("Caption", (190, 950, 1300, 90), "body", "on_dark", "Caption", insets=(40, 0, 40, 18),
                **_PHOTO_CARD),
    ]),
    _light("15 Before / After", "before_after",
           pic_ph("PhotoBefore", (240, 330, 600, 400)), pic_ph("PhotoAfter", (900, 330, 600, 400)),
           text_ph("LabelBefore", (240, 750, 600, 40), "body", "slate", "Before"),
           text_ph("LabelAfter", (900, 750, 600, 40), "body", "slate", "After")),
    _light("16 Photo Annotated", "photo_annotated", pic_ph("Photo", (240, 300, 900, 600))),
    _light("17 Case", "case",
           text_ph("Story", (240, 330, 1260, 150), "lead", "slate", "The case in two or three sentences.")),
    _layout("18 Quiz", "quiz", "dark", [
        KICKER_PH,
        text_ph("Question", (240, 180, 1260, 220), "quote", "white", "Question?"),
    ]),
]
