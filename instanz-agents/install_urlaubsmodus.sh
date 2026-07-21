#!/bin/bash
# ============================================================
# Urlaubsmodus der Instanz — einmalige Installation (macOS)
# Richtet einen LaunchAgent ein: Sobald der Mac eingeschaltet
# oder aufgeweckt wird (und dann stündlich zur Kontrolle),
# prüft er, ob der Tageslauf heute schon lief — wenn nicht,
# läuft die komplette Pipeline und der Bericht landet in Notion.
# ============================================================
set -e
PROJEKT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJEKT/venv/bin/python"
PLIST="$HOME/Library/LaunchAgents/at.instanz.tageslauf.plist"

if [ ! -f "$PYTHON" ]; then
  echo "⚠️  venv fehlt — bitte zuerst laut README installieren."; exit 1
fi

mkdir -p "$PROJEKT/data"
cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>at.instanz.tageslauf</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$PROJEKT/orchestrator.py</string>
    <string>--wenn-faellig</string>
  </array>
  <key>WorkingDirectory</key><string>$PROJEKT</string>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>3600</integer>
  <key>StandardOutPath</key><string>$PROJEKT/data/lauf.log</string>
  <key>StandardErrorPath</key><string>$PROJEKT/data/lauf.log</string>
</dict>
</plist>
PLISTEOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "✅ Urlaubsmodus aktiv."
echo "   Air einschalten → Pipeline läuft einmal → Bericht in Notion."
echo "   Log: $PROJEKT/data/lauf.log"
echo "   Deaktivieren: launchctl unload $PLIST"
