import re

from campus.tokens import COLOR, PH_IDX, PRESENTER_MODES, SLIDE_PX, SMALL_AT, px


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


def test_presenter_tokens():
    assert PRESENTER_MODES[0] == "none" and "full" in PRESENTER_MODES and "small" in PRESENTER_MODES
    for at, (x, y, w) in SMALL_AT.items():
        assert x + w <= SLIDE_PX[0] - 40 and y + w * 9 / 16 <= SLIDE_PX[1] - 40, at
