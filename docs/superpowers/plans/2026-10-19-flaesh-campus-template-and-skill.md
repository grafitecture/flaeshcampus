# fläsh Campus – Vorlage, Build-Pipeline und Skill · Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine echte PowerPoint-Vorlage mit 18 Layouts, eine Pipeline „Folienplan (JSON) → PowerPoint → Prüfung“ und Episode 2 als Musterfolien bis Freitag 23.10.; danach das Claude-Skill-Paket.

**Architecture:** Ein Python-Generator erzeugt die Vorlage (Theme, Master, 18 Layouts mit echten Platzhaltern inkl. `lstStyle`). `build_deck` öffnet diese Vorlage mit python-pptx, legt Folien über Layout-Namen an, füllt Platzhalter und zeichnet dynamische Elemente (Leisten-Fortschritt, Diagramme, Nummern, Bildbriefings). `check_deck` misst Text mit den echten Corporate-S-Metriken, prüft Kreis-Zone/Leerstellen/Schriften/Glyphen und rendert über LibreOffice.

**Tech Stack:** Python 3, python-pptx 1.0.2, lxml, Pillow, fontTools, pytest; LibreOffice 24.2 + pdftoppm; Playwright/Chromium nur zum Rastern des Logos.

**Spec:** `docs/superpowers/specs/2026-10-19-flaesh-campus-design.md`

## Global Constraints

- Folie 16:9 = 12192000 × 6858000 EMU; Raster 1920 × 1080 px; 1 px = 6350 EMU; 1 pt = 2 px.
- Farben: slate 5D6C73 · sky 00A5FF · steel ABB7BE · mist DEE7EC · ink 333333 · white FFFFFF · night 1F272B · night2 283237 · rail 192024; Hilfstöne on_dark C9D4DA · muted 7D8B91 · muted_dark 8597A0 · dim 56666E · ring_dark 232C31.
- Schrift ausschließlich „Corporate S“ (Theme major + minor). Kein Bold, kein Italic, bis die Bold-Datei vorliegt.
- Die Zeichen ✓ → ▸ ● ○ fehlen in der Schrift: nie als Text, immer als Form.
- Kreis-Zone x 1564–1864, y 724–1024 (Mitte 1714/874, r 150) ist auf allen Layouts außer „01 Title“ frei.
- Größen (pt): display 52 · chapter_number 400 · chapter_title 85 · title 39 · quote 36 · statement_big 160 · statement 32 · line 23 · focus_title 23 · lead 21 · subtitle 20 · body 17 · kicker 14 (Versalien, spc 196) · small 13 · label 11 (Versalien, spc 176) · rail_ep 31.
- Max. 4 Punkte pro Folie, Titel einzeilig. Schrift wird nie verkleinert, um Platz zu schaffen.
- Layoutnamen exakt wie in der Tabelle in Task 4; Folienplan-Schlüssel exakt wie in der Spec, Abschnitt 4.
- Folientext Englisch.
- Jeder Commit endet mit:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` und
  `Claude-Session: https://claude.ai/code/session_01N9PVtcZKjnuaWVKADDArAR`

## Review Focus

1. **Unteilbare lange Wörter** (deutsche Komposita, lange Fachbegriffe): Die Messung bricht zeichenweise um, endet garantiert und meldet das Wort. Test in Task 6.
2. **Fotos mit extremem Seitenverhältnis oder fehlender Datei:** Bild wird beschnitten statt verzerrt; fehlende Datei ergibt Bildbriefing plus Warnung, kein Absturz. Test in Task 8.
3. **Episoden mit 2 oder 6 Kapiteln:** Der Fortschritt in der Leiste bleibt zwischen y 300 und 900 und kollidiert nicht mit dem Logo. Test in Task 8.
4. **Nicht darstellbare Zeichen** (→, ✓, ≥, Emoji) im Folienplan: Build läuft durch, Prüfung meldet jedes Zeichen. Test in Task 10.
5. **Fehlende optionale Felder** (kicker, evidence, notes, focus, caption): Es bleibt kein leerer Platzhalter stehen; der Kicker wird aus dem Kapitel abgeleitet. Test in Task 9.

---

## Dateistruktur

Repo `/home/claude/flaesh-campus`. Der Skill-Ordner ist zugleich Quellcode und Lieferpaket.

```
requirements-dev.txt                  python-pptx==1.0.2, lxml, Pillow, fonttools, pytest
tests/conftest.py                     sys.path += skill/flaesh-campus/scripts; Fixtures: font_path, template_path (Session, baut Vorlage in tmp)
fonts/CorporateS-Regular.otf          git-ignoriert
out/                                  git-ignoriert
skill/flaesh-campus/
  scripts/campus/tokens.py            Maße, Farben, Größen, Platzhalter-Indizes, px()
  scripts/campus/oxml.py              XML-Ergänzungen: Glow, Alpha, Radialverlauf, Platzhalter, Laufweite, Versalien
  scripts/campus/layouts.py           deklarative Definition der 18 Layouts
  scripts/campus/template.py          erzeugt Vorlage + layout-spec.json
  scripts/campus/measure.py           Textmessung
  scripts/campus/plan.py              Folienplan laden und prüfen
  scripts/campus/widgets_frame.py     Leiste, Evidence, Fußzeile, Fokus-Box, Fotos/Briefing
  scripts/campus/widgets_content.py   Punkte, Checkliste, Schritte, Balken, Vergleich, Skala, Zeitstrahl, Summary, Marker, Befunde, Quiz, Abschluss, Icons
  scripts/campus/slides.py            ein Renderer pro Folientyp
  scripts/campus/build.py             Orchestrierung
  scripts/campus/checks.py            Prüfungen
  scripts/campus/render.py            PPTX → PDF → PNG
  scripts/make_template.py · build_deck.py · check_deck.py    CLIs
  assets/brand/logo.svg · logo-white.png · logo-slate.png
  assets/template/flaesh-campus-template.pptx · layout-spec.json
  examples/episode-02.json · layout-gallery.json · photos/gomez.jpg
  SKILL.md · reference/                (Task 12)
```

---

### Task 1: Gerüst und Design-Tokens

**Files:**
- Create: `requirements-dev.txt`, `tests/conftest.py`, `skill/flaesh-campus/scripts/campus/__init__.py`, `skill/flaesh-campus/scripts/campus/tokens.py`
- Test: `tests/test_tokens.py`

**Interfaces:**
- Produces:
  - `px(v: float) -> int` (EMU) und `SLIDE_EMU = (12192000, 6858000)`
  - `COLOR: dict[str, str]`: Hex ohne `#`, Großbuchstaben, alle Werte aus den Global Constraints
  - `SIZE_PT: dict[str, float]` und `FONT = "Corporate S"`
  - `RAIL_W = 150`, `CONTENT_X = 240`, `ZONE = (1564, 724, 300, 300)`, `zone_circle() -> tuple[float, float, float]` (Mitte x, Mitte y, Radius in px)
  - `PH_IDX: dict[str, int]`: Title 0 · Episode 10 · Kicker 11 · Subtitle 12 · Presenter 13 · Credentials 14 · Photo 15 · Number 16 · Line 17 · Quote 18 · TruthLabel 19 · TruthText 20 · AnswerLabel 21 · AnswerText 22 · NextLabel 23 · NextTitle 24 · NextText 25 · Points 26 · Caption 27 · Big 28 · Statement 29 · Text 30 · PhotoBefore 31 · PhotoAfter 32 · LabelBefore 33 · LabelAfter 34 · Story 35 · Question 36

- [ ] **Step 1: Test schreiben**

  `test_px`: `px(1920) == 12192000`, `px(1080) == 6858000`, `px(1) == 6350`.
  `test_colors`: Jeder Wert erfüllt `re.fullmatch(r"[0-9A-F]{6}", v)`, und `COLOR["sky"] == "00A5FF"`.
  `test_ph_idx_unique`: Die Werte sind eindeutig, und `PH_IDX["Title"] == 0`.
  `test_zone`: `zone_circle() == (1714, 874, 150)`.
- [ ] **Step 2:** `pytest tests/test_tokens.py -v`. Erwartet: FAIL (ImportError).
- [ ] **Step 3:** `tokens.py` umsetzen. Dazu `conftest.py` mit `sys.path`-Eintrag und den Fixtures `font_path` (`fonts/CorporateS-Regular.otf`, Skip wenn fehlt) und `template_path` (ruft `campus.template.build_template` einmal je Session in `tmp_path_factory`; `pytest.skip` bis Task 4 existiert).
- [ ] **Step 4:** `pip install --break-system-packages -r requirements-dev.txt && pytest tests/test_tokens.py -v`. Erwartet: PASS.
- [ ] **Step 5:** Commit `chore: Gerüst und Design-Tokens`.

### Task 2: Marken-Assets und Schrift

**Files:**
- Create: `skill/flaesh-campus/assets/brand/logo.svg` (Pfade aus `scratchpad/look/build_boards.py`, `LOGO_PATHS`, viewBox `0 -2 595.3 252`), `logo-white.png`, `logo-slate.png`, `skill/flaesh-campus/examples/photos/gomez.jpg`, `scripts/tools/raster_logo.py`, `fonts/CorporateS-Regular.otf`, `.gitignore` (+ `fonts/`, `out/`)
- Test: `tests/test_assets.py`

**Interfaces:**
- Produces: PNG-Logos 1200 px breit, RGBA, transparenter Hintergrund; `gomez.jpg` (JPEG, Qualität 92, aus `uploads/…/693be94d-image.webp`).

- [ ] **Step 1: Test schreiben**

  `test_logo_pngs`: Beide Dateien existieren, `mode == "RGBA"`, `width == 1200`, `getpixel((0, 0))[3] == 0`, Seitenverhältnis 595.3/252 ± 1 %.
  `test_portrait`: `Image.open(...).format == "JPEG"` und Breite ≥ 700.
  `test_font_installed`: `"Corporate S" in fc-list` (Skip ohne Fontdatei).
- [ ] **Step 2:** `pytest tests/test_assets.py -v`. Erwartet: FAIL.
- [ ] **Step 3:** `raster_logo.py` rendert das SVG mit Playwright (`page.screenshot(omit_background=True)`) in Weiß und Slate. Dann: Porträt mit Pillow nach JPEG umwandeln, Font nach `fonts/` und `~/.fonts` kopieren, `fc-cache -f` ausführen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: Logo-Assets, Porträt, Schrift-Setup`. Die Schrift wird nicht committet.

### Task 3: OOXML-Helfer

**Files:**
- Create: `skill/flaesh-campus/scripts/campus/oxml.py`
- Test: `tests/test_oxml.py`

**Interfaces:**
- Produces:
  - `add_glow(shape, color: str, radius_px: float, alpha_pct: int) -> None`: `a:effectLst/a:glow` in `spPr`, in Schema-Reihenfolge nach `a:ln`.
  - `set_fill_alpha(shape, alpha_pct: int) -> None` und `set_line_alpha(shape, alpha_pct: int) -> None`
  - `set_radial_fill(shape, color: str, stops: list[tuple[int, int]]) -> None`: `stops` sind (Position %, Deckkraft %); `a:path path="circle"` mit `fillToRect` 50/50/50/50.
  - `add_text_glow(rpr_el, color: str, radius_px: float, alpha_pct: int) -> None`: `effectLst` nach `solidFill`, vor `latin`.
  - `to_placeholder(shape, ph_type: Literal["title", "body", "pic"], idx: int | None, name: str, levels: list[dict], prompt: list[str], anchor: str = "t", insets_px=(0, 0, 0, 0), geom: str = "rect") -> None`
    - Wandelt eine per API erzeugte Form auf einem Layout in einen Platzhalter um: `p:ph` (Titel ohne `idx`), `hasCustomPrompt="1"`, `a:spLocks noGrp="1"`.
    - Schreibt den `a:lstStyle` aus `levels`. Schlüssel je Ebene: `size_pt`, `color`, `caps`, `spc`, `ln_spc_pct`, `spc_before_pt`, `spc_after_pt`, `mar_l_px`, `indent_px`, `tab_px`, `align`.
    - Setzt `a:bodyPr` mit `wrap="square"`, Insets und `a:noAutofit`, dazu je einen Prompt-Absatz pro Ebene.
- Hinweis: XML immer mit lxml über `shape._element` bearbeiten, nie über `xml.etree` (zerstört Namespaces).

- [ ] **Step 1: Test schreiben.** Die Formen legt der Test auf einem Layout an, über `SlideShapes(layout.shapes._spTree, layout)` aus der Standard-`Presentation()`.

  `test_glow_after_ln`: In den Kindern von `spPr` steht `a:ln` vor `a:effectLst`; `glow@rad == px(46)`; `alpha@val == "45000"`.
  `test_radial_fill`: `gradFill/a:path@path == "circle"`; drei `a:gs` mit Deckkraft 34000 / 10000 / 0.
  `test_body_placeholder`: `shape.is_placeholder`; `placeholder_format.idx == 26`; `lvl1pPr/defRPr@sz == "2100"`, `solidFill/srgbClr@val == "5D6C73"`, `latin@typeface == "Corporate S"`; `lvl2pPr@marL == str(px(80))`.
  `test_title_placeholder`: `ph@type == "title"` und kein `idx`-Attribut.
  `test_pic_placeholder_ellipse`: `ph@type == "pic"` und `prstGeom@prst == "ellipse"`.
- [ ] **Step 2:** Test ausführen. Erwartet: FAIL.
- [ ] **Step 3:** `oxml.py` umsetzen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: OOXML-Helfer (Glow, Verläufe, Platzhalter)`.

### Task 4: Vorlagen-Generator: Theme, Master, Rahmen, 18 Layouts

**Files:**
- Create: `scripts/campus/layouts.py`, `scripts/campus/template.py`, `skill/flaesh-campus/scripts/make_template.py`
- Test: `tests/test_template.py`

**Interfaces:**
- Consumes: `tokens`, `oxml`.
- Produces:
  - `@dataclass PhDef(name, ph_type, box, levels, prompt, anchor="t", geom="rect", fill=None, fill_alpha=None, line=None, glow=None, insets=(0, 0, 0, 0))`
  - `@dataclass DecorDef(kind: Literal["rect", "roundrect", "ellipse", "text", "image", "radial"], name: str, box, style: dict)`
  - `@dataclass LayoutDef(name: str, key: str, frame: Literal["cover", "dark", "light", "full"], placeholders: list[PhDef], decor: list[DecorDef])`
  - `LAYOUTS: list[LayoutDef]`, `build_template(out: Path, assets_dir: Path) -> Path`
  - CLI: `python scripts/make_template.py --out PATH [--gallery PLAN.json]`. `--gallery` folgt in Task 11.

**Technik (entschieden):**
- Basis ist `Presentation()`. Slide-Größe auf `SLIDE_EMU` setzen.
- **Theme:** Blob des Theme-Parts ersetzen. Name „fläsh Campus“, major/minor latin „Corporate S“. Farben: dk1 333333 · lt1 FFFFFF · dk2 1F272B · lt2 DEE7EC · accent1 00A5FF · accent2 5D6C73 · accent3 ABB7BE · accent4 283237 · accent5 7D8B91 · accent6 C9D4DA · hlink 00A5FF · folHlink 5D6C73.
- **Master:** Hintergrund Weiß. `txStyles`: titleStyle 39 pt slate; bodyStyle lvl1 21 pt slate, lvl2–3 17 pt ink; alles Corporate S.
- **Layouts:**
  - Die 11 Standard-Layouts entfernen: `sldLayoutId` löschen und `master.part.drop_rel(rId)`.
  - Jedes neue Layout aus minimalem `p:sldLayout`-XML erzeugen, mit `cSld@name` = Layoutname und `preserve="1"`.
  - Part: `SlideLayoutPart(package.next_partname("/ppt/slideLayouts/slideLayout%d.xml"), CT.PML_SLIDE_LAYOUT, package, element)`.
  - Beidseitig verknüpfen (`RT.SLIDE_MASTER` und `RT.SLIDE_LAYOUT`). `sldLayoutId` ab 2147483649 fortlaufend.
- **Formen:** über `SlideShapes(layout.shapes._spTree, layout)` (`add_shape`, `add_textbox`, `add_picture`), Platzhalter danach per `oxml.to_placeholder`.
- **Reihenfolge im spTree:** Dekor zuerst, dann Platzhalter. Layout-Formen liegen auf der Folie immer unter Folien-Formen.

**Rahmen** (Formen in px; benannt, damit Tests sie finden):

| Rahmen | Elemente |
|---|---|
| light | Hintergrund Weiß · `rail` Rechteck (0,0,150,1080) night · `rail-ep-label` Text „EP“ (0,84,150,30) label steel zentriert · `rail-logo` logo-white.png (31,960,88,37) · `zone-ring` Ellipse ZONE, Linie sky 4 px, Füllung Weiß, Glow sky 46 px 45 % · Platzhalter Episode (0,108,150,70) rail_ep weiß zentriert, Prompt „00“ |
| dark | wie light, aber Hintergrund night, `rail` rail-Farbe, `zone-ring` Füllung ring_dark mit Glow sky 60 px 55 % |
| cover | wie dark ohne `zone-ring`. Zusätzlich: `glow-bg` Ellipse (766,−220,1520,1520), Radialfüllung sky 34/10/0 % · `arc-1` Ellipse (1126,140,800,800), Linie sky 2 px 28 % · `arc-2` Ellipse (1036,50,980,980), Linie sky 2 px 14 % · `cover-logo` logo-white.png (230,96,200,85) · `cover-campus` Text „Campus“ (452,108,320,80) 29 pt sky |
| full | Hintergrund night · `rail` + Episode-Platzhalter + `rail-logo` wie dark. Den Ring zeichnet der Build über das Foto, siehe Task 8 |

**Kopf-Platzhalter** an Standardposition:

- Kicker (240,110,1500,40): kicker, sky, Versalien. Auf 03–13 und 15–18.
- Title (240,150,1500,100): title; slate auf light, weiß auf dark. Auf 04–13 und 15–17.
- 01, 02 und 14 haben eigene Positionen laut Tabelle. 03 und 18 haben keinen Title: Quote bzw. Question übernehmen die Rolle.

**Layouts und Platzhalter** (Box in px; Größe = `SIZE_PT`-Schlüssel; Farbe):

| Layout | Schlüssel | Rahmen | Platzhalter (zusätzlich zum Kopf) |
|---|---|---|---|
| 01 Title | cover | cover | Kicker (230,356,980,40) · Title (226,404,960,230) display weiß, Zeilenabstand 102 % · Subtitle (230,654,820,110) subtitle on_dark · Presenter (230,880,1000,46) lead weiß · Credentials (230,930,1000,80) small steel · Photo pic (1236,250,580,580) Ellipse, Linie sky 6 px, Glow sky 90 px 60 % |
| 02 Chapter | chapter | dark + `glow-bg` Ellipse (−60,−200,1240,1240) radial 26/8/0 % | Number (230,20,560,880) chapter_number sky mit Text-Glow 80 px 65 % · Kicker (800,330,900,40) · Title (792,376,1000,180) chapter_title weiß · Line (800,590,700,130) line on_dark |
| 03 Hook | hook | dark + `truth-card` Roundrect (240,520,600,360) night2 + `answer-card` Roundrect (880,520,620,360) night2, Linie sky 2 px, Glow 50 px 40 % | Kein Title · Quote (240,170,1300,300) quote weiß · TruthLabel (290,560,500,30) label steel · TruthText (290,610,500,240) body on_dark · AnswerLabel (930,560,520,30) label sky · AnswerText (930,610,520,240) body weiß |
| 04 Closing | closing | dark + `next-card` Roundrect (1180,330,620,330) night2, Linie sky, Glow | NextLabel (1230,370,520,30) label sky · NextTitle (1230,410,520,120) lead weiß · NextText (1230,540,520,110) body on_dark |
| 05 Points | points | light | Points (240,330,1260,560): lvl1 lead slate, spcBef 22 pt, marL 80, indent −80, tab 80; lvl2 body ink, marL 80, spcBef 6 pt |
| 06 Points + Photo | points_photo | light | Points (240,330,700,560) · Photo pic (1000,300,800,400) · Caption (1000,712,540,40) small muted |
| 07 Points + Chart | points_chart | light | Points (240,330,700,560) |
| 08 Statement | statement | light | Big (240,200,1300,330) statement_big sky · Statement (240,560,1200,150) statement slate · Text (240,730,1200,130) body ink |
| 09 Checklist | checklist | light | – |
| 10 Steps | steps | light | – |
| 11 Compare | compare | light | – |
| 12 Scale | scale | light | Points (240,560,1260,330), Ebenen wie 05 |
| 13 Summary | summary | light | – |
| 14 Photo | photo | full | Photo pic (150,0,1770,1080). Darüber, je mit Füllung night 85 % und Innenabstand 40 px: Kicker (190,780,1300,60) · Title (190,840,1300,110) weiß · Caption (190,950,1300,90) body on_dark |
| 15 Before / After | before_after | light | PhotoBefore pic (240,330,600,400) · PhotoAfter pic (900,330,600,400) · LabelBefore (240,750,600,40) body slate · LabelAfter (900,750,600,40) body slate |
| 16 Photo Annotated | photo_annotated | light | Photo pic (240,300,900,600) |
| 17 Case | case | light | Story (240,330,1260,150) lead slate |
| 18 Quiz | quiz | dark | Kicker · Question (240,180,1260,220) quote weiß. Kein Title-Platzhalter |

- [ ] **Step 1: Test schreiben** (nutzt Fixture `template_path`)

  `test_slide_size`: `(prs.slide_width, prs.slide_height) == SLIDE_EMU`.
  `test_layout_names`: `[l.name for l in prs.slide_layouts] == ["01 Title", "02 Chapter", "03 Hook", "04 Closing", "05 Points", "06 Points + Photo", "07 Points + Chart", "08 Statement", "09 Checklist", "10 Steps", "11 Compare", "12 Scale", "13 Summary", "14 Photo", "15 Before / After", "16 Photo Annotated", "17 Case", "18 Quiz"]`.
  `test_theme_fonts`: major- und minor-`latin@typeface == "Corporate S"`.
  `test_zone_ring`: Jedes Layout außer 01 und 14 hat die Form `zone-ring` mit Box == `px(ZONE)` und einem `a:glow`.
  `test_rail`: Alle 18 haben `rail` mit `left == 0` und `width == px(150)`.
  `test_header`: Bei 03–13 und 15–18 liegt Kicker-idx 11 bei (240,110). Bei 04–13 und 15–17 hat der Title-Platzhalter den Typ TITLE mit Box (240,150,1500,100). 03 und 18 haben keinen Title-Platzhalter.
  `test_validate`: `subprocess.run(["python3", "/mnt/skills/public/pptx/scripts/office/validate.py", str(template_path)]).returncode == 0` (Skip, wenn das Script fehlt).
- [ ] **Step 2:** `pytest tests/test_template.py -v`. Erwartet: FAIL.
- [ ] **Step 3:** `layouts.py` mit Rahmen und Kopf für alle 18, `template.py` und `make_template.py` umsetzen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS. Zusätzlich die Vorlage mit `python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf` rendern und eine leere Musterfolie je Layout ansehen.
- [ ] **Step 5:** Commit `feat: Vorlagen-Generator mit Theme, Master und 18 Layout-Rahmen`.

### Task 5: Typ-Platzhalter und layout-spec.json

**Files:**
- Modify: `scripts/campus/layouts.py` (Tabelle aus Task 4 vollständig), `scripts/campus/template.py`
- Test: `tests/test_template_placeholders.py`

**Interfaces:**
- Produces:
  - `layout_spec() -> dict`: `{layoutname: {"key", "frame", "zone": bool, "placeholders": {name: {"idx", "type", "box": [x, y, w, h], "levels": [...]}}}}`
  - `write_layout_spec(path: Path) -> None` nach `assets/template/layout-spec.json`. Diese Datei ist die Quelle für Prüfung und Skill-Doku.

- [ ] **Step 1: Test schreiben**

  `test_placeholder_matrix`: Für jede Zeile der Tabelle aus Task 4 existiert ein Platzhalter mit `PH_IDX[name]`; Typ und Box stimmen auf ±1 EMU; `lvl1 sz == SIZE_PT[...] * 100`.
  `test_cover_photo`: Photo auf „01 Title“ hat `prstGeom@prst == "ellipse"`, `ln@w == str(px(6))` und Glow-`rad == px(90)`.
  `test_spec_json`: `json.loads` ergibt 18 Schlüssel; jeder Platzhalter hat `idx`, `type`, `box` und `levels`.
- [ ] **Step 2:** Test ausführen. Erwartet: FAIL.
- [ ] **Step 3:** Umsetzen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: Typ-Platzhalter und layout-spec.json`.

### Task 6: Textmessung

**Files:**
- Create: `scripts/campus/measure.py`
- Test: `tests/test_measure.py`

**Interfaces:**
- Produces:
  - `@dataclass Para(text: str, size_pt: float, ln_spc_pct: int = 100, spc_before_pt: float = 0, spc_after_pt: float = 0, spc_pt: float = 0, indent_px: float = 0)`
  - `class Measurer(font_path: Path | None)` mit dem Attribut `approximate: bool` und den Methoden:
    - `width_px(text, size_pt, spc_pt=0) -> float`
    - `line_height_px(size_pt, ln_spc_pct=100) -> float`
    - `wrap(text, size_pt, width_px, spc_pt=0) -> list[str]`
    - `block_height_px(paras: list[Para], width_px: float) -> float`
    - `long_words(text, size_pt, width_px) -> list[str]`
  - `find_font() -> Path | None`. Reihenfolge: Umgebungsvariable `CAMPUS_FONT`, dann `assets/fonts/CorporateS-Regular.otf`, dann `<repo>/fonts/…`, sonst `None`.
- **Algorithmus:**
  - `wrap` bricht greedy an Leerzeichen um. Ein Wort breiter als `width_px` wird zeichenweise geteilt.
  - Zeilenhöhe = (hhea ascender − descender + lineGap) / unitsPerEm × size_px × ln_spc.
  - Ohne Font: Fallback auf `fc-match -f '%{file}' sans`, `approximate = True`.

- [ ] **Step 1: Test schreiben**

  `test_width_monotonic`: Die Breite von „Lock the geometry, then check“ ist größer als die von „Lock the geometry“.
  `test_wrap_short`: `wrap("Lock the geometry", 21, 1260) == ["Lock the geometry"]`.
  `test_wrap_long`: Ein 30-Wort-Satz bei 17 pt und 700 px ergibt ≥ 3 Zeilen.
  `test_unbreakable` (Review Focus 1): `w = "Zahnaufhellungsbehandlungsprotokoll" * 2`. `wrap(w, 39, 300)` liefert ≥ 2 Teile, `"".join(...) == w`, und `long_words(w, 39, 300) == [w]`.
  `test_line_height`: 17 pt bei 100 % liegt zwischen 1,1 × 34 und 1,35 × 34 px.
  `test_fallback`: `Measurer(None).approximate is True` und `width_px("abc", 17) > 0`.
- [ ] **Step 2:** Test ausführen. Erwartet: FAIL.
- [ ] **Step 3:** Umsetzen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: Textmessung mit Corporate-S-Metriken`.

### Task 7: Folienplan laden und prüfen

**Files:**
- Create: `scripts/campus/plan.py`, `tests/fixtures/minimal-plan.json` (cover, chapter, points, quiz)
- Test: `tests/test_plan.py`

**Interfaces:**
- Produces:
  - `class PlanError(Exception)` mit `.errors: list[str]`
  - `validate_plan(plan: dict) -> list[str]`
  - `load_plan(path: Path) -> dict` (wirft `PlanError`)
  - `default_kicker(plan: dict, slide: dict) -> str | None`: liefert `"Phase {n} · {chapters[n-1]}"`.
- **Format:**
  - `{"episode": {"number", "title", "subtitle", "presenter": {"name", "credentials", "photo"}, "chapters": [2–6 strings]}, "slides": [...]}`
  - Ein Foto-Objekt hat die Form `{"file"?, "brief"?}`; mindestens eins von beiden.
  - Felder je Typ: Spec, Abschnitt 4.
  - Grenzen: points 2–4 · checklist ≤ 7 · steps 3–5 · summary ≤ 5 · compare ≤ 4 je Seite · scale items 2–16 · timeline 2–6 · markers ≤ 5 · findings ≤ 5 · quiz 3 Optionen, answer 0–2 · closing steps ≤ 3.
  - Fehlertext: `"slide {n} ({type}): {problem}"`.

- [ ] **Step 1: Test schreiben**

  `test_minimal_ok`: `validate_plan(minimal) == []`.
  `test_unknown_type`: Fehler enthält `"unknown type 'bullets'"`.
  `test_points_bounds`: 5 Punkte ergeben einen Fehler mit `"points: 2–4 items"`.
  `test_chapter_range`: chapter 6 bei 5 Kapiteln ergibt einen Fehler mit `"chapter 6 out of range 1–5"`.
  `test_quiz_answer`: answer 3 ergibt einen Fehler mit `"answer must be 0–2"`.
  `test_photo_object`: `{}` ergibt einen Fehler mit `"photo needs 'file' or 'brief'"`.
  `test_collects_all`: Drei Fehler im Plan ergeben `len(errors) == 3`.
  `test_default_kicker`: chapter 3 ergibt `"Phase 3 · Apply"`; ohne chapter `None`.
- [ ] **Step 2:** Test ausführen. Erwartet: FAIL.
- [ ] **Step 3:** Umsetzen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: Folienplan-Validierung`.

### Task 8: Widgets für Rahmen und Fotos

**Files:**
- Create: `scripts/campus/widgets_frame.py`
- Test: `tests/test_widgets_frame.py`

**Interfaces:**
- Consumes: `tokens`, `oxml`, `measure.Measurer`.
- Produces (alle Formen benannt):
  - `rail_progress(slide, chapters: list[str], current: int | None, dark: bool) -> None`
    - Formen `rail-line`, `rail-dot-{i}` (aktiv: Name mit Suffix `-active`) und `rail-num-{i}`.
    - Erster Punkt bei y 300, Abstand `min(104, 600 / (n − 1))`.
    - Aktiv: 30 px sky mit Glow 26 px 95 %. Erledigt: 16 px steel. Offen: 16 px Kontur dim.
  - `evidence(slide, text: str, dark: bool) -> None`: `evidence-label` „EVIDENCE“ (240,920,600,24) label sky; `evidence-text` (240,948,1240,36) small muted bzw. muted_dark.
  - `footer(slide, text: str, dark: bool) -> None`: `footer` (240,1010,1200,30) label steel.
  - `focus_box(slide, box: tuple[int, int, int], label: str, title: str, text: str, m: Measurer) -> int`
    - Box ist (x, y, w); Rückgabe: Höhe in px.
    - Formen: `focus-card` night, Linie sky 2 px, Glow 50 px 40 % · `focus-label` label sky · `focus-title` focus_title weiß · `focus-text` body on_dark.
  - `place_photo(slide, idx: int, photo: dict | None, base_dir: Path, warnings: list[str], ellipse: bool = False) -> str | None`
    - Nicht-JPEG/PNG (z. B. webp) per Pillow nach JPEG in ein temporäres Verzeichnis.
    - Einfügen mit `insert_picture`, beschnitten statt verzerrt (python-pptx-Crop).
    - Bei Ellipse: `auto_shape_type = MSO_SHAPE.OVAL` plus Linie und Glow wie im Layout.
    - Fehlt die Datei: Platzhalter löschen, `brief_card` zeichnen, Briefing zurückgeben und eine Warnung eintragen.
  - `brief_card(slide, box, brief: str) -> None`: `brief-card` mist, Kontur steel gestrichelt; `brief-icon` Kamera aus Formen; `brief-text` body slate.
  - `zone_ring_on_top(slide, dark: bool) -> None`: Ring wie im dark-Rahmen, als letzte Form.

- [ ] **Step 1: Test schreiben** (Folien aus `template_path`)

  `test_rail_active`: 5 Kapitel, current 3. Genau eine Form endet auf `-active`, nämlich `rail-dot-3-active`; 5 Punkte insgesamt.
  `test_rail_bounds` (Review Focus 3): Bei n = 2 und n = 6 liegen alle Punkt-Tops zwischen `px(300)` und `px(900)`.
  `test_photo_aspect` (Review Focus 2): Ein Bild 400×1200 in Photo (1000,300,800,400) ergibt `crop_top + crop_bottom > 0` und `crop_left == crop_right == 0`.
  `test_photo_missing`: `{"file": "nope.jpg", "brief": "Foto: Lampe"}` liefert `"Foto: Lampe"`; die Folie hat `brief-card`; die Warnung enthält `"nope.jpg"`; kein Platzhalter idx 15 mehr auf der Folie.
  `test_webp`: Ein webp-Bild ergibt `picture.image.content_type == "image/jpeg"`.
  `test_focus_height`: Langer Text ergibt eine größere Höhe als kurzer Text.
- [ ] **Step 2:** Test ausführen. Erwartet: FAIL.
- [ ] **Step 3:** Umsetzen.
- [ ] **Step 4:** Test ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: Rahmen-Widgets und Foto-Handling`.

### Task 9: Inhalts-Widgets, Renderer und Build

**Files:**
- Create: `scripts/campus/widgets_content.py`, `scripts/campus/slides.py`, `scripts/campus/build.py`, `skill/flaesh-campus/scripts/build_deck.py`
- Test: `tests/test_widgets_content.py`, `tests/test_build.py`

**Interfaces:**
- Consumes: alles aus den Tasks 1–8.
- Produces (`widgets_content`, Formen benannt, Maße in px):
  - `points_text(ph, points: list[dict]) -> None`: je Punkt zwei Absätze. Ebene 0 = Lauf „01“ in sky, dann `"\t" + lead`. Ebene 1 = text.
  - `checklist(slide, items, x=240, y=330, w=900) -> None`: `check-num-{i}` (Kreis 60 px mist, Zahl sky) und `check-text-{i}` (body ink), Zeilenabstand 82.
  - `steps_grid(slide, steps, dark: bool, area=(240,330,1260,560)) -> None`
    - Raster: 3 → 1×3, 4 → 2×2, 5 → 3 + 2.
    - Formen `step-num-{i}` (64 px sky, weiße Zahl), `step-title-{i}` (lead), `step-text-{i}` (body).
  - `bars_card(slide, chart: dict, box=(1000,330,800,364)) -> None`
    - Formen `chart-card` (mist), `chart-title`, `bar-track-{i}`, `bar-fill-{i}` (Breite = Wert % der Spur), `bar-label-{i}`, `bar-value-{i}`, `chart-note`.
    - Hervorgehobener Balken in sky mit Glow, die übrigen in steel.
  - `compare_columns(slide, left: dict, right: dict, style: Literal["do_dont", "myth_fact"]) -> None`
    - Spalten (240,330,600) und (900,330,600).
    - Formen `compare-head-l/r`, `compare-item-l/r-{i}`, `icon-check-l-{i}` bzw. `icon-cross-r-{i}` aus Linien.
  - `scale_chips(slide, items, highlight: list[str], box=(240,330,1560,140)) -> None`: `scale-chip-{i}`; hervorgehoben in sky mit weißem Text.
  - `timeline(slide, points, box=(240,330,1260,200), dark=False) -> None`: `tl-line`, `tl-dot-{i}`, `tl-at-{i}`, `tl-label-{i}`.
  - `scale_caption(slide, text: str) -> None`: `scale-caption` (240,490,1260,40) small muted. Die Punkte stehen im Platzhalter Points darunter.
  - `summary_items(slide, items) -> None`: zwei Spalten mit 3 + 2 Einträgen; `sum-check-{i}` (Kreis sky mit Haken aus Linien), `sum-title-{i}`, `sum-text-{i}`.
  - `markers(slide, photo_box, markers) -> None`
    - Formen `marker-{i}` (sky mit Glow, Position = x/y-Anteil der Fotobox) und `legend-{i}`.
    - Die Legende liegt in (1200,320,560,380).
  - `case_findings(slide, findings, y=520) -> None`: `finding-{i}`, `arrow-{i}` und `cause-{i}`, Zeilenabstand 76.
  - `quiz_options(slide, options, answer: int | None, explanation: str | None) -> None`
    - `quiz-opt-{i}` (night2; bei der Antwort sky mit Glow), `quiz-letter-{i}`.
    - Erklärung `quiz-expl` (240,880,1260,80) body on_dark.
  - `closing_steps(slide, steps) -> None`: `next-step-num-{i}`, `next-step-title-{i}`, `next-step-text-{i}` in (240,330,880).
- Produces (`slides`, `build`):
  - `@dataclass Ctx(prs, plan, m: Measurer, base_dir: Path, report: BuildReport)`
  - `@dataclass BuildReport(slides: int = 0, briefs: list[tuple[int, str]] = field(default_factory=list), warnings: list[str] = field(default_factory=list))`
  - `new_slide(ctx, layout_name: str)`
  - `fill(slide, name: str, text: str | None) -> None`: entfernt den Platzhalter, wenn der Text leer ist; setzt sonst Läufe ohne Formatierung, die Formatierung erbt aus dem Layout.
  - `RENDERERS: dict[str, Callable[[Ctx, dict], None]]`
  - `build_deck(plan: dict, template: Path, out: Path, base_dir: Path, m: Measurer | None = None) -> BuildReport`. Leert zuerst alle Folien der Vorlage über `sldIdLst` und `drop_rel`.
  - CLI: `python scripts/build_deck.py PLAN.json --out OUT.pptx [--template PATH]` gibt den Report als JSON aus. Bei `PlanError` Exit-Code 2 mit einer Zeile pro Fehler.
- **Jeder Renderer:**
  - Layout wählen, Kicker = `slide.kicker` oder `default_kicker`.
  - Leiste: `rail_progress` mit dem Kapitel der Folie, auf Kapitelfolien das eigene Kapitel. Episode-Platzhalter = `f"{number:02d}"`.
  - Fußzeile `f"{episode.title.upper()} · {slide_no}"` auf allen Folien außer 01, 02 und 14.
  - Evidence, sofern vorhanden. Notizen über `notes_slide.notes_text_frame.text`.
- **Zusatzregeln:**
  - points mit `focus`: Points-Platzhalter auf 900 px Breite, `focus_box` bei (1220,330,580).
  - checklist mit `focus`: Fokus-Box bei (1220,330,580).
  - quiz erzeugt zwei Folien: Frage (answer `None`) und Auflösung (answer + explanation).
  - photo ruft `zone_ring_on_top` auf.

- [ ] **Step 1: Tests schreiben**

  `test_points_runs`: Absatz 0 hat den Text `"01\tLock the geometry"`, Lauf 0 die Farbe sky; Absatz 1 hat `level == 1`.
  `test_checklist_rows`: 7 Einträge ergeben `check-num-1`…`7`, mit `top` im Abstand `px(82)`.
  `test_steps_grid`: 4 Schritte ergeben 2 verschiedene `top`-Werte für `step-num`, 5 Schritte ebenfalls 2.
  `test_bars`: `bar-fill-2.width == round(0.56 * bar-track-2.width)` ± 1.
  `test_quiz_highlight`: answer 1 ergibt `quiz-opt-2` mit Füllung sky, die anderen night2.
  `test_no_glyphs`: Kein Text auf Folien aus `compare_columns` und `summary_items` enthält ✓ oder →.
  `test_layout_per_type`: Ein Plan mit allen 18 Typen ergibt Layoutnamen in Plan-Reihenfolge; quiz ergibt 2 Folien, also 19 insgesamt.
  `test_optional_absent` (Review Focus 5):
  - points mit chapter 3 und ohne kicker: Kicker-Text = „Phase 3 · Apply“.
  - Ohne chapter und kicker: kein idx 11 auf der Folie.
  - Auf keiner Folie bleibt ein Platzhalter ohne Text oder Bild.
  `test_notes`: Notiztext == Plan.
  `test_footer`: Die Fußzeile von Folie 5 endet auf `"· 5"`.
  `test_cli_plan_error`: Ein ungültiger Plan ergibt Exit-Code 2 und `"unknown type"` im stdout.
- [ ] **Step 2:** `pytest tests/test_widgets_content.py tests/test_build.py -v`. Erwartet: FAIL.
- [ ] **Step 3:** `widgets_content.py`, dann `slides.py`, `build.py` und die CLI umsetzen.
- [ ] **Step 4:** Tests ausführen. Erwartet: PASS.
- [ ] **Step 5:** Commit `feat: Inhalts-Widgets, Renderer und build_deck`.

### Task 10: Prüfungen und Rendering

**Files:**
- Create: `scripts/campus/checks.py`, `scripts/campus/render.py`, `skill/flaesh-campus/scripts/check_deck.py`
- Test: `tests/test_checks.py`

**Interfaces:**
- Produces:
  - `@dataclass Issue(slide: int, kind: Literal["overflow", "zone", "empty", "font", "glyph"], shape: str, detail: str)`
  - `check_deck(pptx: Path, spec: dict, m: Measurer) -> list[Issue]`
  - `render_pdf(pptx: Path, outdir: Path, timeout: int = 240) -> Path`: nutzt `/mnt/skills/public/pptx/scripts/office/soffice.py`, falls vorhanden; sonst `soffice --headless -env:UserInstallation=file://<tmp>`.
  - `render_pngs(pdf: Path, outdir: Path, dpi: int = 80) -> list[Path]` über `pdftoppm -png`.
  - CLI: `python scripts/check_deck.py DECK.pptx [--render DIR]` gibt eine Zeile pro Issue aus, z. B. `slide 7 overflow Points: 1040px > 560px`. Exit-Code 1 bei Issues.
  - Ist `m.approximate`, gibt die CLI zuerst aus: `Hinweis: Corporate S fehlt, Prüfung mit Ersatzmaßen – Feinprüfung in PowerPoint nötig`.
- **Regeln:**
  - **Effektive Größe:** `run.font.size`, sonst `spec[layout]["placeholders"][name]["levels"][level]`. Den Namen liefert die Umkehrung von `PH_IDX`.
  - **overflow:** gemessene Höhe > Boxhöhe − Insets + 2 px.
  - **zone:** Folien-Form außer `zone-ring*` schneidet den Kreis aus `zone_circle()`; gilt nicht für „01 Title“. Für 14 Photo ist das Foto selbst ausgenommen.
  - **empty:** Platzhalter ohne Text bzw. Bild.
  - **font:** `latin@typeface` ist nicht leer, nicht „Corporate S“ und nicht `+mj-lt`/`+mn-lt`.
  - **glyph:** Zeichen nicht in der cmap der Schrift (Whitespace ausgenommen); nur wenn `not m.approximate`.

- [ ] **Step 1: Test schreiben**

  `test_zone_violation`: Textbox bei (1600,800) auf einer points-Folie ergibt ein Issue `zone`.
  `test_overflow`: 4 Punkte mit je 30-Wort-Text ergeben `overflow` auf „Points“.
  `test_glyph` (Review Focus 4): Titel „Do → Don't ✓“. `build_deck` läuft durch; die Issues `glyph` nennen → und ✓.
  `test_font`: Ein Lauf mit Arial ergibt ein Issue `font`.
  `test_clean_minimal`: Der minimale Plan ergibt `[]`.
  `test_render_pages` (markiert als slow): Seitenzahl in `pdfinfo` == Anzahl der Folien.
- [ ] **Step 2:** Test ausführen. Erwartet: FAIL.
- [ ] **Step 3:** Umsetzen.
- [ ] **Step 4:** `pytest -v` ausführen. Erwartet: alle PASS.
- [ ] **Step 5:** Commit `feat: check_deck und Rendering`.

### Task 11: Episode 2 und Layout-Galerie: Inhalte, Qualitätsrunde, Lieferung

**Files:**
- Create: `examples/episode-02.json`, `examples/layout-gallery.json`
- Modify: `scripts/make_template.py` (`--gallery`: Galerie-Plan in die frische Vorlage bauen und als Vorlage speichern)
- Output: `assets/template/flaesh-campus-template.pptx` (Layouts + Galerie), `out/episode-02.pptx/.pdf`, `out/flaesh-campus-layouts.pdf`

**Inhaltsregeln:**
- Texte stammen aus dem Projekt-Dokument „R fläsh Ep02 …“. Gekürzt wird nach Spec, Abschnitt 5; der vollständige Originalwortlaut der Folie kommt in die `notes`.
- Fachaussagen und Zahlen bleiben unverändert (32 %, 1 mm, 460 nm, < 39 °C, 3–4 × 15 min, ≈ 50 %).
- Episode:
  - number 2, title „In-Office Whitening Workflow“, subtitle „Step-by-Step Protocol + Common Mistakes“
  - chapters: Document · Protect · Apply · Activate & Monitor · Seal & Instruct
  - presenter: Dr. Germán Gómez; credentials „DDS · MD · PhD (University of Tübingen) · Esthetic Dentistry & Implantology, Spain“ / „500+ lectures · 43 countries“; photo `photos/gomez.jpg`

**Zuordnung Episode 2** (Plan-Folie ← Quellfolie):

| # | Typ | Quelle | Kap. |
|---|---|---|---|
| 1 | cover | 1 | – |
| 2 | hook | 2 | – |
| 3 | points | 3, vier Prinzipien | – |
| 4 | statement | 3, Kennzahl „30 years“ | – |
| 5 | steps | 4, fünf Phasen | – |
| 6 | chapter | Phase 1, Satz aus Folie 6 | 1 |
| 7 | points_photo | 6, Briefing „Professional prophylaxis — before and after“ | 1 |
| 8 | scale | 7, Shade Guide B1…C4, 3 Punkte, Evidence Joiner A., J Dent 2004 | 1 |
| 9 | points + focus | 8 | 1 |
| 10 | chapter | Phase 2, Satz aus Folie 9 | 2 |
| 11 | points_photo | 9, Briefing „Lamp docked on the lip retractor · filtered goggles“, Evidence Li & Greenwall, Br Dent J 2013 | 2 |
| 12 | checklist + focus | 10 | 2 |
| 13 | chapter | Phase 3, Satz aus Folie 11 | 3 |
| 14 | points | 11 | 3 |
| 15 | points_chart | 12, Balken 100/56, Evidence Ontiveros & Paravina, J Dent 2009 | 3 |
| 16 | chapter | Phase 4, Satz aus Folie 13 | 4 |
| 17 | points_photo | 13, Briefing „fläsh lamp touchscreen guiding each cycle“ | 4 |
| 18 | points + focus | 14 | 4 |
| 19 | chapter | Phase 5, Satz aus Folie 15 | 5 |
| 20 | points + focus | 15 | 5 |
| 21 | scale (Zeitstrahl) | 16, Pellikel: minutes · ~2 h · 18–24 h, 2 Punkte, Evidence Hannig M., Clin Oral Investig 1999 | 5 |
| 22–24 | photo | 17, 18, 19 (Briefings je Schritt) | – |
| 25 | case | 20 + 21 | – |
| 26 | steps | 22 | – |
| 27–28 | quiz | neu aus Folie 21: „Cervical thirds still yellow — most likely cause?“, richtig: barrier over-extended onto cervical enamel | – |
| 29 | summary | 23 | – |
| 30 | closing | 24, Up next Episode 3 | – |

**Galerie:** Eine Folie je Layout mit Inhalten aus Episode 2. Für Typen ohne Ep2-Folie:
- compare: Myth „Whitening etches the enamel“ / Fact „Oxidation of chromogens at neutral pH“
- before_after: Briefings „Baseline shade, identical setup“ / „Final shade, identical setup“
- photo_annotated: Briefing „Isolation setup“, Marker lip protection · retractor docked · filtered goggles · cured barrier

- [ ] **Step 1:** `episode-02.json` und `layout-gallery.json` schreiben.
- [ ] **Step 2:** `validate_plan` meldet `[]` für beide Pläne.
- [ ] **Step 3:** Beide bauen. `check_deck` meldet 0 Issues; bei Issues Texte kürzen oder Folien teilen und neu bauen.
- [ ] **Step 4:** `python3 /mnt/skills/public/pptx/scripts/office/validate.py out/episode-02.pptx --original assets/template/flaesh-campus-template.pptx` gibt Exit-Code 0. Dazu `markitdown out/episode-02.pptx | grep -iE "lorem|TODO|xxx"` ohne Treffer.
- [ ] **Step 5:** Rendern und jede Folie ansehen; Prüfliste aus dem pptx-Skill, Abschnitt „Visual QA“. Mängel im Plan oder Code beheben, betroffene Folien neu rendern.
- [ ] **Step 6:** `make_template.py --gallery examples/layout-gallery.json` erzeugt die finale Vorlage. Danach PDFs exportieren.
- [ ] **Step 7:** Commit `feat: Episode 2 und Layout-Galerie`. Dann an Martin liefern: Vorlage, Episode 2 als PPTX und PDF, Layout-PDF, dazu die Fotoliste.

### Task 12 (nach Bennos Feedback): Skill-Paket

**Files:**
- Create: `skill/flaesh-campus/SKILL.md`, `reference/slide-types.md` (Felder + JSON-Beispiel je Typ, aus `layout-spec.json`), `reference/workflow.md`, `scripts/package_skill.sh`

- [ ] **Step 1:** SKILL.md schreiben.
  - **Frontmatter:** name `flaesh-campus`; description: wann verwenden (fläsh Campus, Dr. Gómez, Trainingsvideo-Folien).
  - **Ablauf:** Input lesen (markitdown für PPTX) → Folienplan → `build_deck` → `check_deck` → rendern und ansehen → liefern (PPTX + Fotoliste + Kürzungen).
  - **Inhalt:** Regeln aus Spec, Abschnitt 5; Befehle; Fehlerfälle aus Spec, Abschnitt 6.
- [ ] **Step 2:** Paket bauen: `package_skill.sh` erzeugt `out/flaesh-campus-skill.zip`. Schriftdateien nur, wenn die Lizenz geklärt ist.
- [ ] **Step 3:** Abnahme: frische Claude-Sitzung mit dem Skill, Eingabe nur der Episode-2-Text.
  - Erwartet: Deck ohne Issues; Sichtprüfung ohne Mängel; Folientypen vergleichbar mit `episode-02.json`.
- [ ] **Step 4:** GitHub-Repo anlegen bzw. pushen (Martins Konto), Commit `feat: Skill-Paket fläsh Campus`.
