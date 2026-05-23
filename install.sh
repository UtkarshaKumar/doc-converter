#!/bin/zsh
# Word ↔ PDF Converter — one-time installer for macOS Finder Quick Actions
#
# What this script does:
#   1. Verifies Python 3 is available
#   2. Creates an isolated venv at ~/.doc-converter/venv/ and installs packages
#   3. Deploys the conversion script to ~/.doc-converter/
#   4. Generates two Automator Quick Action workflows in ~/Library/Services/
#   5. Refreshes the macOS services registry
#
# Safe to re-run: existing venv and workflows are updated in place.
# To remove everything: run uninstall.sh

set -euo pipefail

# ── Styling ───────────────────────────────────────────────────────────────
BOLD=$'\033[1m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
RED=$'\033[0;31m'
NC=$'\033[0m'

step()  { printf "${GREEN}▶${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}⚠${NC}  %s\n" "$1"; }
abort() { printf "${RED}✗${NC}  %s\n" "$1" >&2; exit 1; }

printf "\n${BOLD}  Word ↔ PDF Converter — Finder Quick Actions${NC}\n"
printf "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

# Resolve the directory containing this script regardless of where it is called from.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.doc-converter"
VENV_DIR="$INSTALL_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
SERVICES_DIR="$HOME/Library/Services"

# ── 1. Verify Python 3 ────────────────────────────────────────────────────
step "Checking Python 3…"
SYSTEM_PYTHON="$(command -v python3 2>/dev/null)" \
    || abort "Python 3 not found. Install via: brew install python3"
printf "   %s (%s)\n" "$SYSTEM_PYTHON" "$("$SYSTEM_PYTHON" --version 2>&1)"

# ── 2. Create isolated venv and install packages ──────────────────────────
step "Setting up isolated environment at $VENV_DIR…"
mkdir -p "$INSTALL_DIR"
if [[ ! -d "$VENV_DIR" ]]; then
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
    printf "   venv created.\n"
else
    printf "   venv already exists — updating packages.\n"
fi

step "Installing Python packages (docx2pdf, pdf2docx)…"
"$VENV_PYTHON" -m pip install --quiet --upgrade pip
"$VENV_PYTHON" -m pip install --quiet --upgrade docx2pdf pdf2docx
printf "   docx2pdf ✓   pdf2docx ✓\n"

# ── 3. Deploy conversion script ───────────────────────────────────────────
step "Deploying conversion script…"
cp "$SCRIPT_DIR/scripts/convert.py" "$INSTALL_DIR/convert.py"
chmod +x "$INSTALL_DIR/convert.py"
printf "   %s/convert.py\n" "$INSTALL_DIR"

# ── 4. Generate Automator Quick Action workflows ──────────────────────────
# Workflows are standard macOS Service packages (~/Library/Services/*.workflow).
# The plist is generated via Python so all XML escaping is handled correctly.
# The venv Python path is hardcoded in the command string so Automator's
# restricted PATH does not matter.
step "Creating Finder Quick Actions…"
mkdir -p "$SERVICES_DIR"

"$VENV_PYTHON" << 'PYEOF'
import os, plistlib, sys, uuid

home       = os.path.expanduser("~")
python_bin = sys.executable                                   # the venv python
script     = os.path.join(home, ".doc-converter", "convert.py")
svc_dir    = os.path.join(home, "Library", "Services")


def make_workflow(name: str, command: str) -> None:
    contents = os.path.join(svc_dir, f"{name}.workflow", "Contents")
    os.makedirs(contents, exist_ok=True)

    doc = {
        "AMApplicationBuild":    "492",
        "AMApplicationVersion":  "2.10",
        "AMDocumentSpecVersion": "1.1",
        "AMOSVersion":           "14.0",
        "AMWorkflowCategory":    "AMWorkflowCategoryUtilities",
        "actions": [{
            "action": {
                "AMAccepts": {
                    "Container": "List",
                    "Optional":  True,
                    "Types":     ["com.apple.cocoa.path"],
                },
                "AMActionVersion":    "2.0.3",
                "AMApplication":      ["Finder"],
                "AMParameterProperties": {
                    "COMMAND_STRING": {}, "CheckedForUserDefaultShell": {},
                    "inputMethod": {},    "shell": {},    "source": {},
                },
                "AMProvides": {
                    "Container": "List",
                    "Types":     ["com.apple.cocoa.path"],
                },
                "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
                "ActionName":       "Run Shell Script",
                "ActionParameters": {
                    "COMMAND_STRING":            command,
                    "CheckedForUserDefaultShell": True,
                    "inputMethod":               1,     # 1 = pass files as arguments
                    "shell":                     "/bin/zsh",
                    "source":                    "",
                },
                "BundleIdentifier":            "com.apple.RunShellScript",
                "CFBundleVersion":             "2.0.3",
                "CanShowSelectedItemsWhenRun": False,
                "CanShowWhenRun":              True,
                "Category":                   ["AMCategoryUtilities"],
                "Class Name":                 "RunShellScriptAction",
                "InputUUID":                  str(uuid.uuid4()).upper(),
                "Keywords":                   ["Shell", "Script", "Command", "Run", "Unix"],
                "OutputUUID":                 str(uuid.uuid4()).upper(),
                "UUID":                       str(uuid.uuid4()).upper(),
                "UnlocalizedApplications":    ["Automator"],
                "arguments": {
                    "0": {"default value": 0,         "name": "inputMethod",    "required": "0", "type": "0", "uuid": "0"},
                    "1": {"default value": "",        "name": "source",         "required": "0", "type": "0", "uuid": "1"},
                    "2": {"default value": "result",  "name": "COMMAND_STRING", "required": "0", "type": "0", "uuid": "2"},
                    "3": {"default value": "/bin/sh", "name": "shell",          "required": "0", "type": "0", "uuid": "3"},
                },
                "isViewVisible": True,
                "location":      "309.000000:253.000000",
                "nibPath":       "/System/Library/Automator/Run Shell Script.action/Contents/Resources/English.lproj/main.nib",
            },
            "isViewVisible": True,
        }],
        "connectors": {},
        "workflowMetaData": {
            "serviceApplicationBundleID":  "com.apple.finder",
            "serviceApplicationPath":      "/System/Library/CoreServices/Finder.app",
            "serviceInputTypeIdentifier":  "com.apple.Automator.fileSystemObject",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput":       0,
            "workflowTypeIdentifier":      "com.apple.Automator.servicesMenu",
        },
    }

    wflow_path = os.path.join(contents, "document.wflow")
    with open(wflow_path, "wb") as fh:
        plistlib.dump(doc, fh, fmt=plistlib.FMT_XML)
    print(f"   Created: {name}.workflow")


make_workflow("Convert to PDF",  f'{python_bin} "{script}" to_pdf "$@"')
make_workflow("Convert to Word", f'{python_bin} "{script}" to_docx "$@"')
PYEOF

# ── 5. Enable services in the macOS Quick Actions menu ────────────────────
# macOS requires third-party services to be explicitly enabled. Write the
# enabled state into pbs (pasteboard server) preferences so both actions
# appear in Quick Actions immediately without the user touching Customize.
# Note: do NOT killall cfprefsd — that flushes unsaved preferences and
# would wipe any settings the user changed since last sync.
# Note: `defaults -dict-add` cannot handle keys containing parentheses,
# so we use a Python export→merge→import cycle instead.
step "Enabling Quick Actions in Finder…"
"$VENV_PYTHON" << 'PYEOF'
import plistlib, subprocess, sys

tmp = "/tmp/pbs_export.plist"
subprocess.run(["defaults", "export", "pbs", tmp], check=True)

with open(tmp, "rb") as f:
    pbs = plistlib.load(f)

entry = {
    "presentation_modes": {
        "ContextMenu":   True,
        "FinderPreview": True,
        "ServicesMenu":  True,
        "TouchBar":      False,
    }
}
pbs.setdefault("NSServicesStatus", {})
pbs["NSServicesStatus"]["(com.apple.Automator) - Convert to PDF"]  = entry
pbs["NSServicesStatus"]["(com.apple.Automator) - Convert to Word"] = entry

with open(tmp, "wb") as f:
    plistlib.dump(pbs, f, fmt=plistlib.FMT_XML)

subprocess.run(["defaults", "import", "pbs", tmp], check=True)
print("   Convert to PDF  ✓  enabled")
print("   Convert to Word ✓  enabled")
PYEOF

# ── 6. Reload macOS services registry ─────────────────────────────────────
step "Refreshing macOS services registry…"
/System/Library/CoreServices/pbs -update 2>/dev/null || true

# Restart Finder to pick up the new services and preference changes.
step "Restarting Finder…"
killall Finder 2>/dev/null || true

printf "\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
printf "  ${BOLD}Installation complete!${NC}\n\n"
printf "  How to use:\n"
printf "   • Right-click any .docx / .doc  →  Quick Actions  →  ${BOLD}Convert to PDF${NC}\n"
printf "   • Right-click any .pdf          →  Quick Actions  →  ${BOLD}Convert to Word${NC}\n"
printf "   • Select multiple files and convert them all at once.\n\n"
warn "DOCX → PDF requires Microsoft Word (used for exact-fidelity export)."
warn "Word will briefly appear in the Dock during conversion — this is expected."
printf "\n  If Quick Actions still don't appear, open System Settings and enable them:\n"
printf "  ${BOLD}System Settings → Keyboard → Keyboard Shortcuts → Services${NC}\n\n"
