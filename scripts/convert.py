#!/usr/bin/env python3
"""
Word ↔ PDF converter — macOS Finder Quick Action backend.

Entry points (called by Automator workflows in ~/Library/Services/):
  convert.py to_pdf   file1.docx [file2.docx …]
  convert.py to_docx  file1.pdf  [file2.pdf  …]

DOCX → PDF: drives Microsoft Word via JXA (identical to File > Export PDF).
            Word must be installed; it will briefly appear in the Dock.
PDF → DOCX: parses PDF structure with PyMuPDF; layout quality varies by PDF.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field

# ── Message catalog ───────────────────────────────────────────────────────
# All user-facing copy lives here. Keys are stable identifiers.
# To localize: duplicate this dict under a new locale key and swap at load time.
# Format fields are injected at notification time — never build strings inline.
MESSAGES: dict[str, tuple[str, str]] = {
    # (title_template, body_template)
    "converting_single":  ("Converting to {fmt}…",               "{name}"),
    "converting_batch":   ("Converting {n} files to {fmt}…",     "This may take a moment…"),
    "success_single":     ("Convert to {fmt} ✓",                 "Saved: {name}"),
    "success_batch":      ("Convert to {fmt} ✓",                 "{n} files converted"),
    "partial_success":    ("Convert to {fmt} — {done}/{total}",  "{first_error}"),
    "failure":            ("Convert to {fmt} — Error",           "{first_error}"),
    "word_not_installed": ("Microsoft Word required",            "Install Word, then try Convert to PDF again."),
    "package_missing":    ("Setup required — {fmt}",             "Run in Terminal: pip3 install {pkg}"),
    "nothing_to_convert": ("Nothing converted",                  "No supported files were selected for {fmt}."),
}


# ── Notification ──────────────────────────────────────────────────────────

def post_notification(key: str, *, sound: bool = True, **fields: str) -> None:
    title_tmpl, body_tmpl = MESSAGES[key]
    title = title_tmpl.format(**fields).replace('"', "'")
    body  = body_tmpl.format(**fields).replace('"', "'")
    sound_clause = ' sound name "Glass"' if sound else ""
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{body}" with title "{title}"{sound_clause}'],
        capture_output=True,
    )


# ── Conversion result ─────────────────────────────────────────────────────

@dataclass
class ConversionResult:
    input_path:  str
    output_path: str | None = field(default=None)
    error:       str | None = field(default=None)

    @property
    def succeeded(self) -> bool:
        return self.error is None


# ── Converters ────────────────────────────────────────────────────────────

def convert_docx_to_pdf(input_path: str) -> ConversionResult:
    # Platform quirk: docx2pdf shells out to osascript/JXA, which opens Word,
    # exports the file, then closes Word if it wasn't already running.
    # "Message not understood" from JXA means Word is not installed.
    try:
        from docx2pdf import convert  # noqa: PLC0415
    except ImportError:
        return ConversionResult(input_path, error="__pkg_missing__")

    output_path = os.path.splitext(input_path)[0] + ".pdf"
    try:
        convert(input_path, output_path)
        return ConversionResult(input_path, output_path=output_path)
    except Exception as exc:
        msg = str(exc)
        if "Message not understood" in msg or "not running" in msg.lower():
            return ConversionResult(input_path, error="__word_not_installed__")
        return ConversionResult(input_path, error=msg[:120])


def convert_pdf_to_docx(input_path: str) -> ConversionResult:
    try:
        import logging  # noqa: PLC0415
        from pdf2docx import Converter  # noqa: PLC0415
        logging.disable(logging.INFO)   # pdf2docx logs each parse step; suppress for Automator
    except ImportError:
        return ConversionResult(input_path, error="__pkg_missing__")

    output_path = os.path.splitext(input_path)[0] + ".docx"
    try:
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        return ConversionResult(input_path, output_path=output_path)
    except Exception as exc:
        return ConversionResult(input_path, error=str(exc)[:120])


# ── Dispatch ──────────────────────────────────────────────────────────────

_MODE_CONFIG = {
    "to_pdf": {
        "fmt":       "PDF",
        "exts":      (".docx", ".doc"),
        "converter": convert_docx_to_pdf,
        "pkg":       "docx2pdf",
    },
    "to_docx": {
        "fmt":       "Word",
        "exts":      (".pdf",),
        "converter": convert_pdf_to_docx,
        "pkg":       "pdf2docx",
    },
}


def dispatch_conversion(mode: str, files: list[str]) -> None:
    cfg     = _MODE_CONFIG[mode]
    fmt     = cfg["fmt"]
    convert = cfg["converter"]
    pkg     = cfg["pkg"]

    valid = [f for f in files if f.lower().endswith(cfg["exts"])]
    if not valid:
        post_notification("nothing_to_convert", sound=False, fmt=fmt)
        return

    n = len(valid)
    if n == 1:
        post_notification("converting_single", sound=False,
                          fmt=fmt, name=os.path.basename(valid[0]))
    else:
        post_notification("converting_batch", sound=False, fmt=fmt, n=str(n))

    results   = [convert(f) for f in valid]
    successes = [r for r in results if r.succeeded]
    failures  = [r for r in results if not r.succeeded]

    if failures:
        first_err = failures[0].error or "unknown error"
        if first_err == "__pkg_missing__":
            post_notification("package_missing", sound=False, fmt=fmt, pkg=pkg)
            return
        if first_err == "__word_not_installed__":
            post_notification("word_not_installed", sound=False)
            return

    if not failures:
        if n == 1:
            post_notification("success_single",
                              fmt=fmt, name=os.path.basename(successes[0].output_path or ""))
        else:
            post_notification("success_batch", fmt=fmt, n=str(n))
    elif successes:
        post_notification("partial_success", sound=False,
                          fmt=fmt,
                          done=str(len(successes)),
                          total=str(n),
                          first_error=failures[0].error or "unknown error")
    else:
        post_notification("failure", sound=False,
                          fmt=fmt,
                          first_error=failures[0].error or "unknown error")


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in _MODE_CONFIG:
        print("Usage: convert.py [to_pdf|to_docx] file1 [file2 …]", file=sys.stderr)
        sys.exit(1)
    dispatch_conversion(sys.argv[1], sys.argv[2:])


if __name__ == "__main__":
    main()
