"""XML-Ergänzungen, die python-pptx nicht direkt anbietet.

Alle Änderungen laufen über lxml auf `shape._element` und halten die
Schema-Reihenfolge von DrawingML ein.
"""
from typing import Literal

from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement

from .tokens import FONT, px

_GEOM = ("a:xfrm", "a:custGeom", "a:prstGeom")
_FILLS = ("a:noFill", "a:solidFill", "a:gradFill", "a:blipFill", "a:pattFill", "a:grpFill")
_RPR_BEFORE_EFFECT = ("a:ln",) + _FILLS


def _clr(color: str, alpha_pct: int | None = None):
    clr = OxmlElement("a:srgbClr")
    clr.set("val", color)
    if alpha_pct is not None:
        alpha = OxmlElement("a:alpha")
        alpha.set("val", str(int(alpha_pct * 1000)))
        clr.append(alpha)
    return clr


def _insert_after(parent, child, predecessors: tuple[str, ...]) -> None:
    """Fügt `child` hinter dem letzten vorhandenen Vorgänger ein (sonst an den Anfang)."""
    tags = {qn(t) for t in predecessors}
    last = None
    for el in parent:
        if el.tag in tags:
            last = el
    if last is None:
        parent.insert(0, child)
    else:
        last.addnext(child)


def _glow(color: str, radius_px: float, alpha_pct: int):
    glow = OxmlElement("a:glow")
    glow.set("rad", str(px(radius_px)))
    glow.append(_clr(color, alpha_pct))
    return glow


def add_glow(shape, color: str, radius_px: float, alpha_pct: int) -> None:
    spPr = shape._element.spPr
    for old in spPr.findall(qn("a:effectLst")):
        spPr.remove(old)
    eff = OxmlElement("a:effectLst")
    eff.append(_glow(color, radius_px, alpha_pct))
    _insert_after(spPr, eff, _GEOM + _FILLS + ("a:ln",))


def _set_alpha(clr, alpha_pct: int) -> None:
    for old in clr.findall(qn("a:alpha")):
        clr.remove(old)
    alpha = OxmlElement("a:alpha")
    alpha.set("val", str(int(alpha_pct * 1000)))
    clr.append(alpha)


def set_fill_alpha(shape, alpha_pct: int) -> None:
    clr = shape._element.spPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    _set_alpha(clr, alpha_pct)


def set_line_alpha(shape, alpha_pct: int) -> None:
    clr = shape._element.spPr.find(qn("a:ln")).find(qn("a:solidFill")).find(qn("a:srgbClr"))
    _set_alpha(clr, alpha_pct)


def set_radial_fill(shape, color: str, stops: list[tuple[int, int]]) -> None:
    spPr = shape._element.spPr
    for tag in _FILLS:
        for old in spPr.findall(qn(tag)):
            spPr.remove(old)
    grad = OxmlElement("a:gradFill")
    grad.set("rotWithShape", "1")
    gs_lst = OxmlElement("a:gsLst")
    for pos, alpha in stops:
        gs = OxmlElement("a:gs")
        gs.set("pos", str(int(pos * 1000)))
        gs.append(_clr(color, alpha))
        gs_lst.append(gs)
    grad.append(gs_lst)
    path = OxmlElement("a:path")
    path.set("path", "circle")
    rect = OxmlElement("a:fillToRect")
    for side in ("l", "t", "r", "b"):
        rect.set(side, "50000")
    path.append(rect)
    grad.append(path)
    _insert_after(spPr, grad, _GEOM)


def add_text_glow(rpr_el, color: str, radius_px: float, alpha_pct: int) -> None:
    for old in rpr_el.findall(qn("a:effectLst")):
        rpr_el.remove(old)
    eff = OxmlElement("a:effectLst")
    eff.append(_glow(color, radius_px, alpha_pct))
    _insert_after(rpr_el, eff, _RPR_BEFORE_EFFECT)


def _def_rpr(style: dict):
    d = OxmlElement("a:defRPr")
    d.set("sz", str(int(round(style["size_pt"] * 100))))
    d.set("b", "0")
    d.set("i", "0")
    if style.get("caps"):
        d.set("cap", "all")
    if style.get("spc"):
        d.set("spc", str(int(style["spc"])))
    fill = OxmlElement("a:solidFill")
    fill.append(_clr(style["color"]))
    d.append(fill)
    if style.get("glow"):
        color, radius, alpha = style["glow"]
        eff = OxmlElement("a:effectLst")
        eff.append(_glow(color, radius, alpha))
        d.append(eff)
    for tag in ("a:latin", "a:ea", "a:cs"):
        font = OxmlElement(tag)
        font.set("typeface", FONT)
        d.append(font)
    return d


def _spacing(tag: str, pts: float):
    el = OxmlElement(tag)
    spc = OxmlElement("a:spcPts")
    spc.set("val", str(int(round(pts * 100))))
    el.append(spc)
    return el


def level_ppr(level: int, style: dict):
    """`a:lvlNpPr` (N = level + 1) aus einem Ebenen-Stil."""
    p = OxmlElement(f"a:lvl{level + 1}pPr")
    p.set("marL", str(px(style.get("mar_l_px", 0))))
    p.set("indent", str(px(style.get("indent_px", 0))))
    p.set("algn", {"left": "l", "center": "ctr", "right": "r"}[style.get("align", "left")])
    if style.get("ln_spc_pct"):
        ln = OxmlElement("a:lnSpc")
        pct = OxmlElement("a:spcPct")
        pct.set("val", str(int(style["ln_spc_pct"] * 1000)))
        ln.append(pct)
        p.append(ln)
    p.append(_spacing("a:spcBef", style.get("spc_before_pt", 0)))
    p.append(_spacing("a:spcAft", style.get("spc_after_pt", 0)))
    p.append(OxmlElement("a:buNone"))
    if style.get("tab_px"):
        tabs = OxmlElement("a:tabLst")
        tab = OxmlElement("a:tab")
        tab.set("pos", str(px(style["tab_px"])))
        tab.set("algn", "l")
        tabs.append(tab)
        p.append(tabs)
    p.append(_def_rpr(style))
    return p


def to_placeholder(
    shape,
    ph_type: Literal["title", "body", "pic"],
    idx: int | None,
    name: str,
    levels: list[dict],
    prompt: list[str],
    anchor: str = "t",
    insets_px=(0, 0, 0, 0),
    geom: str = "rect",
) -> None:
    sp = shape._element
    sp.nvSpPr.cNvPr.set("name", name)

    cNvSpPr = sp.nvSpPr.cNvSpPr
    cNvSpPr.attrib.pop("txBox", None)
    for old in cNvSpPr.findall(qn("a:spLocks")):
        cNvSpPr.remove(old)
    locks = OxmlElement("a:spLocks")
    locks.set("noGrp", "1")
    cNvSpPr.insert(0, locks)

    nvPr = sp.nvSpPr.nvPr
    for old in nvPr.findall(qn("p:ph")):
        nvPr.remove(old)
    ph = OxmlElement("p:ph")
    ph.set("type", ph_type)
    if idx is not None and ph_type != "title":
        ph.set("idx", str(idx))
    ph.set("hasCustomPrompt", "1")
    nvPr.insert(0, ph)

    style_el = sp.find(qn("p:style"))
    if style_el is not None:
        sp.remove(style_el)

    spPr = sp.spPr
    prst = spPr.find(qn("a:prstGeom"))
    if prst is None:
        prst = OxmlElement("a:prstGeom")
        _insert_after(spPr, prst, ("a:xfrm",))
    prst.set("prst", geom)
    if prst.find(qn("a:avLst")) is None:
        prst.append(OxmlElement("a:avLst"))

    txBody = sp.find(qn("p:txBody"))
    if txBody is None:
        txBody = OxmlElement("p:txBody")
        sp.append(txBody)
    for child in list(txBody):
        txBody.remove(child)

    body_pr = OxmlElement("a:bodyPr")
    body_pr.set("wrap", "square")
    for attr, value in zip(("lIns", "tIns", "rIns", "bIns"), insets_px):
        body_pr.set(attr, str(px(value)))
    body_pr.set("anchor", {"t": "t", "ctr": "ctr", "b": "b"}[anchor])
    body_pr.append(OxmlElement("a:noAutofit"))
    txBody.append(body_pr)

    lst = OxmlElement("a:lstStyle")
    for level, style in enumerate(levels):
        lst.append(level_ppr(level, style))
    txBody.append(lst)

    for level, text in enumerate(prompt):
        p = OxmlElement("a:p")
        if level:
            ppr = OxmlElement("a:pPr")
            ppr.set("lvl", str(level))
            p.append(ppr)
        r = OxmlElement("a:r")
        rpr = OxmlElement("a:rPr")
        rpr.set("lang", "en-US")
        rpr.set("dirty", "0")
        r.append(rpr)
        t = OxmlElement("a:t")
        t.text = text
        r.append(t)
        p.append(r)
        txBody.append(p)
