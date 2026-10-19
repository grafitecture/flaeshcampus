#!/usr/bin/env python3
"""Baut eine fläsh-Campus-PowerPoint aus einem Folienplan (JSON).

Aufruf: python3 scripts/build_deck.py PLAN.json --out OUT.pptx [--template PATH]
Ausgabe: Bericht als JSON (Folienzahl, Bildbriefings, Warnungen). Exit-Code 2 bei Fehlern im Plan.
"""
import argparse
import json
import pathlib
import sys
import tempfile
from dataclasses import asdict

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from campus.build import build_deck  # noqa: E402
from campus.plan import PlanError, load_plan  # noqa: E402
from campus.template import build_template  # noqa: E402

DEFAULT_TEMPLATE = HERE.parent / "assets" / "template" / "flaesh-campus-template.pptx"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--template", type=pathlib.Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
    except PlanError as err:
        for line in err.errors:
            print(line)
        return 2
    template = args.template
    if not template.exists():
        template = build_template(pathlib.Path(tempfile.mkdtemp()) / "template.pptx", HERE.parent / "assets")
    report = build_deck(plan, template, args.out, args.plan.resolve().parent)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
