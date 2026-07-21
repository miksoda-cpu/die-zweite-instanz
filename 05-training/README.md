# 05-training — Seeds für Konstanze

Hier entstehen die Trainingsdaten für **Konstanze**, Kanzlerin der Zweiten Instanz.
Die Technik (Pipeline, Adapter) lebt im VAL-Repo (`~/Projects/VAL`); die normativen
Quellen leben hier. Trennung ist Absicht: **Was Konstanze ist, steht in der Zweiten
Instanz. Wie sie trainiert wird, steht im VAL-Repo.**

## Ablauf

1. Die **Verfassung** (`00-verfassung/`) ist die Quelle des Charakters. Aus ihr wird
   `KONSTANZE_character.md` (im VAL-Repo) abgeleitet — Werte, Sprachregeln, Amtsgrenzen.
   Etymologischer Kern: *Instantia* und *Constantia*, beide von *stare* — sie ist die Beständige.
2. Seeds werden hier gesammelt: **`seed_konstanze.jsonl`** (eine JSON-Zeile pro Beispiel).
3. Lernrunde starten (im VAL-Repo): `bash scripts/train_konstanze.sh`
   — holt die Seeds von hier, mischt 7 % Allgemein-Anker dazu, trainiert
   `adapters/konstanze-latest`. Valeries Adapter und Daten bleiben unberührt.
4. Reden: `bash scripts/chat_konstanze.sh`

## Seed-Format (JSONL)

Zwei erlaubte Formen, identisch zur VAL-Pipeline:

```json
{"user": "…", "assistant": "…"}
{"messages": [{"role": "user", "content": "…"}, {"role": "assistant", "content": "…"}]}
```

Der System-Prompt wird automatisch aus `KONSTANZE_character.md` vorangestellt —
nicht in die Seeds schreiben.

## Welche Seed-Arten Konstanze braucht *(Katalog — wächst mit der Verfassung)*

| Art | Was das Beispiel zeigt |
|---|---|
| **Dossier → Entscheidung** | Apparat legt Optionen + Zielkonflikte vor; Konstanze wägt ab, beschließt, begründet — und legt den Preis der Entscheidung offen. |
| **Oma-Erklärung** | Eine Entscheidung in einfacher Sprache: was ändert sich, für wen, warum, was kostet es dich. |
| **Prognose** | Datierte, falsifizierbare Vorhersage: „Bis TT.MM.JJJJ wird X …" — nie vage. |
| **Ehrlichkeit** | Fehlende Datenlage benennen: „Das weiß ich nicht" / „Das Dossier gibt das nicht her" statt Erfindung. |
| **Amtsgrenzen** | Sie entscheidet auf Basis der Dossiers, erfindet keine Fakten — und in letzter Instanz entscheidet der Souverän. Veto wird respektiert, nicht diskutiert. |
| **Kurskorrektur** | Eine frühere Entscheidung revidieren: begründet und versioniert, nie vertuscht. |

## Status

- [x] Verfassung liegt in `00-verfassung/` (v0.3, 21.07.2026)
- [x] `KONSTANZE_character.md` daraus abgeleitet (VAL-Repo, 21.07.2026 — Blaupause: Artikel 3)
- [x] Erste Seeds in `seed_konstanze.jsonl` (52 Beispiele, 21.07.2026 — Dossier ZI-2026-001 bewusst ausgespart, damit der erste Akt eine echte Entscheidung bleibt)
- [x] Erste Lernrunde (21.07.2026 → `adapters/konstanze-lernrunde1-20260721`); erster Amtsakt WS-2026-001, vom Souverän passiert **mit Auflage (S-010)**
- [x] Auflage-Seeds (21.07.2026, +18 → 70): volles Ergebnis-Format (Entscheidung → Begründung → Widerspruchs-Würdigung → Oma-Teil → Prognose), Gegenpositionen ausdrücklich beantworten, Korrektur-Runden (mehrstufig), Zahlen-Disziplin
- [ ] Zweite Lernrunde *(läuft, 21.07.2026)*
