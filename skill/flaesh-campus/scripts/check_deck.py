#!/usr/bin/env python3
"""Prüft ein fläsh-Campus-Deck: Textüberlauf, Kreis-Zone, leere Platzhalter, Schriften, Glyphen.

Aufruf: python3 scripts/check_deck.py DECK.pptx [--render DIR]
Ausgabe: eine Zeile pro Befund. Exit-Code 1, wenn es Befunde gibt.
Mit --render werden PDF und PNG-Bilder je Folie für die Sichtprüfung erzeugt.
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from campus.checks import check_deck  # noqa: E402
from campus.measure import Measurer, find_font  # noqa: E402
from campus.render import render_pdf, render_pngs  # noqa: E402
from campus.template import layout_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck", type=pathlib.Path)
    parser.add_argument("--render", type=pathlib.Path)
    args = parser.parse_args()
    m = Measurer(find_font())
    if m.approximate:
        print("Hinweis: Corporate S fehlt, Prüfung mit Ersatzmaßen – Feinprüfung in PowerPoint nötig")
    issues = check_deck(args.deck, layout_spec(), m)
    for i in issues:
        print(f"slide {i.slide} {i.kind} {i.shape}: {i.detail}")
    if args.render:
        pdf = render_pdf(args.deck, args.render)
        for png in render_pngs(pdf, args.render):
            print(png)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
