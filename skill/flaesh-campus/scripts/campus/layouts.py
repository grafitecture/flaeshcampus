"""Deklarative Definition der 18 Layouts (Maße in px auf dem 1920 × 1080-Raster)."""
from dataclasses import dataclass, field
from typing import Literal

from .tokens import COLOR, KICKER_SPC, LABEL_SPC, SIZE_PT, ZONE

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

EPISODE_PH = PhDef("Episode", "body", (0, 108, 150, 70), [lvl("rail_ep", "white", align="center")], ["00"])
KICKER_PH = PhDef("Kicker", "body", (240, 110, 1500, 40), [KICKER], ["Phase 1 · Chapter"])


def title_ph(dark: bool) -> PhDef:
    return PhDef("Title", "title", (240, 150, 1500, 100), [lvl("title", "white" if dark else "slate")],
                 ["Slide title"])


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
    if frame == "light":
        decor.append(DecorDef("ellipse", "zone-ring", ZONE,
                              {"fill": COLOR["white"], "line": (COLOR["sky"], 4), "glow": (COLOR["sky"], 46, 45)}))
    elif frame == "dark":
        decor.append(DecorDef("ellipse", "zone-ring", ZONE,
                              {"fill": COLOR["ring_dark"], "line": (COLOR["sky"], 4), "glow": (COLOR["sky"], 60, 55)}))
    return decor


def _card(name: str, box: Box, accent: bool) -> DecorDef:
    style = {"fill": COLOR["night2"], "radius_px": 18}
    if accent:
        style.update(line=(COLOR["sky"], 2), glow=(COLOR["sky"], 50, 40))
    return DecorDef("roundrect", name, box, style)


def _layout(name: str, key: str, frame: str, placeholders=(), decor=()) -> LayoutDef:
    return LayoutDef(name, key, frame, [EPISODE_PH, *placeholders], list(decor))


def _light(name: str, key: str, *extra: PhDef) -> LayoutDef:
    return _layout(name, key, "light", [KICKER_PH, title_ph(False), *extra])


LAYOUTS: list[LayoutDef] = [
    _layout("01 Title", "cover", "cover"),
    _layout("02 Chapter", "chapter", "dark", decor=[
        DecorDef("radial", "glow-bg", (-60, -200, 1240, 1240),
                 {"color": COLOR["sky"], "stops": [(0, 26), (50, 8), (100, 0)], "behind": True}),
    ]),
    _layout("03 Hook", "hook", "dark", [KICKER_PH], decor=[
        _card("truth-card", (240, 520, 600, 360), accent=False),
        _card("answer-card", (880, 520, 620, 360), accent=True),
    ]),
    _layout("04 Closing", "closing", "dark", [KICKER_PH, title_ph(True)], decor=[
        _card("next-card", (1180, 330, 620, 330), accent=True),
    ]),
    _light("05 Points", "points"),
    _light("06 Points + Photo", "points_photo"),
    _light("07 Points + Chart", "points_chart"),
    _light("08 Statement", "statement"),
    _light("09 Checklist", "checklist"),
    _light("10 Steps", "steps"),
    _light("11 Compare", "compare"),
    _light("12 Scale", "scale"),
    _light("13 Summary", "summary"),
    _layout("14 Photo", "photo", "full"),
    _light("15 Before / After", "before_after"),
    _light("16 Photo Annotated", "photo_annotated"),
    _light("17 Case", "case"),
    _layout("18 Quiz", "quiz", "dark", [KICKER_PH]),
]
