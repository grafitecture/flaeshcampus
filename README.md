# fläsh Campus

PowerPoint-Vorlage und Bau-Pipeline für die Trainingsreihe **fläsh Campus** (WHITEsmile, mit Dr. Germán Gómez). Gestaltung und Umsetzung: Grafitecture.

Ein Folienplan im JSON-Format wird zu einer fertigen PowerPoint im Campus-Layout. Die Vorlage hat 18 Layouts. Eine Prüfung misst jeden Text mit den echten Schriftmaßen von Corporate S und hält den Bereich für die Videoeinblendung frei.

## Inhalt

| Pfad | Was |
|---|---|
| `skill/flaesh-campus/assets/template/` | Vorlage `flaesh-campus-template.pptx` mit 18 Layouts und Beispielgalerie, `layout-spec.json` |
| `skill/flaesh-campus/scripts/` | `make_template.py`, `build_deck.py`, `check_deck.py` und das Paket `campus/` |
| `skill/flaesh-campus/examples/` | Folienplan Episode 2, Layout-Galerie, Fotos |
| `site/` | Präsentationsseite für Vercel, erzeugt mit `scripts/tools/build_site.py` |
| `docs/superpowers/` | Konzept (Spec) und Umsetzungsplan |

## Bauen

```bash
S=skill/flaesh-campus/scripts
python3 $S/make_template.py --gallery skill/flaesh-campus/examples/layout-gallery.json \
        --out skill/flaesh-campus/assets/template/flaesh-campus-template.pptx
python3 $S/build_deck.py skill/flaesh-campus/examples/episode-02.json --out out/episode-02.pptx
python3 $S/check_deck.py out/episode-02.pptx --render out/render
python3 scripts/tools/build_site.py   # site/ neu erzeugen (braucht LibreOffice und PDFs in out/)
```

Voraussetzungen: Python 3.12+, `python-pptx`, `lxml`, `Pillow`, `fonttools` und für das Rendern LibreOffice mit `pdftoppm`. Die Schrift **Corporate S** gehört nicht ins Repo, sie ist lizenziert. Für die Textprüfung liegt sie lokal unter `fonts/CorporateS-Regular.otf`.

Tests: `python3 -m pytest tests -q`

## Webseite

Vercel liefert den Ordner `site/` aus, eingestellt in `vercel.json`. Einen Build-Schritt auf Vercel gibt es nicht. Die Seite ist von Suchmaschinen ausgeschlossen (`noindex`) und lädt keine externen Dienste. Die Seitenschrift ist Carlito (SIL Open Font License) und liegt auf dem eigenen Server.
