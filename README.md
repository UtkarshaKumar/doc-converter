# Word ↔ PDF Converter — Finder Quick Actions

A recurring time sink: switching between Word and PDF formats means opening an app, finding the export menu, choosing a format, picking a save location, and waiting. Do that a dozen times a day and it adds up fast.

This tool puts the conversion one right-click away — no app switch, no menus, no dialog boxes.

![Right-click a .docx → Quick Actions → Convert to PDF](.github/demo.png)

## What it does

- Right-click any `.docx` or `.doc` → **Quick Actions → Convert to PDF**
- Right-click any `.pdf` → **Quick Actions → Convert to Word**
- Select multiple files and convert them all at once
- Output lands in the same folder as the original
- A native macOS notification confirms when it's done (or tells you exactly what went wrong)

## Requirements

- macOS (Ventura or later recommended)
- Python 3 — install via [Homebrew](https://brew.sh): `brew install python3`
- Google Chrome — used for the DOCX → PDF step (renders via Chrome headless)
- No account, no subscription, no internet connection needed after install

## Install

```bash
git clone https://github.com/UtkarshaKumar/doc-converter
cd doc-converter
./install.sh
```

The installer creates an isolated Python environment at `~/.doc-converter/`, installs the two conversion libraries there, and registers the Quick Actions with macOS. Re-running `install.sh` is safe — it updates packages in place.

If the Quick Actions don't appear immediately after install, restart Finder:

```bash
killall Finder
```

## How DOCX → PDF works

Conversion is a two-step pipeline, entirely offline:
1. **textutil** (macOS built-in) converts the DOCX to HTML
2. **Chrome headless** renders the HTML to PDF via `--print-to-pdf`

No app windows open. Microsoft Word is not required. Chrome must be installed (it almost certainly already is).

## How PDF → DOCX works

Conversion runs fully offline using [pdf2docx](https://github.com/dothinking/pdf2docx), which parses PDF structure with PyMuPDF and reconstructs it as a Word document. Quality is good for text-heavy PDFs. Complex multi-column layouts or PDFs generated from scans may not reconstruct perfectly.

## Uninstall

```bash
./uninstall.sh
killall Finder
```

This removes `~/.doc-converter/` and both Quick Action workflows from `~/Library/Services/`.
