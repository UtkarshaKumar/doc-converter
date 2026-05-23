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
- Microsoft Word — required for DOCX → PDF (uses Word's own export engine for exact fidelity)
- No account, no subscription, no internet connection needed

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

The conversion drives Microsoft Word via macOS automation (JXA). The result is identical to doing File → Export → PDF inside Word — no quality loss, fonts and layout preserved. Word will briefly appear in the Dock while it runs; that's expected.

## How PDF → DOCX works

Conversion runs fully offline using [pdf2docx](https://github.com/dothinking/pdf2docx), which parses PDF structure with PyMuPDF and reconstructs it as a Word document. Quality is good for text-heavy PDFs. Complex multi-column layouts or PDFs generated from scans may not reconstruct perfectly.

## Uninstall

```bash
./uninstall.sh
killall Finder
```

This removes `~/.doc-converter/` and both Quick Action workflows from `~/Library/Services/`.
