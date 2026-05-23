#!/bin/zsh
# Word ↔ PDF Converter — uninstaller
#
# Removes the isolated Python environment and both Finder Quick Action workflows.
# After this script completes, restart Finder to clear the menu entries.
set -euo pipefail

BOLD=$'\033[1m'
GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
NC=$'\033[0m'

step()  { printf "${GREEN}▶${NC} %s\n" "$1"; }
abort() { printf "${RED}✗${NC}  %s\n" "$1" >&2; exit 1; }

printf "\n${BOLD}  Word ↔ PDF Converter — Uninstaller${NC}\n"
printf "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

step "Removing conversion environment…"
rm -rf "$HOME/.doc-converter"
printf "   ~/.doc-converter removed\n"

step "Removing Finder Quick Actions…"
rm -rf "$HOME/Library/Services/Convert to PDF.workflow"
rm -rf "$HOME/Library/Services/Convert to Word.workflow"
printf "   Convert to PDF.workflow removed\n"
printf "   Convert to Word.workflow removed\n"

step "Refreshing macOS services registry…"
/System/Library/CoreServices/pbs -update 2>/dev/null || true

step "Restarting Finder…"
killall Finder 2>/dev/null || true

printf "\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
printf "  ${BOLD}Uninstall complete.${NC}\n\n"
printf "  The Services menu entries will no longer appear in Finder.\n\n"
