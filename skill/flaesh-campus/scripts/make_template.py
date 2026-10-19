#!/usr/bin/env python3
"""Erzeugt die fläsh-Campus-Vorlage.

Aufruf: python3 scripts/make_template.py --out assets/template/flaesh-campus-template.pptx
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from campus.template import build_template, write_layout_spec  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    path = build_template(args.out, HERE.parent / "assets")
    write_layout_spec(path.with_name("layout-spec.json"))
    print(path)


if __name__ == "__main__":
    main()
