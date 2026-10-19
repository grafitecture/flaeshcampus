"""Textmessung mit den Metriken von Corporate S (1 pt = 2 px auf dem 1920er Raster)."""
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import ImageFont

FONT_FILE = "CorporateS-Regular.otf"
_SCRIPTS = Path(__file__).resolve().parents[1]


@dataclass
class Para:
    text: str
    size_pt: float
    ln_spc_pct: int = 100
    spc_before_pt: float = 0
    spc_after_pt: float = 0
    spc_pt: float = 0
    indent_px: float = 0


def find_font() -> Path | None:
    candidates = []
    if os.environ.get("CAMPUS_FONT"):
        candidates.append(Path(os.environ["CAMPUS_FONT"]))
    candidates.append(_SCRIPTS.parent / "assets" / "fonts" / FONT_FILE)      # Skill-Paket
    candidates.append(_SCRIPTS.parents[2] / "fonts" / FONT_FILE)             # Repo
    return next((c for c in candidates if c.exists()), None)


def _fallback_font() -> Path:
    out = subprocess.run(["fc-match", "-f", "%{file}", "sans"], capture_output=True, text=True).stdout.strip()
    return Path(out)


class Measurer:
    def __init__(self, font_path: Path | None):
        self.approximate = font_path is None
        self.font_path = Path(font_path) if font_path else _fallback_font()
        hhea = TTFont(str(self.font_path))["hhea"]
        upm = TTFont(str(self.font_path))["head"].unitsPerEm
        self._line_ratio = (hhea.ascent - hhea.descent + hhea.lineGap) / upm
        self._fonts: dict[float, ImageFont.FreeTypeFont] = {}

    def _font(self, size_pt: float) -> ImageFont.FreeTypeFont:
        if size_pt not in self._fonts:
            self._fonts[size_pt] = ImageFont.truetype(str(self.font_path), size_pt * 2)
        return self._fonts[size_pt]

    def width_px(self, text: str, size_pt: float, spc_pt: float = 0) -> float:
        return self._font(size_pt).getlength(text) + spc_pt * 2 * len(text)

    def line_height_px(self, size_pt: float, ln_spc_pct: int = 100) -> float:
        return self._line_ratio * size_pt * 2 * ln_spc_pct / 100

    def wrap(self, text: str, size_pt: float, width_px: float, spc_pt: float = 0) -> list[str]:
        lines: list[str] = []
        for block in text.split("\n"):
            lines.extend(self._wrap_block(block, size_pt, width_px, spc_pt))
        return lines

    def _wrap_block(self, text: str, size_pt: float, width_px: float, spc_pt: float) -> list[str]:
        fits = lambda s: self.width_px(s, size_pt, spc_pt) <= width_px  # noqa: E731
        lines: list[str] = []
        line = ""
        for word in text.split():
            candidate = f"{line} {word}" if line else word
            if fits(candidate):
                line = candidate
                continue
            if line:
                lines.append(line)
            if fits(word):
                line = word
                continue
            chunk = ""
            for ch in word:
                if chunk and not fits(chunk + ch):
                    lines.append(chunk)
                    chunk = ch
                else:
                    chunk += ch
            line = chunk
        lines.append(line)
        return lines

    def block_height_px(self, paras: list[Para], width_px: float) -> float:
        total = 0.0
        for p in paras:
            text = p.text.rsplit("\t", 1)[-1]
            lines = self.wrap(text, p.size_pt, width_px - p.indent_px, p.spc_pt)
            total += p.spc_before_pt * 2 + p.spc_after_pt * 2
            total += len(lines) * self.line_height_px(p.size_pt, p.ln_spc_pct)
        return total

    def long_words(self, text: str, size_pt: float, width_px: float) -> list[str]:
        return [w for w in text.split() if self.width_px(w, size_pt) > width_px]
