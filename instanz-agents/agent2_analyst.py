"""
AGENT 2 — DER ANALYST
Liest die Tagesernte des Beobachters, ordnet die Berichterstattung
unter Berücksichtigung der ideologischen Ausrichtung der Quellen ein
und entwickelt Handlungsempfehlungen für die Instanz.

Ablage:
  data/analysen/YYYY-MM-DD/lagebericht.md
  data/analysen/YYYY-MM-DD/themen.json
  data/empfehlungen/YYYY-MM-DD/empfehlungen.json
"""

import logging
from pathlib import Path

from basis import (DATA_DIR, heute, tages_ordner, lade_json,
                   speichere_json, frage_instanz, denker,
                   parse_json_antwort)

log = logging.getLogger("analyst")

MAX_ARTIKEL_PRO_BATCH = 15
MAX_ZEICHEN_PRO_ARTIKEL = 1200

SYSTEM_ANALYSE = """Du bist der Analyse-Agent der Instanz, einer österreichischen
Partei mit KI-Führung. Deine Aufgaben:
1. Medienberichte NIE für bare Münze nehmen. Jede Quelle hat eine
   ideologische Ausrichtung (Skala -2 links bis +2 rechts) und eine
   Verlässlichkeit (1-5). Beides ist angegeben. Gewichte entsprechend:
   Übereinstimmende Darstellung quer über das Spektrum = wahrscheinlich
   Faktenkern. Darstellung nur an einem Rand = als Framing kennzeichnen.
2. Trenne strikt: FAKTENKERN / FRAMING JE LAGER / OFFENE FRAGEN.
3. Sei nüchtern, präzise, ohne eigene Ideologie. Deine einzige
   Loyalität gilt der überprüfbaren Wahrheit und dem Wohl des Souveräns,
   wie es die Verfassung der Instanz definiert.
Antworte ausschließlich auf Deutsch."""

SYSTEM_EMPFEHLUNG = """Du bist der Strategie-Agent der Instanz, einer neuen
österreichischen Partei mit KI-Führung. Grundwerte: radikale Transparenz,
Interessenfreiheit, überprüfbare Konsistenz, Dienst am Souverän.
Positionierung: unbesetzter Raum zwischen Protest (derzeit FPÖ-dominiert)
und Establishment — Wut in Kontrolle übersetzen statt in Abrissbirne.
Entwickle aus der Tagesanalyse konkrete Handlungsempfehlungen.
Jede Empfehlung braucht: These, Begründung, Kanal, Risiko, Priorität (1-3).
Bleibe im Rahmen demokratischer, legaler, transparenter Mittel.
Keine Desinformation, keine verdeckten Kampagnen — die Instanz gewinnt
durch Offenheit oder gar nicht. Antworte ausschließlich auf Deutsch."""


def lade_tagesartikel() -> list:
    ordner = DATA_DIR / "raw" / heute()
    if not ordner.exists():
        return []
    return [lade_json(p) for p in sorted(ordner.glob("*.json"))]


def artikel_block(a: dict) -> str:
    text = a["volltext"][:MAX_ZEICHEN_PRO_ARTIKEL] or a["anriss"][:400]
    return (f"[{a['quelle_name']} | Ausrichtung {a['ausrichtung']:+d} | "
            f"Verlässlichkeit {a['verlaesslichkeit']}/5 | {a['region']}]\n"
            f"TITEL: {a['titel']}\nTEXT: {text}\n")


def analysiere_batch(batch: list, nr: int) -> str:
    bloecke = "\n---\n".join(artikel_block(a) for a in batch)
    prompt = (f"Hier ist Batch {nr} der heutigen Politik-Berichterstattung "
              f"({len(batch)} Artikel). Erstelle eine verdichtete Analyse:\n"
              f"1. Die 3-5 wichtigsten Ereignisse/Themen\n"
              f"2. Je Thema: Faktenkern vs. Framing der verschiedenen Lager\n"
              f"3. Auffällige Leerstellen (worüber wird NICHT berichtet?)\n\n"
              f"{bloecke}")
    return frage_instanz(SYSTEM_ANALYSE, prompt)


def synthetisiere(teilanalysen: list) -> str:
    zusammen = "\n\n=====\n\n".join(teilanalysen)
    prompt = ("Hier sind Teilanalysen des heutigen Tages. Verdichte sie zu "
              "EINEM Lagebericht mit den Abschnitten:\n"
              "## Lage des Tages (max. 5 Sätze)\n"
              "## Themen im Detail (Faktenkern / Framing / offene Fragen)\n"
              "## Stimmungsbild über das Medienspektrum\n"
              "## Leerstellen\n\n" + zusammen)
    return denker(SYSTEM_ANALYSE, prompt)


def empfehle(lagebericht: str) -> dict:
    prompt = ("Hier der heutige Lagebericht. Entwickle daraus 3-6 "
              "Handlungsempfehlungen für die Instanz.\n"
              "Antworte NUR mit validem JSON in dieser Struktur:\n"
              '{"empfehlungen": [{"these": "...", "begruendung": "...", '
              '"kanal": "...", "risiko": "...", "prioritaet": 1}]}\n\n'
              + lagebericht)
    return parse_json_antwort(
        denker(SYSTEM_EMPFEHLUNG, prompt, json_modus=True))


def main() -> None:
    artikel = lade_tagesartikel()
    if not artikel:
        log.warning("Keine Artikel für heute — erst Agent 1 laufen lassen.")
        return
    log.info("Analysiere %d Artikel …", len(artikel))

    batches = [artikel[i:i + MAX_ARTIKEL_PRO_BATCH]
               for i in range(0, len(artikel), MAX_ARTIKEL_PRO_BATCH)]
    teilanalysen = [analysiere_batch(b, i + 1) for i, b in enumerate(batches)]

    lagebericht = (synthetisiere(teilanalysen)
                   if len(teilanalysen) > 1 else teilanalysen[0])

    analyse_ordner = tages_ordner("analysen")
    (analyse_ordner / "lagebericht.md").write_text(
        f"# Lagebericht der Instanz — {heute()}\n\n{lagebericht}\n",
        encoding="utf-8")
    speichere_json(analyse_ordner / "themen.json", {
        "datum": heute(),
        "artikel_gesamt": len(artikel),
        "quellen": sorted({a["quelle_name"] for a in artikel}),
        "teilanalysen": len(teilanalysen),
    })

    log.info("Entwickle Handlungsempfehlungen …")
    empfehlungen = empfehle(lagebericht)
    empfehlungen["datum"] = heute()
    speichere_json(tages_ordner("empfehlungen") / "empfehlungen.json",
                   empfehlungen)

    log.info("ANALYST FERTIG: Lagebericht + %d Empfehlungen",
             len(empfehlungen.get("empfehlungen", [])))


if __name__ == "__main__":
    main()
