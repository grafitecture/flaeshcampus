"""Folienplan (JSON) laden und prüfen.

Fehlertexte: "episode: …" bzw. "slide {n} ({type}): …"; alle Fehler werden gesammelt.
Geprüft werden Pflichtfelder, Anzahlen und Typen, damit der Bau nie mit einem Traceback abbricht.
"""
import json
from pathlib import Path

# Optionale Textfelder auf Folienebene; Pflichtfelder prüfen die Typ-Prüfungen unten zusätzlich.
OPTIONAL_TEXT = ("kicker", "title", "evidence", "notes", "caption", "line", "big", "statement", "text",
                 "explanation", "style")
BOX_TEXT = ("label", "title", "text")


class PlanError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def _is_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text(slide: dict, key: str) -> list[str]:
    value = slide.get(key)
    if value is not None and not isinstance(value, str):
        return [f"'{key}' must be text"]
    return [] if _is_text(value) else [f"missing '{key}'"]


def _optional_text(obj: dict, keys: tuple[str, ...], prefix: str = "") -> list[str]:
    return [f"{prefix}'{k}' must be text" for k in keys if k in obj and not isinstance(obj[k], str)]


def _photo(value, name: str = "photo") -> list[str]:
    if not isinstance(value, dict):
        return [f"{name} needs 'file' or 'brief'"]
    problems = _optional_text(value, ("file", "brief"), f"{name} ")
    if problems:
        return problems
    return [] if (_is_text(value.get("file")) or _is_text(value.get("brief"))) else [f"{name} needs 'file' or 'brief'"]


def _items(value, name: str, lo: int, hi: int, keys: tuple[str, ...] = ()) -> list[str]:
    if not isinstance(value, list) or not lo <= len(value) <= hi:
        return [f"{name}: exactly {lo} items" if lo == hi else f"{name}: {lo}–{hi} items"]
    problems = []
    for i, item in enumerate(value, 1):
        if not keys:
            if not _is_text(item):
                problems.append(f"{name}[{i}] must be text")
            continue
        if not isinstance(item, dict):
            problems.append(f"{name}[{i}] must be an object")
            continue
        wrong = [k for k in keys if k in item and item[k] is not None and not isinstance(item[k], str)]
        problems += [f"{name}[{i}] '{k}' must be text" for k in wrong]
        missing = [k for k in keys if k not in wrong and not _is_text(item.get(k))]
        if missing:
            problems.append(f"{name}[{i}] missing {', '.join(missing)}")
    return problems


def _box(value, name: str, keys: tuple[str, ...]) -> list[str]:
    if not isinstance(value, dict):
        return [f"missing '{name}'"]
    wrong = [k for k in BOX_TEXT if k in value and not isinstance(value[k], str)]
    problems = [f"{name} '{k}' must be text" for k in wrong]
    return problems + [f"{name} missing '{k}'" for k in keys if k not in wrong and not _is_text(value.get(k))]


def _focus(slide: dict) -> list[str]:
    return _box(slide["focus"], "focus", ("title", "text")) if "focus" in slide else []


def _check_points(s):
    return _text(s, "title") + _items(s.get("points"), "points", 2, 4, ("lead", "text")) + _focus(s)


def _check_points_photo(s):
    return _text(s, "title") + _items(s.get("points"), "points", 2, 4, ("lead", "text")) + _photo(s.get("photo"))


def _check_points_chart(s):
    problems = _text(s, "title") + _items(s.get("points"), "points", 2, 4, ("lead", "text"))
    chart = s.get("chart")
    if not isinstance(chart, dict):
        return problems + ["missing 'chart'"]
    problems += _optional_text(chart, ("title", "note"), "chart ")
    problems += _items(chart.get("bars"), "chart.bars", 2, 4, ("label",))
    for i, bar in enumerate(chart.get("bars") or [], 1):
        if not isinstance(bar, dict):
            continue
        value = bar.get("value")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
            problems.append(f"chart.bars[{i}] value must be 0–100")
        problems += _optional_text(bar, ("display",), f"chart.bars[{i}] ")
    return problems


def _check_statement(s):
    if not (_is_text(s.get("big")) or _is_text(s.get("statement"))):
        return ["needs 'big' or 'statement'"]
    return []


def _check_scale(s):
    problems = _text(s, "title")
    if "scale" in s:
        scale = s["scale"]
        if not isinstance(scale, dict):
            return problems + ["'scale' must be an object"]
        problems += _items(scale.get("items"), "scale.items", 2, 16)
        highlight = scale.get("highlight", [])
        if not isinstance(highlight, list) or not all(isinstance(h, str) for h in highlight):
            problems.append("scale.highlight must be a list of texts")
    elif "timeline" in s:
        timeline = s["timeline"]
        if not isinstance(timeline, dict):
            return problems + ["'timeline' must be an object"]
        problems += _items(timeline.get("points"), "timeline.points", 2, 6, ("at", "label"))
    else:
        problems.append("needs 'scale' or 'timeline'")
    if "points" in s:
        problems += _items(s["points"], "points", 1, 2, ("lead", "text"))
    return problems


def _check_compare(s):
    problems = _text(s, "title")
    for side in ("left", "right"):
        box = s.get(side)
        problems += _box(box, side, ("label",))
        if isinstance(box, dict):
            problems += _items(box.get("items"), f"{side}.items", 1, 4)
    if s.get("style", "do_dont") not in ("do_dont", "myth_fact"):
        problems.append("style must be 'do_dont' or 'myth_fact'")
    return problems


def _check_before_after(s):
    problems = _text(s, "title")
    for side in ("before", "after"):
        box = s.get(side)
        problems += _box(box, side, ("label",))
        if isinstance(box, dict):
            problems += _photo(box.get("photo"), f"{side}.photo")
    return problems


def _check_photo(s):
    problems = _text(s, "title") + _photo(s.get("photo"))
    if "evidence" in s:  # die Fußzeilen-Evidence läge über dem Textband
        problems.append("'evidence' is not shown on photo slides — put the source into the caption")
    return problems


def _check_photo_annotated(s):
    problems = _text(s, "title") + _photo(s.get("photo")) + _items(s.get("markers"), "markers", 1, 5, ("label",))
    for i, mk in enumerate(s.get("markers") or [], 1):
        if not isinstance(mk, dict) or not all(isinstance(mk.get(k), (int, float)) and not isinstance(mk.get(k), bool)
                                                and 0 <= mk[k] <= 1 for k in ("x", "y")):
            problems.append(f"markers[{i}] x and y must be 0–1")
    return problems


def _check_quiz(s):
    problems = _text(s, "question") + _items(s.get("options"), "options", 3, 3)
    if s.get("answer") not in (0, 1, 2) or isinstance(s.get("answer"), bool):
        problems.append("answer must be 0–2")
    return problems


CHECKS = {
    "cover": lambda s: [],
    "chapter": lambda s: [] if "chapter" in s else ["missing 'chapter'"],
    "hook": lambda s: _text(s, "quote") + _box(s.get("truth"), "truth", ("text",))
    + _box(s.get("answer"), "answer", ("text",)),
    "closing": lambda s: _text(s, "title") + _items(s.get("steps"), "steps", 1, 3, ("title", "text"))
    + _box(s.get("next"), "next", ("title",)),
    "points": _check_points,
    "points_photo": _check_points_photo,
    "points_chart": _check_points_chart,
    "statement": _check_statement,
    "checklist": lambda s: _text(s, "title") + _items(s.get("items"), "items", 1, 7) + _focus(s),
    "steps": lambda s: _text(s, "title") + _items(s.get("steps"), "steps", 3, 5, ("title", "text")),
    "compare": _check_compare,
    "scale": _check_scale,
    "summary": lambda s: _text(s, "title") + _items(s.get("items"), "items", 1, 5, ("title", "text")),
    "photo": _check_photo,
    "before_after": _check_before_after,
    "photo_annotated": _check_photo_annotated,
    "case": lambda s: _text(s, "title") + _text(s, "story")
    + _items(s.get("findings"), "findings", 1, 5, ("finding", "cause")),
    "quiz": _check_quiz,
}
SLIDE_TYPES = tuple(CHECKS)


def _check_episode(episode) -> list[str]:
    if not isinstance(episode, dict):
        return ["episode: missing"]
    problems = []
    if not isinstance(episode.get("number"), int) or isinstance(episode.get("number"), bool):
        problems.append("'number' must be an integer")
    problems += _text(episode, "title") + _optional_text(episode, ("subtitle",))
    problems += _items(episode.get("chapters"), "chapters", 2, 6)
    if "presenter" in episode:
        presenter = episode["presenter"]
        if not isinstance(presenter, dict):
            problems.append("'presenter' must be an object")
        else:
            problems += _optional_text(presenter, ("name", "credentials"), "presenter ")
            if "photo" in presenter:
                problems += [f"presenter.{p}" for p in _photo(presenter["photo"])]
    return [f"episode: {p}" for p in problems]


def validate_plan(plan: dict) -> list[str]:
    episode = plan.get("episode") if isinstance(plan, dict) else None
    errors = _check_episode(episode)
    chapters = (episode or {}).get("chapters") if isinstance(episode, dict) else None
    chapters = chapters if isinstance(chapters, list) else []
    slides = plan.get("slides") if isinstance(plan, dict) else None
    if not isinstance(slides, list) or not slides:
        return errors + ["slides: at least one slide"]
    for n, slide in enumerate(slides, 1):
        kind = slide.get("type") if isinstance(slide, dict) else None
        prefix = f"slide {n} ({kind}): "
        if kind not in CHECKS:
            errors.append(prefix + f"unknown type '{kind}'")
            continue
        problems = _optional_text(slide, OPTIONAL_TEXT) + list(CHECKS[kind](slide))
        if "chapter" in slide:
            ch = slide["chapter"]
            if not isinstance(ch, int) or isinstance(ch, bool) or not 1 <= ch <= len(chapters):
                problems.append(f"chapter {ch} out of range 1–{len(chapters)}")
        errors += [prefix + p for p in dict.fromkeys(problems)]
    return errors


def load_plan(path: Path) -> dict:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_plan(plan)
    if errors:
        raise PlanError(errors)
    return plan


def default_kicker(plan: dict, slide: dict) -> str | None:
    n = slide.get("chapter")
    if not n:
        return None
    return f"Phase {n} · {plan['episode']['chapters'][n - 1]}"
