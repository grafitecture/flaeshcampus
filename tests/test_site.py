import json
import sys

from conftest import REPO, SKILL

sys.path.insert(0, str(REPO / "scripts" / "tools"))

from campus.build import build_deck  # noqa: E402
from build_site import download_sources, slide_records, write_index  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "minimal-plan.json"


def test_slide_records(template_path, tmp_path):
    """Je Folie: Nummer, Titel, Kicker, aktives Kapitel aus der Leiste und Sprechertext."""
    plan = json.loads(FIXTURE.read_text(encoding="utf-8"))
    deck = tmp_path / "deck.pptx"
    build_deck(plan, template_path, deck, SKILL / "examples")
    records = slide_records(deck)
    assert [r["n"] for r in records] == [1, 2, 3, 4, 5]
    assert records[0]["title"] == "In-Office Whitening Workflow"
    assert records[1]["chapter"] == 3 and records[1]["title"] == "Apply"
    assert records[2]["kicker"] == "Phase 3 · Apply"
    assert records[2]["notes"] == "Light intensity falls with the square of distance."
    assert records[0]["chapter"] is None


def test_write_index(tmp_path):
    """Die Seite listet alle Folien und Downloads und bleibt aus Suchmaschinen heraus."""
    slides = [{"n": i, "title": f"Slide {i}", "kicker": "", "chapter": None, "notes": "",
               "src": f"slides/ep02/{i:02d}.jpg", "thumb": f"slides/ep02/thumb/{i:02d}.jpg"} for i in (1, 2)]
    layouts = [{"name": "01 Title", "key": "cover", "src": "slides/layouts/01.jpg", "thumb": "slides/layouts/thumb/01.jpg"}]
    downloads = [{"label": "Episode 2 als PDF", "href": "downloads/ep02.pdf", "size": "1,8 MB", "kind": "PDF"}]
    episode = {"number": 2, "title": "In-Office Whitening Workflow", "presenter": "Dr. Germán Gómez",
               "chapters": ["Document", "Protect"]}
    html = write_index(tmp_path, episode, slides, layouts, downloads).read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex' in html
    assert "slides/ep02/02.jpg" in html and "downloads/ep02.pdf" in html and "slides/layouts/01.jpg" in html
    assert html.count('lang="de"') == 1


def test_page_calls_the_deck_ppt(tmp_path):
    """Auf der Seite heißt das Deck „PPT“, nicht „Episode“."""
    slides = [{"n": 1, "title": "Slide 1", "kicker": "", "chapter": None, "notes": "",
               "src": "slides/ep02/01.jpg", "thumb": "slides/ep02/thumb/01.jpg"}]
    episode = {"number": 2, "title": "In-Office Whitening Workflow", "presenter": "Dr. Germán Gómez",
               "chapters": ["Document"]}
    html = write_index(tmp_path, episode, slides, [], []).read_text(encoding="utf-8")
    assert "<title>fläsh Campus · PPT</title>" in html
    assert "Die PPT zur Trainingsreihe mit Dr. Germán Gómez." in html
    assert '<p class="rail-ep">PPT</p>' in html
    assert "Episode" not in html and ">EP<" not in html


def test_downloads_are_called_ppt():
    """Die Downloads heißen „PPT als …“, die Dateinamen tragen kein ep02 mehr."""
    sources = download_sources(REPO / "out" / "episode-02.pptx", REPO / "gallery.pptx")
    assert [label for label, *_ in sources] == [
        "PPT als PDF", "PPT als PowerPoint", "Vorlage mit allen Layouts", "Layout-Übersicht als PDF"]
    assert [name for _, _, name, _ in sources] == [
        "flaesh-campus-in-office-whitening-workflow.pdf", "flaesh-campus-in-office-whitening-workflow.pptx",
        "flaesh-campus-template.pptx", "flaesh-campus-layouts.pdf"]
