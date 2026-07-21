"""
ORCHESTRATOR — Der Tageslauf der Instanz
Führt die drei Agenten in Reihenfolge aus:
  1. Beobachter (Medien sammeln)
  2. Analyst   (Lagebericht + Empfehlungen)
  3. Kurator   (Trainingsmaterial)

Aufruf:  python orchestrator.py                 # sofort laufen
         python orchestrator.py --wenn-faellig   # nur wenn heute noch nicht gelaufen
                                                 # (für den LaunchAgent / Urlaubsmodus)
"""

import logging
import sys
import time
from pathlib import Path
from datetime import date

import agent1_beobachter
import agent2_analyst
import agent3_kurator
import agent4_bote

log = logging.getLogger("orchestrator")


STEMPEL = Path(__file__).parent / "data" / "letzter_lauf.txt"


def heute_schon_gelaufen() -> bool:
    return STEMPEL.exists() and STEMPEL.read_text().strip() == date.today().isoformat()


def stemple() -> None:
    STEMPEL.parent.mkdir(parents=True, exist_ok=True)
    STEMPEL.write_text(date.today().isoformat())


def main() -> None:
    if "--wenn-faellig" in sys.argv and heute_schon_gelaufen():
        log.info("Heute schon gelaufen — nichts zu tun.")
        return
    start = time.time()
    log.info("=== TAGESLAUF DER INSTANZ STARTET ===")

    for name, agent in (("Beobachter", agent1_beobachter),
                        ("Analyst", agent2_analyst),
                        ("Kurator", agent3_kurator),
                        ("Bote", agent4_bote)):
        log.info("--- Agent: %s ---", name)
        try:
            agent.main()
        except Exception as e:
            log.error("Agent %s abgebrochen: %s", name, e)
            if name == "Beobachter":
                log.error("Ohne Rohdaten kein Weiterlauf. Ende.")
                sys.exit(1)

    stemple()
    log.info("=== TAGESLAUF FERTIG in %.0f s ===", time.time() - start)


if __name__ == "__main__":
    main()
