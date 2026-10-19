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
