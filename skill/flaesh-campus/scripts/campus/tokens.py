"""Design-Tokens für fläsh Campus.

Raster 1920 × 1080 px auf 13,333 × 7,5 Zoll: 1 px = 6350 EMU, 1 pt = 2 px.
"""

SLIDE_PX = (1920, 1080)
EMU_PER_PX = 6350
SLIDE_EMU = (12192000, 6858000)

FONT = "Corporate S"

COLOR = {
    "slate": "5D6C73",
    "sky": "00A5FF",
    "steel": "ABB7BE",
    "mist": "DEE7EC",
    "ink": "333333",
    "white": "FFFFFF",
    "night": "1F272B",
    "night2": "283237",
    "rail": "192024",
    "on_dark": "C9D4DA",
    "muted": "7D8B91",
    "muted_dark": "8597A0",
    "dim": "56666E",
    "ring_dark": "232C31",
}

SIZE_PT = {
    "display": 52,
    "chapter_number": 400,
    "chapter_title": 85,
    "title": 39,
    "quote": 36,
    "statement_big": 160,
    "statement": 32,
    "line": 23,
    "focus_title": 23,
    "lead": 21,
    "subtitle": 20,
    "body": 17,
    "kicker": 14,
    "small": 13,
    "label": 11,
    "rail_ep": 31,
}

# Laufweite in 1/100 pt für Versalien-Zeilen
KICKER_SPC = 196
LABEL_SPC = 176

RAIL_W = 150
CONTENT_X = 240
VIDEO_PRESENTER = "brand/video-presenter.jpg"  # Porträt für die Standbilder im Videofeld, falls der Plan keins hat

# Einblendung von Dr. Gómez (Details in presenter.py)
PRESENTER_MODES = ("none", "full", "half_left", "half_right", "third_left", "third_right", "small")
SMALL_AT = {"top_right": (1384, 40, 480), "bottom_right": (1384, 754, 480)}   # x, y, Breite (16:9)
SMALL_MIN_W = 320

PH_IDX = {
    "Title": 0,
    "Episode": 10,
    "Kicker": 11,
    "Subtitle": 12,
    "Presenter": 13,
    "Credentials": 14,
    "Photo": 15,
    "Number": 16,
    "Line": 17,
    "Quote": 18,
    "TruthLabel": 19,
    "TruthText": 20,
    "AnswerLabel": 21,
    "AnswerText": 22,
    "NextLabel": 23,
    "NextTitle": 24,
    "NextText": 25,
    "Points": 26,
    "Caption": 27,
    "Big": 28,
    "Statement": 29,
    "Text": 30,
    "PhotoBefore": 31,
    "PhotoAfter": 32,
    "LabelBefore": 33,
    "LabelAfter": 34,
    "Story": 35,
    "Question": 36,
}


def px(v: float) -> int:
    """Rasterpixel → EMU."""
    return int(round(v * EMU_PER_PX))
