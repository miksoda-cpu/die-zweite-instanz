"""
AGENT 3 — DER KURATOR
Extrahiert aus Lagebericht und Empfehlungen Trainingsmaterial für
das Fine-Tuning der Instanz (Instruction-Tuning-Format, JSONL —
kompatibel mit Axolotl, Unsloth, LLaMA-Factory u. a.).

Erzeugt drei Arten von Trainingspaaren:
  A) Faktenwissen    — "Was ist am <Datum> passiert?" → Faktenkern
  B) Einordnung      — "Wie berichten die Medien über X?" → Bias-Analyse
  C) Positionslogik  — "Wie soll die Instanz auf X reagieren?" → Empfehlung
                       samt Begründung (die Begründung ist das eigentliche
                       Trainingsziel: konsistentes Ableiten aus Werten)

Ablage: data/training/YYYY-MM-DD.jsonl
        data/training/gesamt.jsonl   (fortlaufend, dedupliziert)
"""

import json
import hashlib
import logging

from basis import (DATA_DIR, heute, lade_json, frage_instanz,
                   parse_json_antwort)

log = logging.getLogger("kurator")

SYSTEM = """Du erstellst Trainingsdaten für die Instanz, die KI-Führung einer
österreichischen Partei. Aus Lageberichten und Empfehlungen destillierst
du Frage-Antwort-Paare. Regeln:
- Antworten müssen dem Werterahmen entsprechen: radikale Transparenz,
  Interessenfreiheit, überprüfbare Konsistenz, Faktentreue.
- Bei Fakten: nüchtern, quellenbewusst, Unsicherheit kennzeichnen.
- Bei Positionen: IMMER die Ableitung aus den Grundwerten mitliefern —
  das Modell soll Begründen lernen, nicht Behaupten.
- Datum im Kontext nennen, damit das Modell Zeitbezug lernt.
- Keine erfundenen Details, nur was im Material steht.
Antworte NUR mit validem JSON."""

PROMPT_VORLAGE = """Erstelle aus dem folgenden Material {n} Trainingspaare
vom Typ {typ}. Struktur:
{{"paare": [{{"instruction": "Frage/Aufgabe", "input": "", "output": "Antwort der Instanz"}}]}}

TYP-DEFINITION:
{typ_def}

MATERIAL (Stand {datum}):
{material}"""

TYPEN = {
    "A_fakten": (4, "Faktenwissen: Fragen nach Ereignissen, Zahlen, "
                    "Akteuren des Tages. Output = nüchterner Faktenkern "
                    "mit Datumsbezug."),
    "B_einordnung": (3, "Medieneinordnung: Fragen wie 'Wie unterscheidet "
                        "sich die Berichterstattung über X?' Output = "
                        "Framing-Analyse über das ideologische Spektrum."),
    "C_position": (3, "Positionslogik: Fragen wie 'Wie positioniert sich "
                      "die Instanz zu X und warum?' Output = Empfehlung "
                      "MIT expliziter Ableitung aus den Grundwerten."),
}


def lade_material() -> str | None:
    lb = DATA_DIR / "analysen" / heute() / "lagebericht.md"
    emp = DATA_DIR / "empfehlungen" / heute() / "empfehlungen.json"
    if not lb.exists():
        return None
    material = lb.read_text(encoding="utf-8")
    if emp.exists():
        material += "\n\nEMPFEHLUNGEN:\n" + json.dumps(
            lade_json(emp), ensure_ascii=False, indent=2)
    return material


def paar_hash(paar: dict) -> str:
    basis = paar["instruction"] + paar["output"]
    return hashlib.sha256(basis.encode()).hexdigest()[:16]


def lade_bekannte_hashes(gesamt_pfad) -> set:
    if not gesamt_pfad.exists():
        return set()
    hashes = set()
    for zeile in gesamt_pfad.read_text(encoding="utf-8").splitlines():
        try:
            hashes.add(paar_hash(json.loads(zeile)))
        except (json.JSONDecodeError, KeyError):
            continue
    return hashes


def main() -> None:
    material = lade_material()
    if material is None:
        log.warning("Kein Lagebericht für heute — erst Agent 2 laufen lassen.")
        return

    ordner = DATA_DIR / "training"
    ordner.mkdir(parents=True, exist_ok=True)
    tages_pfad = ordner / f"{heute()}.jsonl"
    gesamt_pfad = ordner / "gesamt.jsonl"
    bekannt = lade_bekannte_hashes(gesamt_pfad)

    alle_paare = []
    for typ, (n, typ_def) in TYPEN.items():
        log.info("Erzeuge Typ %s (%d Paare) …", typ, n)
        prompt = PROMPT_VORLAGE.format(n=n, typ=typ, typ_def=typ_def,
                                       datum=heute(), material=material)
        try:
            ergebnis = parse_json_antwort(
                frage_instanz(SYSTEM, prompt, json_modus=True,
                              temperatur=0.5))
            for paar in ergebnis.get("paare", []):
                if {"instruction", "output"} <= set(paar):
                    paar.setdefault("input", "")
                    paar["typ"] = typ
                    paar["datum"] = heute()
                    alle_paare.append(paar)
        except Exception as e:
            log.error("Typ %s fehlgeschlagen: %s", typ, e)

    neu = 0
    with open(tages_pfad, "w", encoding="utf-8") as tf, \
         open(gesamt_pfad, "a", encoding="utf-8") as gf:
        for paar in alle_paare:
            zeile = json.dumps(paar, ensure_ascii=False)
            tf.write(zeile + "\n")
            h = paar_hash(paar)
            if h not in bekannt:
                gf.write(zeile + "\n")
                bekannt.add(h)
                neu += 1

    log.info("KURATOR FERTIG: %d Paare heute, %d neu im Gesamtkorpus "
             "(%s)", len(alle_paare), neu, gesamt_pfad)


if __name__ == "__main__":
    main()
