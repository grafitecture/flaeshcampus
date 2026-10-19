import re

from campus.tokens import COLOR, PH_IDX, px, zone_circle


def test_px():
    assert px(1920) == 12192000
    assert px(1080) == 6858000
    assert px(1) == 6350


def test_colors():
    for name, value in COLOR.items():
        assert re.fullmatch(r"[0-9A-F]{6}", value), name
    assert COLOR["sky"] == "00A5FF"


def test_ph_idx_unique():
    values = list(PH_IDX.values())
    assert len(values) == len(set(values))
    assert PH_IDX["Title"] == 0


def test_zone():
    assert zone_circle() == (1714, 874, 150)
