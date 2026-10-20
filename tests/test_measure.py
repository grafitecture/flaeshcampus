import pytest

from campus.measure import Measurer, Para


@pytest.fixture(scope="module")
def m(font_path):
    return Measurer(font_path)


def test_width_monotonic(m):
    assert m.width_px("Lock the geometry, then check", 21) > m.width_px("Lock the geometry", 21)


def test_wrap_short(m):
    assert m.wrap("Lock the geometry", 21, 1260) == ["Lock the geometry"]


def test_wrap_long(m):
    text = ("Light intensity falls with the square of distance so one centimetre of extra gap between lamp "
            "and teeth costs roughly half of the available light power at the enamel surface")
    assert len(text.split()) == 30
    assert len(m.wrap(text, 17, 700)) >= 3


def test_unbreakable(m):
    word = "Zahnaufhellungsbehandlungsprotokoll" * 2
    parts = m.wrap(word, 39, 300)
    assert len(parts) >= 2
    assert "".join(parts) == word
    assert m.long_words(word, 39, 300) == [word]


def test_line_height(m):
    h = m.line_height_px(17)
    assert 1.1 * 34 <= h <= 1.35 * 34


def test_block_height_adds_paragraphs(m):
    one = m.block_height_px([Para("Lock the geometry", 21)], 1260)
    two = m.block_height_px([Para("Lock the geometry", 21), Para("Patient at 45°", 17, spc_before_pt=6)], 1260)
    assert two == pytest.approx(one + m.line_height_px(17) + 12)


def test_fallback():
    fallback = Measurer(None)
    assert fallback.approximate is True
    assert fallback.width_px("abc", 17) > 0
