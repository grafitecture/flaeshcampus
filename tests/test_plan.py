import copy
import json

import pytest

from campus.plan import PlanError, default_kicker, load_plan, validate_plan
from conftest import REPO

FIXTURE = REPO / "tests" / "fixtures" / "minimal-plan.json"


@pytest.fixture
def plan():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_minimal_ok(plan):
    assert validate_plan(plan) == []
    assert load_plan(FIXTURE)["episode"]["number"] == 2


def test_unknown_type(plan):
    plan["slides"].append({"type": "bullets"})
    errors = validate_plan(plan)
    assert any("unknown type 'bullets'" in e for e in errors)
    assert errors[0].startswith("slide 5 (bullets): ")


def test_points_bounds(plan):
    plan["slides"][2]["points"] = [{"lead": f"Point {i}", "text": "Text"} for i in range(5)]
    assert any("points: 2–4 items" in e for e in validate_plan(plan))


def test_scale_points_bound(plan):
    """Unter Skala oder Zeitstrahl passen höchstens zwei Punkte (Platzhalter 330 px hoch)."""
    points = [{"lead": f"Point {i}", "text": "Text"} for i in range(3)]
    plan["slides"].append({"type": "scale", "title": "Shade guide", "scale": {"items": ["B1", "A1"]}, "points": points})
    assert any("slide 5 (scale): points: 1–2 items" in e for e in validate_plan(plan))
    plan["slides"][-1]["points"] = points[:2]
    assert validate_plan(plan) == []


def _slide(plan, n):
    return plan["slides"][n - 1]


CHART = {"type": "points_chart", "title": "Chart", "points": [{"lead": "a", "text": "b"}, {"lead": "c", "text": "d"}],
         "chart": {"bars": [{"label": "Docked", "value": 100}, {"label": "Gap", "value": 56}]}}
TYPE_SLIPS = [
    (lambda p: _slide(p, 3).update(notes=["a", "b"]), "slide 3 (points): 'notes' must be text"),
    (lambda p: _slide(p, 3).update(evidence=2004), "slide 3 (points): 'evidence' must be text"),
    (lambda p: _slide(p, 3)["points"][0].update(lead=7), "slide 3 (points): points[1] 'lead' must be text"),
    (lambda p: _slide(p, 3).update(focus={"title": 5, "text": "x"}), "slide 3 (points): focus 'title' must be text"),
    (lambda p: _slide(p, 4).update(explanation=["a"]), "slide 4 (quiz): 'explanation' must be text"),
    (lambda p: p["episode"].update(title=7), "episode: 'title' must be text"),
    (lambda p: p["episode"].update(presenter="Dr. X"), "episode: 'presenter' must be an object"),
    (lambda p: p["episode"]["presenter"].update(photo={"file": 5}), "episode: presenter.photo 'file' must be text"),
    (lambda p: p["slides"].append({**CHART, "chart": {"bars": [{"label": "a", "value": 1, "display": 10},
                                                                {"label": "b", "value": 2}]}}),
     "slide 5 (points_chart): chart.bars[1] 'display' must be text"),
    (lambda p: p["slides"].append({"type": "scale", "title": "Shades", "scale": "B1 A1"}),
     "slide 5 (scale): 'scale' must be an object"),
    (lambda p: p["slides"].append({"type": "scale", "title": "Shades", "scale": {"items": ["A3", "A3.5"],
                                                                                 "highlight": "A3"}}),
     "slide 5 (scale): scale.highlight must be a list of texts"),
    (lambda p: p["slides"].append({"type": "photo_annotated", "title": "Setup", "photo": {"brief": "x"},
                                   "markers": [{"x": 0.5, "y": 0.5, "label": 3}]}),
     "slide 5 (photo_annotated): markers[1] 'label' must be text"),
    (lambda p: p["slides"].append({"type": "steps", "title": "Fix", "steps": [{"title": 4, "text": "x"}] * 3}),
     "slide 5 (steps): steps[1] 'title' must be text"),
    (lambda p: p["slides"].append({"type": "photo", "title": "Prepare", "photo": {"brief": "x"},
                                   "evidence": "Li & Greenwall, Br Dent J 2013"}),
     "slide 5 (photo): 'evidence' is not shown on photo slides — put the source into the caption"),
]


PHOTO_STEPS = {"type": "steps", "title": "Apply & Activate", "start": 6, "caption": "Repeat 3× (max 4×).",
               "steps": [{"title": "Apply the gel", "photo": {"file": "a.jpg"}},
                         {"title": "Dock the lamp", "photo": {"brief": "Lamp docked", "fit": False}}]}
TYPE_SLIPS += [
    (lambda p: p["slides"].append({**PHOTO_STEPS, "steps": [{"title": "a", "photo": {"brief": "x"}},
                                                            {"title": "b", "text": "c"}]}),
     "slide 5 (steps): give every step a photo, or none"),
    (lambda p: p["slides"].append({**PHOTO_STEPS, "steps": [{"title": f"s{i}", "photo": {"brief": "x"}}
                                                            for i in range(5)]}),
     "slide 5 (steps): steps: 2–4 items"),
    (lambda p: p["slides"].append({"type": "steps", "title": "Fix", "caption": "x",
                                   "steps": [{"title": "a", "text": "b"}] * 3}),
     "slide 5 (steps): 'caption' needs step photos"),
    (lambda p: p["slides"].append({**PHOTO_STEPS, "steps": [{"title": "a", "photo": {"brief": "x", "fit": "yes"}},
                                                            {"title": "b", "photo": {"brief": "y"}}]}),
     "slide 5 (steps): steps[1].photo 'fit' must be true or false"),
    (lambda p: p["slides"].append({**PHOTO_STEPS, "start": 0}),
     "slide 5 (steps): 'start' must be a whole number from 1"),
    (lambda p: p["slides"].append({**PHOTO_STEPS, "steps": [{"title": "a", "text": "b", "photo": {"brief": "x"}},
                                                            {"title": "c", "photo": {"brief": "y"}}]}),
     "slide 5 (steps): steps[1] 'text' is not shown with photos — use the caption or notes"),
]


def test_photo_steps_valid(plan):
    plan["slides"].append(PHOTO_STEPS)
    assert validate_plan(plan) == []


@pytest.mark.parametrize("mutate,expected", TYPE_SLIPS)
def test_type_slips_reported(plan, mutate, expected):
    """Falsche Feldtypen ergeben eine klare Meldung je Folie statt eines Absturzes beim Bauen."""
    mutate(plan)
    assert expected in validate_plan(plan)


def test_chapter_range(plan):
    plan["slides"][2]["chapter"] = 6
    assert any("chapter 6 out of range 1–5" in e for e in validate_plan(plan))


def test_quiz_answer(plan):
    plan["slides"][3]["answer"] = 3
    assert any("answer must be 0–2" in e for e in validate_plan(plan))


def test_photo_object(plan):
    plan["slides"].append({"type": "photo", "title": "Prepare & Protect", "photo": {}})
    assert any("photo needs 'file' or 'brief'" in e for e in validate_plan(plan))


def test_collects_all(plan):
    broken = copy.deepcopy(plan)
    broken["slides"][2]["chapter"] = 9
    broken["slides"][3]["answer"] = 5
    broken["slides"].append({"type": "bullets"})
    assert len(validate_plan(broken)) == 3


def test_load_plan_raises(tmp_path, plan):
    plan["slides"].append({"type": "bullets"})
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(PlanError) as exc:
        load_plan(path)
    assert any("unknown type" in e for e in exc.value.errors)


def test_default_kicker(plan):
    assert default_kicker(plan, {"type": "points", "chapter": 3}) == "Phase 3 · Apply"
    assert default_kicker(plan, {"type": "points"}) is None


def test_closing_needs_next(plan):
    plan["slides"].append({"type": "closing", "title": "Make it your team's reflex",
                           "steps": [{"title": "Run one dry run", "text": "No patient in the chair."}]})
    assert any("missing 'next'" in e for e in validate_plan(plan))
