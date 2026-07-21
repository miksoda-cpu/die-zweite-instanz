"""
basis.py — Gemeinsame Infrastruktur für die Instanz-Agenten.
Ollama-Client, Konfiguration, Dateiablage, Logging.
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import date

import requests
import yaml

# ---------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------
BASIS_DIR = Path(__file__).parent
DATA_DIR = BASIS_DIR / "data"            # anpassbar: externer Pfad möglich
OLLAMA_URL = "http://localhost:11434"
MODELL = "qwen2.5:32b"                    # dein Arbeitspferd; für Tests: "gemma2:9b"
KONTEXT_TOKENS = 16384                    # num_ctx für Ollama

LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def heute() -> str:
    return date.today().isoformat()


def tages_ordner(unterordner: str) -> Path:
    """Legt data/<unterordner>/<YYYY-MM-DD>/ an und gibt den Pfad zurück."""
    p = DATA_DIR / unterordner / heute()
    p.mkdir(parents=True, exist_ok=True)
    return p


def lade_register() -> dict:
    with open(BASIS_DIR / "medien_register.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def speichere_json(pfad: Path, daten) -> None:
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")


def lade_json(pfad: Path):
    return json.loads(pfad.read_text(encoding="utf-8"))


# ---------------------------------------------------------------
# Ollama-Client
# ---------------------------------------------------------------
def frage_instanz(system: str, prompt: str, json_modus: bool = False,
                  temperatur: float = 0.3, modell: str = MODELL) -> str:
    """Schickt eine Anfrage an die lokale Ollama-Instanz."""
    payload = {
        "model": modell,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperatur, "num_ctx": KONTEXT_TOKENS},
    }
    if json_modus:
        payload["format"] = "json"
    antwort = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=600)
    antwort.raise_for_status()
    return antwort.json()["response"].strip()


def frage_claude(system: str, prompt: str, temperatur: float = 0.3) -> str:
    """Optionaler Tiefendenker: Claude via Anthropic-API.
    Aktiv nur wenn ANTHROPIC_API_KEY gesetzt ist. Wird für die
    Synthese-Schritte genutzt (TIEFENDENKER=claude in der Umgebung).
    Rollenverständnis: Claude ist externer Gutachter/Zuarbeiter —
    die Instanz selbst spricht und entscheidet lokal."""
    import os
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt")
    antwort = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": 4096,
              "temperature": temperatur, "system": system,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=300)
    antwort.raise_for_status()
    return "".join(b.get("text", "") for b in antwort.json()["content"]).strip()


def denker(system: str, prompt: str, **kw) -> str:
    """Wählt den Denker: Claude wenn TIEFENDENKER=claude und Key da,
    sonst die lokale Ollama-Instanz. Fällt bei Fehlern auf lokal zurück."""
    import os
    if os.environ.get("TIEFENDENKER") == "claude":
        try:
            return frage_claude(system, prompt,
                                temperatur=kw.get("temperatur", 0.3))
        except Exception as e:
            logging.getLogger("basis").warning(
                "Claude nicht erreichbar (%s) — lokaler Fallback.", e)
    return frage_instanz(system, prompt, **kw)


def parse_json_antwort(text: str):
    """Robustes Parsen: entfernt Markdown-Zäune, versucht Reparatur."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Letzter Versuch: erstes { bis letztes }
        start, ende = text.find("{"), text.rfind("}")
        if start >= 0 and ende > start:
            return json.loads(text[start:ende + 1])
        raise
