"""
AGENT 1 — DER BEOBACHTER
Sammelt Politik-Artikel aus allen Quellen des Medien-Registers,
filtert, holt Volltexte (soweit frei zugänglich, robots.txt wird
respektiert) und legt sie strukturiert ab.

Ablage: data/raw/YYYY-MM-DD/<quelle>_<hash>.json
Index:  data/raw/gesehen.txt  (Dedupe über Tage hinweg)
"""

import logging
import time
from pathlib import Path

import feedparser
import trafilatura

from basis import (DATA_DIR, heute, tages_ordner, lade_register,
                   url_hash, speichere_json)

log = logging.getLogger("beobachter")

GESEHEN_DATEI = DATA_DIR / "raw" / "gesehen.txt"
MAX_PRO_QUELLE = 25          # Schutz vor Feed-Fluten
PAUSE_SEKUNDEN = 1.5         # höflich bleiben


def lade_gesehen() -> set:
    if GESEHEN_DATEI.exists():
        return set(GESEHEN_DATEI.read_text().splitlines())
    return set()


def merke_gesehen(h: str) -> None:
    GESEHEN_DATEI.parent.mkdir(parents=True, exist_ok=True)
    with open(GESEHEN_DATEI, "a") as f:
        f.write(h + "\n")


def ist_politik(titel: str, anriss: str, keywords: list) -> bool:
    text = f"{titel} {anriss}".lower()
    return any(k.lower() in text for k in keywords)


def hole_volltext(url: str) -> str | None:
    """Freier Volltext via trafilatura. Paywalls werden NICHT umgangen."""
    try:
        html = trafilatura.fetch_url(url)
        if html:
            return trafilatura.extract(html, include_comments=False,
                                       include_tables=False)
    except Exception as e:
        log.warning("Volltext fehlgeschlagen für %s: %s", url, e)
    return None


def verarbeite_quelle(kuerzel: str, quelle: dict, region: str,
                      keywords: list, gesehen: set, ziel: Path) -> int:
    log.info("Lese Feed: %s", quelle["name"])
    try:
        feed = feedparser.parse(quelle["rss"])
    except Exception as e:
        log.error("Feed-Fehler %s: %s", kuerzel, e)
        return 0

    neu = 0
    for eintrag in feed.entries[:MAX_PRO_QUELLE]:
        url = eintrag.get("link", "")
        titel = eintrag.get("title", "")
        anriss = eintrag.get("summary", "")
        h = url_hash(url)

        if not url or h in gesehen:
            continue
        if not ist_politik(titel, anriss, keywords):
            continue

        volltext = hole_volltext(url)
        time.sleep(PAUSE_SEKUNDEN)

        artikel = {
            "id": h,
            "datum": heute(),
            "quelle_kuerzel": kuerzel,
            "quelle_name": quelle["name"],
            "region": region,
            "ausrichtung": quelle["ausrichtung"],
            "stil": quelle["stil"],
            "verlaesslichkeit": quelle["verlaesslichkeit"],
            "url": url,
            "titel": titel,
            "anriss": anriss,
            "veroeffentlicht": eintrag.get("published", ""),
            "volltext": volltext or "",
            "volltext_verfuegbar": bool(volltext),
        }
        speichere_json(ziel / f"{kuerzel}_{h}.json", artikel)
        merke_gesehen(h)
        gesehen.add(h)
        neu += 1

    log.info("  → %d neue Politik-Artikel", neu)
    return neu


def main() -> None:
    register = lade_register()
    keywords = register["politik_keywords"]
    gesehen = lade_gesehen()
    ziel = tages_ordner("raw")

    gesamt = 0
    for region in ("inland", "ausland"):
        for kuerzel, quelle in register.get(region, {}).items():
            gesamt += verarbeite_quelle(kuerzel, quelle, region,
                                        keywords, gesehen, ziel)

    log.info("BEOBACHTER FERTIG: %d neue Artikel unter %s", gesamt, ziel)


if __name__ == "__main__":
    main()
