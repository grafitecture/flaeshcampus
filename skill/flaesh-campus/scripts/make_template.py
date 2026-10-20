#!/usr/bin/env python3
"""Erzeugt die fläsh-Campus-Vorlage.

Aufruf: python3 scripts/make_template.py --out assets/template/flaesh-campus-template.pptx
                [--gallery examples/layout-gallery.json]
Mit --gallery kommt eine Beispielfolie je Layout in die Vorlage. build_deck.py entfernt diese Folien beim Bauen.
"""
import argparse
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from campus.build import build_deck  # noqa: E402
from campus.plan import load_plan  # noqa: E402
from campus.template import build_template, write_layout_spec  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--gallery", type=pathlib.Path, help="Folienplan mit einer Beispielfolie je Layout")
    args = parser.parse_args()
    if args.gallery:
        plan = load_plan(args.gallery)
        with tempfile.TemporaryDirectory() as tmp:
            bare = build_template(pathlib.Path(tmp) / "template.pptx", HERE.parent / "assets")
            built = pathlib.Path(tmp) / "gallery.pptx"
            build_deck(plan, bare, built, args.gallery.resolve().parent)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(built, args.out)
        path = args.out
    else:
        path = build_template(args.out, HERE.parent / "assets")
    write_layout_spec(path.with_name("layout-spec.json"))
    print(path)


if __name__ == "__main__":
    main()
