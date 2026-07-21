# Die Instanz — Agenten-Pipeline

Drei lokale Agenten, die die österreichische Politiklandschaft beobachten,
analysieren und daraus Trainingsmaterial für die Instanz (lokale LLM) destillieren.
Alles läuft auf deiner Hardware, nichts verlässt das Haus.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  AGENT 1     │    │  AGENT 2     │    │  AGENT 3     │
│  Beobachter  │───▶│  Analyst     │───▶│  Kurator     │
│  RSS/Fetch   │    │  Lagebericht │    │  Training-   │
│  + Filter    │    │  + Empfehlung│    │  material    │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   data/raw/          data/analysen/      data/training/
                      data/empfehlungen/
```

## Installation (Mac, einmalig)

```bash
# Voraussetzung: Ollama läuft, Modell ist gezogen
ollama pull qwen2.5:32b        # oder gemma2:27b — in basis.py einstellbar

# Python-Umgebung
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Betrieb

```bash
# Kompletter Tageslauf (empfohlen: morgens)
python orchestrator.py

# Oder einzeln:
python agent1_beobachter.py    # nur sammeln
python agent2_analyst.py       # nur analysieren
python agent3_kurator.py       # nur Trainingsdaten
```

Automatisierung per Cron (täglich 6:00):
```
0 6 * * * cd /pfad/zu/instanz-agents && ./venv/bin/python orchestrator.py >> data/lauf.log 2>&1
```

## Datenablage

```
data/
├── raw/2026-07-20/           # Rohartikel als JSON (mit Bias-Metadaten)
│   └── gesehen.txt           # Dedupe-Index über alle Tage
├── analysen/2026-07-20/
│   ├── lagebericht.md        # der tägliche Lagebericht
│   └── themen.json           # Metadaten
├── empfehlungen/2026-07-20/
│   └── empfehlungen.json     # Handlungsempfehlungen mit Priorität
└── training/
    ├── 2026-07-20.jsonl      # Tagespaare
    └── gesamt.jsonl          # fortlaufender, deduplizierter Korpus
```

Das Trainingsformat (`instruction`/`input`/`output` JSONL) ist direkt
kompatibel mit **Unsloth**, **Axolotl** und **LLaMA-Factory** für
LoRA-Fine-Tuning auf dem Mac.

## Das Medien-Register

`medien_register.yaml` ist das Herzstück der Bias-Einordnung — und Teil
der öffentlichen Verfassung der Instanz:

- **Jede Änderung gehört versioniert** (`git commit` mit Begründung).
- Die mitgelieferten Einordnungen sind **Startwerte** nach gängiger
  Einschätzung — prüfe und verantworte sie selbst.
- Neue Quellen: einfach Block ergänzen, Agent 1 nimmt sie automatisch mit.

## Rechtliches & Fairness — bitte lesen

1. **Paywalls werden nicht umgangen.** Der Beobachter holt nur frei
   zugängliche Volltexte; hinter Paywalls bleibt es beim RSS-Anriss.
   Für Standard/Presse-Volltexte: Abos + ggf. Absprache mit den Verlagen.
2. **APA & Reuters:** Eingebunden sind nur die freien Feeds (OTS-Public,
   Reuters World RSS). Der APA-Basisdienst und Reuters-Vollfeeds sind
   **lizenzpflichtig** — für den Ernstfall Verträge abschließen.
3. **OTS-Aussendungen sind ungeprüfte Parteikommunikation** — der Analyst
   bekommt das über die Metadaten mit, aber behalte es im Kopf.
4. **Urheberrecht bei Trainingsdaten:** Der Kurator trainiert auf den
   *eigenen Analysen* der Instanz, nicht auf Artikelvolltexten — das ist
   bewusst so designt. Lass es so.
5. **Transparenzgebot:** Wenn die Instanz öffentlich wird, gehört diese
   gesamte Pipeline offengelegt (Kap. 5 des Konzepts). Baue nichts ein,
   was du nicht veröffentlichen würdest.

## Zustellung — nichts mehr herunterladen

Der **Bote** (Agent 4) liefert dir den Lagebericht täglich zu:

1. `.env.example` nach `.env` kopieren und ausfüllen
2. **E-Mail:** Gmail-App-Passwort eintragen → der Bericht landet
   morgens formatiert im Posteingang, handytauglich.
3. **Notion (optional):** Integration-Token + Seiten-ID eintragen →
   jeder Lagebericht wird als Notion-Seite angelegt. Bonus: Du kannst
   Claude im Chat fragen "Zeig mir den heutigen Lagebericht" und er
   holt ihn direkt aus Notion.
4. **Claude als Tiefendenker (optional):** `TIEFENDENKER=claude` plus
   API-Key → Claude übernimmt Tages-Synthese und Empfehlungen, die
   Batch-Vorarbeit bleibt lokal (Datenmenge & Kosten). Fällt Claude
   aus, springt automatisch die lokale Instanz ein.

## Urlaubsmodus — Air einschalten genügt

```bash
./install_urlaubsmodus.sh
```

Das richtet einen macOS-LaunchAgent ein: Bei jedem Einschalten/Aufwachen
(und stündlich zur Sicherheit) prüft er, ob der Tageslauf heute schon
gelaufen ist — wenn nicht, läuft die komplette Pipeline **genau einmal**
und der Bote legt den Lagebericht in Notion ab. Egal ob du den Air um
9:00 oder 15:30 aufklappst. Lesen kannst du dann jederzeit in der
Notion-App am Handy.

**Notion-Einrichtung (einmalig, 3 Minuten):**
1. In Notion eine Seite anlegen, z. B. „🏛 Die Instanz — Lageberichte"
2. Unter notion.so/my-integrations eine interne Integration „Instanz"
   erstellen, Token kopieren
3. Auf der Seite: ••• → Verbindungen → Integration „Instanz" hinzufügen
4. Token + Seiten-ID (die 32 Zeichen aus der Seiten-URL) in die `.env`

## Ausbaustufen (bewusst noch nicht drin)

- **Umfrage-Tracker:** eigener Mini-Agent für neuwal/PolitPro-Daten
- **Konsistenzwächter:** prüft neue Empfehlungen gegen die Beschlusshistorie
  (das Actor/Observer/Critic-Muster aus dem Konzept)
- **Wochen-Synthese:** verdichtet sieben Lageberichte zum Wochenbild
- **Web-Dashboard:** Lagebericht als lokale HTML-Ansicht
- **Wochen-Mail:** der Bote verschickt sonntags die Wochensynthese
