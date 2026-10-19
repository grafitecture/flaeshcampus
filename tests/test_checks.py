import copy
import json
import shutil
import subprocess

import pytest
from pptx import Presentation
from pptx.util import Pt

from campus.build import build_deck
from campus.checks import check_deck
from campus.measure import Measurer
from campus.render import render_pdf
from campus.template import layout_spec
from campus.tokens import px
from conftest import REPO, SKILL

FIXTURE = REPO / "tests" / "fixtures" / "minimal-plan.json"


@pytest.fixture(scope="module")
def m(font_path):
    return Measurer(font_path)


@pytest.fixture
def plan():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def build(plan, template_path, tmp_path, name="deck.pptx"):
    out = tmp_path / name
    build_deck(plan, template_path, out, SKILL / "examples")
    return out


def kinds(issues, kind):
    return [i for i in issues if i.kind == kind]


def test_clean_minimal(plan, template_path, tmp_path, m):
    issues = check_deck(build(plan, template_path, tmp_path), layout_spec(), m)
    assert issues == []


def test_zone_violation(plan, template_path, tmp_path, m):
    path = build(plan, template_path, tmp_path)
    prs = Presentation(path)
    tb = prs.slides[2].shapes.add_textbox(px(1600), px(800), px(200), px(60))
    tb.name = "intruder"
    run = tb.text_frame.paragraphs[0].add_run()
    run.text = "x"
    run.font.name = "Corporate S"
    prs.save(path)
    zone = kinds(check_deck(path, layout_spec(), m), "zone")
    assert [(i.slide, i.shape) for i in zone] == [(3, "intruder")]


def test_overflow(plan, template_path, tmp_path, m):
    long_text = ("Light intensity falls with the square of distance so one centimetre of extra gap between "
                 "lamp and teeth costs roughly half of the available light power at the enamel surface")
    plan["slides"][2]["points"] = [{"lead": f"Point {i}", "text": long_text} for i in range(4)]
    issues = check_deck(build(plan, template_path, tmp_path), layout_spec(), m)
    assert any(i.kind == "overflow" and i.slide == 3 and i.shape == "Points" for i in issues)


def test_glyph(plan, template_path, tmp_path, m):
    plan["slides"][2]["title"] = "Do → Don't ✓"
    issues = check_deck(build(plan, template_path, tmp_path), layout_spec(), m)
    glyphs = kinds(issues, "glyph")
    assert glyphs and "→" in glyphs[0].detail and "✓" in glyphs[0].detail


def test_font(plan, template_path, tmp_path, m):
    path = build(plan, template_path, tmp_path)
    prs = Presentation(path)
    tb = prs.slides[2].shapes.add_textbox(px(240), px(880), px(400), px(40))
    run = tb.text_frame.paragraphs[0].add_run()
    run.text = "Arial text"
    run.font.name = "Arial"
    run.font.size = Pt(13)
    prs.save(path)
    assert kinds(check_deck(path, layout_spec(), m), "font")


@pytest.mark.slow
def test_render_pages(plan, template_path, tmp_path):
    if not shutil.which("pdfinfo"):
        pytest.skip("pdfinfo missing")
    path = build(plan, template_path, tmp_path)
    pdf = render_pdf(path, tmp_path / "render")
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages = int(next(line.split()[-1] for line in info.splitlines() if line.startswith("Pages:")))
    assert pages == len(Presentation(path).slides)


def test_check_cli(plan, template_path, tmp_path):
    import sys

    path = build(plan, template_path, tmp_path)
    cli = [sys.executable, str(SKILL / "scripts" / "check_deck.py"), str(path)]
    ok = subprocess.run(cli, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    prs = Presentation(path)
    tb = prs.slides[2].shapes.add_textbox(px(1600), px(800), px(200), px(60))
    tb.name = "intruder"
    tb.text_frame.paragraphs[0].add_run().text = "x"
    prs.save(path)
    bad = subprocess.run(cli, capture_output=True, text=True)
    assert bad.returncode == 1
    assert "slide 3 zone intruder" in bad.stdout
