"""Einblendung von Dr. Gómez: Plan-Angaben, Geometrie, Standbild, Zeichnen, Untertitel (Martin, 02.11.)."""
import copy
import json

import pytest
from PIL import Image
from pptx import Presentation
from pptx.oxml.ns import qn

from campus.build import build_deck
from campus.plan import validate_plan
from campus.presenter import CONTENT, FULL_AREA, resolve, still_image
from campus.tokens import PH_IDX, px
from conftest import REPO, SKILL

FIXTURE = REPO / "tests" / "fixtures" / "minimal-plan.json"
PORTRAIT = SKILL / "examples" / "photos" / "gomez.jpg"


@pytest.fixture
def plan():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- Plan

@pytest.mark.parametrize("spec, error", [
    ({"mode": "corner"}, "presenter mode must be one of"),
    ("full", "'presenter' must be an object"),
    ({"mode": "small", "at": "top_left"}, "presenter at must be one of: top_right, bottom_right"),
    ({"mode": "small", "box": [1700, 900, 480]}, "presenter box must lie on the slide"),
    ({"mode": "small", "box": [100, 100, 200]}, "width at least 320"),
    ({"mode": "small", "box": [100, 100]}, "presenter box must be [x, y, width]"),
    ({"mode": "half_left", "at": "top_right"}, "'box' and 'at' need mode 'small'"),
    ({"mode": "none", "caption": "Hello"}, "caption needs a presenter on the slide"),
    ({"mode": "full", "caption": 5}, "presenter 'caption' must be text"),
])
def test_plan_presenter_errors(plan, spec, error):
    plan["slides"][2]["presenter"] = spec
    errors = validate_plan(plan)
    assert any(e.startswith("slide 3 (points): ") and error in e for e in errors), errors


def test_plan_presenter_rules_per_type(plan):
    plan["slides"][0]["presenter"] = {"mode": "half_left"}
    plan["slides"][2]["presenter_answer"] = {"mode": "full"}
    plan["slides"].append({"type": "photo", "title": "Photo", "photo": {"brief": "Lamp"}, "presenter": {"mode": "full"}})
    errors = validate_plan(plan)
    assert "slide 1 (cover): presenter mode on the cover must be 'third_right' or 'half_right'" in errors
    assert "slide 3 (points): 'presenter_answer' only on quiz slides" in errors
    assert "slide 5 (photo): presenter mode 'full' would hide the photo" in errors


def test_plan_presenter_ok(plan):
    plan["slides"][1]["presenter"] = {"mode": "full", "caption": "Prophylaxis first."}
    plan["slides"][2]["presenter"] = {"mode": "small", "box": [1380, 40, 480]}
    plan["slides"][3]["presenter_answer"] = {"mode": "third_right"}
    assert validate_plan(plan) == []


# ---------------------------------------------------------------- Geometrie

def test_resolve_geometry():
    assert resolve(None).kind == "none" and resolve(None).box is None
    assert resolve({"mode": "full"}).box == (0, 0, 1920, 1080) and resolve({"mode": "full"}).area == FULL_AREA
    assert resolve({"mode": "half_right"}).box == (960, 0, 960, 1080)
    assert resolve({"mode": "half_right"}).area == (240, 890)
    assert resolve({"mode": "third_left"}).box == (150, 0, 640, 1080)   # rechts neben der Leiste
    assert resolve({"mode": "third_left"}).area == (860, 1820)
    small = resolve({"mode": "small", "box": [1100, 626, 400]})
    assert small.box == (1100, 626, 400, 225) and small.area == CONTENT and not small.narrow
    assert resolve({"mode": "small"}).box == (1384, 754, 480, 270)       # Standard: unten rechts


@pytest.mark.parametrize("kind, size", [("full", (1920, 1080)), ("panel", (640, 1080)), ("small", (480, 270))])
def test_still_image(kind, size):
    """Standbild füllt jedes Seitenverhältnis: Porträt auf erweitertem Hintergrund, kein Rand."""
    path = still_image(str(PORTRAIT), *size, kind)
    with Image.open(path) as im:
        assert im.size == size
        corner = im.convert("RGB").getpixel((2, 2))
    assert all(abs(a - b) < 12 for a, b in zip(corner, (170, 183, 191)))   # Hintergrundfarbe des Porträts


# ---------------------------------------------------------------- Zeichnen

EPISODE = {"number": 2, "title": "In-Office Whitening Workflow",
           "presenter": {"name": "Dr. Germán Gómez", "photo": {"file": "photos/gomez.jpg"}},
           "chapters": ["Document", "Protect", "Apply", "Activate & Monitor", "Seal & Instruct"]}
POINTS = [{"lead": "Lock the geometry", "text": "Patient at 45°, lamp docked on the retractor."},
          {"lead": "Light, not heat", "text": "Blue 460 nm light activates the green gel."}]


def _build(template_path, tmp_path, slides):
    out = tmp_path / "presenter.pptx"
    report = build_deck({"episode": copy.deepcopy(EPISODE), "slides": slides}, template_path, out, SKILL / "examples")
    return Presentation(out), report


def test_full_mode(template_path, tmp_path):
    """Vollbild: Video und Verlauf ganz hinten, keine Leiste, Logo unten links, Untertitel unter ihm."""
    prs, report = _build(template_path, tmp_path, [
        {"type": "chapter", "chapter": 1, "line": "Whitening never begins on an uncleaned tooth.",
         "presenter": {"mode": "full", "caption": "Prophylaxis first."}}])
    slide = prs.slides[0]
    names = [s.name for s in slide.shapes]
    assert names[:2] == ["presenter-video", "presenter-shade"]
    assert names[-2:] == ["presenter-caption-box", "presenter-caption"]
    assert "presenter-logo" in names
    assert not [n for n in names if n.startswith("rail-")]
    assert PH_IDX["Episode"] not in [ph.placeholder_format.idx for ph in slide.placeholders]
    shade = slide.shapes[1]._element.spPr.find(qn("a:gradFill"))
    assert shade is not None and shade.find(qn("a:lin")) is not None
    caption = next(s for s in slide.shapes if s.name == "presenter-caption-box")
    assert caption.left >= px(1040)          # rechts neben der Textspalte
    assert report.presenter[0]["mode"] == "full"


def test_panel_moves_content(template_path, tmp_path):
    """Drittel links: Titel und Punkte rücken rechts neben das Videofeld, die Kante leuchtet."""
    prs, _ = _build(template_path, tmp_path, [
        {"type": "points", "title": "The lamp", "points": POINTS, "presenter": {"mode": "third_left"}}])
    slide = prs.slides[0]
    title = next(ph for ph in slide.placeholders if ph.placeholder_format.idx == 0)
    points = next(ph for ph in slide.placeholders if ph.placeholder_format.idx == PH_IDX["Points"])
    assert title.left == points.left == px(860)
    assert points.left + points.width <= px(1820)
    edge = next(s for s in slide.shapes if s.name == "presenter-edge")
    assert edge.left == px(150 + 640 - 2)


def test_small_frame_rounded_with_glow(template_path, tmp_path):
    prs, _ = _build(template_path, tmp_path, [
        {"type": "points", "title": "The lamp", "points": POINTS, "presenter": {"mode": "small", "at": "top_right"}}])
    slide = prs.slides[0]
    video = next(s for s in slide.shapes if s.name == "presenter-video")
    assert (video.left, video.top, video.width, video.height) == tuple(px(v) for v in (1384, 40, 480, 270))
    sp_pr = video._element.spPr
    assert sp_pr.find(qn("a:prstGeom")).get("prst") == "roundRect"
    assert sp_pr.find(qn("a:effectLst")).find(qn("a:glow")) is not None
    title = next(ph for ph in slide.placeholders if ph.placeholder_format.idx == 0)
    assert title.left + title.width <= px(1384 - 40)   # Titel endet vor dem Videofeld


def test_long_caption_warns(template_path, tmp_path):
    long = "A rather long sentence that cannot possibly fit into two lines of a small presenter field at all."
    _, report = _build(template_path, tmp_path, [
        {"type": "points", "title": "The lamp", "points": POINTS,
         "presenter": {"mode": "small", "at": "top_right", "caption": long}}])
    assert report.warnings == ["Folie 1: Untertitel länger als 2 Zeilen – kürzen"]


def test_episode_02_plan_varies_presenter():
    """Episode 2 zeigt alle Einblendungen, nicht immer dieselbe Ecke."""
    plan = json.loads((SKILL / "examples" / "episode-02.json").read_text(encoding="utf-8"))
    assert validate_plan(plan) == []
    modes = {s["presenter"]["mode"] for s in plan["slides"]}
    assert modes == {"none", "full", "half_left", "half_right", "third_left", "third_right", "small"}
    assert sum(1 for s in plan["slides"] if s["presenter"].get("caption")) >= 5
