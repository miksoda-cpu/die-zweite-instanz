"""
AGENT 4 — DER BOTE
Stellt den täglichen Lagebericht zu, damit niemand Dateien öffnen muss:
  1. E-Mail (HTML, gut lesbar am Handy) — via SMTP
  2. Optional: Notion-Seite — damit Claude im Chat den Bericht
     direkt abrufen kann ("zeig mir den heutigen Lagebericht")

Konfiguration über Umgebungsvariablen (.env, siehe .env.example):
  INSTANZ_SMTP_HOST / _PORT / _USER / _PASS / _EMPFAENGER
  NOTION_TOKEN, NOTION_PARENT_PAGE_ID   (optional)
"""

import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from basis import DATA_DIR, heute, lade_json

log = logging.getLogger("bote")


def lade_env() -> None:
    """Liest eine .env-Datei im Projektordner (falls vorhanden)."""
    env = DATA_DIR.parent / ".env"
    if env.exists():
        for zeile in env.read_text().splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, _, v = zeile.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def hole_bericht() -> tuple[str, dict] | None:
    lb = DATA_DIR / "analysen" / heute() / "lagebericht.md"
    emp = DATA_DIR / "empfehlungen" / heute() / "empfehlungen.json"
    if not lb.exists():
        return None
    bericht = lb.read_text(encoding="utf-8")
    empfehlungen = lade_json(emp) if emp.exists() else {"empfehlungen": []}
    return bericht, empfehlungen


def als_html(bericht: str, empfehlungen: dict) -> str:
    """Sehr einfache, mailtaugliche Markdown-Umsetzung."""
    zeilen = []
    for z in bericht.splitlines():
        if z.startswith("## "):
            zeilen.append(f"<h2 style='color:#1a4d6d'>{z[3:]}</h2>")
        elif z.startswith("# "):
            zeilen.append(f"<h1 style='color:#0d2d40'>{z[2:]}</h1>")
        elif z.startswith(("- ", "* ")):
            zeilen.append(f"<li>{z[2:]}</li>")
        elif z.strip():
            zeilen.append(f"<p>{z}</p>")
    koerper = "\n".join(zeilen)

    emp_html = ""
    empf = sorted(empfehlungen.get("empfehlungen", []),
                  key=lambda e: e.get("prioritaet", 3))
    if empf:
        emp_html = "<h2 style='color:#1a4d6d'>Handlungsempfehlungen</h2>"
        for e in empf:
            prio = {1: "🔴 Prio 1", 2: "🟡 Prio 2"}.get(
                e.get("prioritaet"), "🟢 Prio 3")
            emp_html += (
                f"<div style='border-left:4px solid #1a4d6d;padding:8px 12px;"
                f"margin:10px 0;background:#f5f8fa'>"
                f"<b>{prio} — {e.get('these','')}</b>"
                f"<p style='margin:6px 0'>{e.get('begruendung','')}</p>"
                f"<small>Kanal: {e.get('kanal','—')} · "
                f"Risiko: {e.get('risiko','—')}</small></div>")

    return (f"<html><body style='font-family:Georgia,serif;max-width:640px;"
            f"margin:auto;line-height:1.5;color:#222'>{koerper}{emp_html}"
            f"<hr><small style='color:#888'>Die Instanz · automatischer "
            f"Tageslauf · {heute()}</small></body></html>")


def sende_mail(html: str) -> bool:
    host = os.environ.get("INSTANZ_SMTP_HOST")
    if not host:
        log.info("Kein SMTP konfiguriert — Mail übersprungen.")
        return False
    port = int(os.environ.get("INSTANZ_SMTP_PORT", "587"))
    user = os.environ["INSTANZ_SMTP_USER"]
    pw = os.environ["INSTANZ_SMTP_PASS"]
    an = os.environ.get("INSTANZ_EMPFAENGER", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏛 Lagebericht der Instanz — {heute()}"
    msg["From"] = user
    msg["To"] = an
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pw)
        s.send_message(msg)
    log.info("Lagebericht per Mail an %s zugestellt.", an)
    return True


def sende_notion(bericht: str, empfehlungen: dict) -> bool:
    token = os.environ.get("NOTION_TOKEN")
    parent = os.environ.get("NOTION_PARENT_PAGE_ID")
    if not (token and parent):
        log.info("Kein Notion konfiguriert — übersprungen.")
        return False

    def block(text: str, typ: str = "paragraph") -> dict:
        return {"object": "block", "type": typ,
                typ: {"rich_text": [{"type": "text",
                                     "text": {"content": text[:1990]}}]}}

    bloecke = []
    for z in bericht.splitlines():
        if z.startswith("## "):
            bloecke.append(block(z[3:], "heading_2"))
        elif z.startswith("# "):
            continue  # Titel steckt im Seitennamen
        elif z.strip():
            bloecke.append(block(z))
    for e in empfehlungen.get("empfehlungen", []):
        bloecke.append(block(
            f"[Prio {e.get('prioritaet','?')}] {e.get('these','')} — "
            f"{e.get('begruendung','')}", "bulleted_list_item"))

    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers={"Authorization": f"Bearer {token}",
                 "Notion-Version": "2022-06-28",
                 "Content-Type": "application/json"},
        json={"parent": {"page_id": parent},
              "properties": {"title": [{"type": "text", "text": {
                  "content": f"Lagebericht {heute()}"}}]},
              "children": bloecke[:100]},
        timeout=60)
    if r.ok:
        log.info("Lagebericht nach Notion übertragen.")
        return True
    log.error("Notion-Fehler %s: %s", r.status_code, r.text[:200])
    return False


def main() -> None:
    lade_env()
    ergebnis = hole_bericht()
    if ergebnis is None:
        log.warning("Kein Lagebericht für heute — nichts zuzustellen.")
        return
    bericht, empfehlungen = ergebnis
    html = als_html(bericht, empfehlungen)
    mail_ok = sende_mail(html)
    notion_ok = sende_notion(bericht, empfehlungen)
    if not (mail_ok or notion_ok):
        log.warning("Kein Zustellkanal aktiv — .env prüfen "
                    "(.env.example als Vorlage).")


if __name__ == "__main__":
    main()
