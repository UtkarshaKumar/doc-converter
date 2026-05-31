# Word ↔ PDF Converter — Finder Quick Actions

A recurring time sink: switching between Word and PDF formats means opening an app, finding the export menu, choosing a format, picking a save location, and waiting. Do that a dozen times a day and it adds up fast.

This tool puts the conversion one right-click away — no app switch, no menus, no dialog boxes.

## What it does

- Right-click any `.docx` or `.doc` → **Services → Convert to PDF**
- Right-click any `.pdf` → **Services → Convert to Word**
- Select multiple files and convert them all at once
- Output lands in the same folder as the original, silently — no app windows open
- A native macOS notification confirms when it's done (or tells you exactly what went wrong)
<img width="643" height="626" alt="image" src="https://github.com/user-attachments/assets/3c92d67e-913b-46a9-b271-479ce890a00d" />

## Requirements

- macOS (Ventura or later recommended)
- Python 3 — install via [Homebrew](https://brew.sh): `brew install python3`
- **LibreOffice** — for high-quality DOCX → PDF (recommended):
  ```bash
  brew install --cask libreoffice
  ```
  If LibreOffice is absent, the installer falls back to `textutil` + Chrome headless (lower fidelity).
- No account, no subscription, no internet connection needed after install

## Install

```bash
git clone https://github.com/UtkarshaKumar/doc-converter
cd doc-converter
./install.sh
```

The installer:
1. Creates an isolated Python environment at `~/.doc-converter/`
2. Installs `pdf2docx` for PDF → DOCX conversion
3. Deploys the conversion script
4. Registers two Finder Quick Actions in `~/Library/Services/`
5. Auto-enables them in the macOS Services menu

Re-running `install.sh` is safe — it updates everything in place.

If the actions don't appear immediately, restart Finder:

```bash
killall Finder
```

## How to use

Right-click a file in Finder → **Services** → **Convert to PDF** or **Convert to Word**.

> macOS places user-created Automator services under the **Services** submenu (not Quick Actions, which is reserved for system and App Store extensions).

## How DOCX → PDF works

**Primary (recommended): LibreOffice headless**  
`soffice --headless --convert-to pdf` — fully silent, preserves fonts and layout exactly, no windows open. Install with `brew install --cask libreoffice`.

**Fallback: textutil + Chrome headless**  
macOS's built-in `textutil` converts DOCX to HTML; Chrome renders it to PDF. Always available but lower fidelity (some formatting may differ from the original).

Microsoft Word is not required for either path.

## How PDF → DOCX works

Conversion runs fully offline using [pdf2docx](https://github.com/dothinking/pdf2docx), which parses PDF structure with PyMuPDF and reconstructs it as a Word document. Quality is good for text-heavy PDFs. Complex multi-column layouts or PDFs generated from scans may not reconstruct perfectly.

## Uninstall

```bash
./uninstall.sh
killall Finder
```

This removes `~/.doc-converter/` and both Quick Action workflows from `~/Library/Services/`.
