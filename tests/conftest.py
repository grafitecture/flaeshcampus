import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SKILL = REPO / "skill" / "flaesh-campus"
sys.path.insert(0, str(SKILL / "scripts"))


@pytest.fixture(scope="session")
def font_path() -> pathlib.Path:
    path = REPO / "fonts" / "CorporateS-Regular.otf"
    if not path.exists():
        pytest.skip("Corporate S font not available")
    return path


@pytest.fixture(scope="session")
def template_path(tmp_path_factory) -> pathlib.Path:
    try:
        from campus.template import build_template
    except ImportError:
        pytest.skip("template builder not implemented yet")
    out = tmp_path_factory.mktemp("template") / "flaesh-campus-template.pptx"
    return build_template(out, SKILL / "assets")
