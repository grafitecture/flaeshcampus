# fläsh Campus – Präsentationsvorlage und Claude-Skill

Konzept · Stand 19.10.2026 · Status: zur Freigabe durch Martin
Auftraggeber: Benno Walter (WHITEsmile GmbH) · Umsetzung: Martin Schweppe (Grafitecture)

## 1. Ziel

fläsh Campus ist eine Serie von 12–13 Trainingsvideos à rund 15 Minuten mit Dr. Germán Gómez, zusammen etwa drei Stunden und rund 300 Folien. Benno möchte dafür:

1. ein eigenes Präsentationslayout – nicht das klassische WHITEsmile-Layout, sondern einen Campus-Look auf Basis der fläsh-Marke, mit Bildseiten, Grafiken und erklärenden Elementen;
2. einen Claude-Skill, wie Andreas ihn für die bisherige Vorlage gebaut hat: Inhalte rein, PowerPoint im Layout 1:1 raus.

Erfolgskriterien:

- Benno gibt die Inhalte einer Episode ein und bekommt eine fertige PowerPoint ohne Nacharbeit am Layout.
- Alle Folien sind im Video gut lesbar.
- Der Platz für Dr. Gómez' Videoeinblendung ist auf keiner Folie verdeckt.
- Benno und Dr. Gómez können in PowerPoint auch von Hand mit denselben Layouts arbeiten.

## 2. Rahmenbedingungen

| Thema | Festlegung |
|---|---|
| Format | 16:9, 13,333 × 7,5 Zoll; Raster 1920 × 1080 px (1 pt = 2 px) |
| Sprache der Folien | Englisch wie Episode 2 *(Annahme)* |
| Aufnahme | Dr. Gómez wird im Schnitt rund eingeblendet, unten rechts |
| Farben (flaesh.com) | Blaugrau #5D6C73 · Himmelblau #00A5FF · Stahl #ABB7BE · Nebel #DEE7EC · Text #333333 · Weiß |
| Campus-Ergänzung | Nacht #1F272B (dunkle Flächen) · Nacht 2 #283237 (Karten auf dunkel) · Leiste #192024 |
| Schrift | Corporate S (URW). Regular liegt vor, **Bold fehlt noch** |
| Logo | fläsh-Wortmarke als SVG (Blaugrau und Weiß), Zusatz „Campus“ in Himmelblau |

Zur Schrift:

- Die Lizenz-Kennung der Schriftdatei erlaubt in PowerPoint nur das Einbetten zum Ansehen und Drucken. Wer Folien bearbeitet, braucht Corporate S installiert.
- Die Zeichen ✓ → ▸ ● ○ fehlen in der Schrift. Haken, Pfeile, Aufzählungszeichen und Nummernkreise werden deshalb als Formen gezeichnet.

## 3. Look: „Campus-Mix mit Leuchten“ (freigegeben)

Referenzen: `assets/look-campus-mix-glow.png` und `assets/cover-with-portrait.png`.

- **Dunkle Rahmenfolien:** Titel, Kapitel, Einstieg und Abschluss auf Nacht-Hintergrund mit blauem Leuchten. Das Leuchten greift das 460-nm-Licht der Lampe auf.
- **Helle Inhaltsfolien** auf Weiß mit dunkler Leiste links (150 px). Die Leiste zeigt oben die Episode („EP 02“), in der Mitte den Fortschritt durch die 2–6 Kapitel der Episode und unten das fläsh-Logo. Das aktuelle Kapitel leuchtet.
- **Titelfolie:** Porträt von Dr. Gómez im großen Kreis (Ø 580 px) mit leuchtendem Ring und feinen Lichtringen. Der Untertitel bricht spätestens bei 820 px um, damit er die Ringe nicht kreuzt.
- **Kreis für die Videoeinblendung:** Ø 300 px mit 56 px Abstand unten und rechts, also x 1564–1864 und y 724–1024. Er ist auf allen Folien außer der Titelfolie frei und als leuchtender Ring markiert.
- **Typografie:**
  - Titel 39 pt
  - Punkt-Überschrift 21 pt, Erklärung 17 pt
  - Kicker 14 pt in Versalien, gesperrt, Himmelblau
  - Evidence 13 pt, Fußzeile 11 pt
  - Kapitelziffer sehr groß in Himmelblau
- **Akzente:** Himmelblau für Nummern, Kicker, aktiven Zustand und Leuchten. Fokus-Boxen sind auf hellen Folien dunkel mit leuchtendem Rand.

## 4. Folientypen (18 Layouts)

Jedes Layout existiert als echtes PowerPoint-Layout im Folienmaster. Der Name im Master und der Schlüssel im Folienplan sind fest.

| # | Layout (Master) | Schlüssel | Inhalt |
|---|---|---|---|
| 1 | 01 Title | `cover` | Episode, Titel, Untertitel, Dr. Gómez (Name, Titel, Porträt) |
| 2 | 02 Chapter | `chapter` | Kapitelnummer, Kapitelname, ein Satz |
| 3 | 03 Hook | `hook` | Zitat oder Frage, Problem („The hard truth“), fläsh-Antwort |
| 4 | 04 Closing | `closing` | Bis zu 4 nächste Schritte, Hinweis auf die nächste Episode |
| 5 | 05 Points | `points` | 2–4 Punkte mit Kurztitel und Erklärung, die Standardfolie |
| 6 | 06 Points + Photo | `points_photo` | Wie 5, plus Foto mit Bildunterschrift |
| 7 | 07 Points + Chart | `points_chart` | Wie 5, plus Grafik (Balken, Skala, Werte) |
| 8 | 08 Statement | `statement` | Große Zahl oder Merksatz mit kurzer Erklärung |
| 9 | 09 Checklist | `checklist` | Bis zu 7 nummerierte Punkte, optional mit Fokus-Box |
| 10 | 10 Steps | `steps` | 3–5 nummerierte Schritte mit Titel und Text |
| 11 | 11 Compare | `compare` | Zwei Spalten: richtig/falsch oder Mythos/Fakt |
| 12 | 12 Scale | `scale` | Skala (z. B. Shade Guide) oder Zeitstrahl (z. B. Pellikel) |
| 13 | 13 Summary | `summary` | Bis zu 5 Punkte mit Haken |
| 14 | 14 Photo | `photo` | Foto über die ganze Fläche rechts der Leiste, mit Bildunterschrift |
| 15 | 15 Before / After | `before_after` | Zwei Fotos mit Beschriftung, z. B. Farbwert |
| 16 | 16 Photo Annotated | `photo_annotated` | Foto mit bis zu 5 nummerierten Markierungen |
| 17 | 17 Case | `case` | Fallbeschreibung und bis zu 5 Befunde mit Ursache |
| 18 | 18 Quiz | `quiz` | Frage mit 3 Antworten, Auflösung auf der Folgefolie |

Inhalts- und Bildfolien tragen die Leiste. Rahmenfolien nutzen dieselbe Leiste in dunkel, die Titelfolie nur mit der Episodennummer.

## 5. Gestaltungsregeln

1. Der Kreis unten rechts bleibt frei, außer auf der Titelfolie.
2. Pro Folie höchstens 4 Punkte. Der Titel passt in eine Zeile mit maximal 6–7 Wörtern, eine Erklärung hat maximal etwa 14 Wörter.
3. Was nicht passt, kommt in die Sprecher-Notizen oder auf eine Folgefolie. Inhalt wird nie verkleinert, um ihn hineinzuquetschen.
4. Quellen stehen als „Evidence“ unten links, nur die Kurzangabe (Autor, Zeitschrift, Jahr).
5. Fehlt ein Foto, entsteht ein Platzhalter mit Bildbriefing, z. B. „Foto: Lampe am Retraktor angedockt“. Alle Briefings werden zusätzlich als Liste ausgegeben.
6. Symbole (Haken, Pfeile, Nummern, Aufzählungszeichen) sind Formen, keine Schriftzeichen.
7. Fachliche Aussagen werden nicht verändert, nur gekürzt oder umverteilt.

## 6. Technischer Aufbau (freigegeben: „Vorlage + Befüllen“)

Die Vorlage ist die Referenz. Martin kann Layouts direkt in PowerPoint verfeinern, der Skill übernimmt solche Änderungen automatisch.

```
flaesh-campus/
├── template/flaesh-campus-template.pptx   Folienmaster + 18 Layouts mit benannten Platzhaltern
├── template/layout-spec.json              feste Maße: Leiste, Kreis-Zone, Raster, Platzhalter je Layout
├── assets/                                Logos (SVG/PNG, weiß/blaugrau), Leucht-Ebenen (PNG), Formen
├── scripts/make_template.*                erzeugt die Vorlage reproduzierbar (Ersterstellung)
├── scripts/build_deck.py                  Folienplan (JSON) → PowerPoint
├── scripts/check_deck.py                  Prüfung: Textlänge, Kreis-Zone, Render als Bilder
├── examples/episode-02.json               vollständiger Folienplan für Episode 2
└── skill/flaesh-campus/                   Skill-Paket: SKILL.md, Referenz der Folientypen, Vorlage, Scripts
```

### Ablauf

1. **Input:** Claude liest die Episode: PowerPoint, Skript oder Stichpunkte.
2. **Folienplan:** Claude erstellt einen Folienplan als JSON. Er enthält die Episodendaten (Nummer, Titel, Kapitel) und je Folie Typ, Kapitel, Felder und Notizen. Ein Schema prüft Pflichtfelder und Höchstlängen.
3. **Bau:** `build_deck.py` (python-pptx) öffnet die Vorlage, legt jede Folie über den Layout-Namen an und füllt die Platzhalter. Dynamisches zeichnet das Script:
   - Fortschritt in der Leiste
   - Balken und Skalen
   - Nummernkreise und Haken
   - Bildplatzhalter
   - Sprecher-Notizen
4. **Leuchten:**
   - Ringe, Punkte und Fokus-Boxen bekommen den PowerPoint-Effekt „Leuchten“.
   - Flächiges Leuchten im Hintergrund ist eine Ellipse mit radialem Farbverlauf in den dunklen Layouts.
5. **Prüfung:** `check_deck.py` misst jeden Text mit den echten Schriftmaßen von Corporate S. Es meldet:
   - Text, der überläuft
   - Elemente in der Kreis-Zone
   - leere Platzhalter
   - fremde Schriften

   Außerdem rendert es die Folien über LibreOffice als Bilder für die Sichtprüfung.
6. **Ausgabe:** PowerPoint, Liste der fehlenden Fotos und eine kurze Zusammenfassung der Kürzungen.

### Fehlerbehandlung

| Fall | Reaktion |
|---|---|
| Unbekannter Folientyp oder fehlendes Pflichtfeld | Build bricht mit klarer Meldung je Folie ab; Claude korrigiert den Folienplan und baut neu |
| Text zu lang | Claude kürzt oder teilt die Folie und baut neu. Die Schriftgröße wird nicht verkleinert |
| Foto fehlt oder ist zu klein | Platzhalter mit Briefing, Eintrag in der Fotoliste |
| Schrift im Prüf-System nicht vorhanden | Prüfung mit Ersatzmaßen, Hinweis, dass die Feinprüfung in PowerPoint nötig ist |

### Tests

- Episode 2 vollständig bauen und mit den freigegebenen Entwürfen vergleichen.
- Automatische Prüfungen laufen bei jedem Bau.
- Für die Skill-Abnahme: Episode 2 aus dem reinen Text neu erzeugen, ohne Handarbeit.

## 7. Arbeitsablauf für Benno

1. In Claude, mit installiertem Skill: Episode-Inhalt hochladen oder einfügen, Episodennummer nennen.
2. Claude baut die Präsentation und prüft sie.
3. Benno bekommt die PowerPoint, die Fotoliste für Dr. Gómez und die Notizen mit dem Text, der nicht auf die Folien passte.
4. Korrekturen per Nachricht, etwa „Folie 7 als Vergleich“. Claude baut dann neu.

## 8. Lieferumfang und Zeitplan

**Bis zum Termin bei Benno, Freitag 23.10.2026:**

1. `flaesh-campus-template.pptx` mit allen 18 Layouts.
2. Episode 2 komplett im neuen Look, rund 24 Folien, als PowerPoint und PDF. Gebaut mit `build_deck.py`, also schon so, wie der Skill später liefert.

**Nach Bennos Feedback:**

3. Skill-Paket fertigstellen und testen: Episode 2 aus dem Rohtext neu erzeugen.
4. Übergabe als ZIP an Benno bzw. Andreas, Versionen auf GitHub.

## 9. Offene Punkte

- **Corporate S Bold** und ggf. weitere Schnitte. Bis dahin wird nur mit Regular gearbeitet, Hervorhebung über Farbe und Größe.
- **Fotos:** Das Porträt liegt vor (768 px, reicht für die Titelfolie). Klinische Fotos fehlen, bis dahin gibt es Platzhalter mit Briefing.
- **Schriftlizenz** für Dr. Gómez' Rechner und für das Skill-Paket. Das klärt Benno.
- **Optional:** Andreas' bestehender Skill als Vorbild für Bedienung und Paketstruktur.

## 10. Nicht im Umfang

- Website oder Styleguide-Seite (Variante C verworfen)
- Animationen und Übergänge; das übernimmt der Videoschnitt
- Einsetzen des Videos von Dr. Gómez; macht der Schnitt
- Übersetzungen; die Layouts vertragen aber auch deutsche oder spanische Texte
- Erzeugen von Bildern per KI
