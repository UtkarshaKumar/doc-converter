#!/bin/zsh
# Word ↔ PDF Converter — uninstaller
set -euo pipefail

echo "Removing Word ↔ PDF Converter…"

rm -rf "$HOME/.doc-converter"
rm -rf "$HOME/Library/Services/Convert to PDF.workflow"
rm -rf "$HOME/Library/Services/Convert to Word.workflow"

/System/Library/CoreServices/pbs -update 2>/dev/null || true
killall cfprefsd 2>/dev/null || true

echo "Done. Restart Finder to clear the menu entries: killall Finder"
